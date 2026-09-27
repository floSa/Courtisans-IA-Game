"""Boucle d'amelioration par auto-jeu, generation apres generation, sur le JEU COMPLET.

Iteration de politique approchee, facon TD-Gammon :

1. **Jouer.** La politique courante -- l'agent d'apres-coup sur `V_k` -- joue contre une
   **ligue** : chaque siege est tenu, independamment, par `V_k` (60 %), une generation
   passee tiree au hasard (25 %) ou le greedy (15 %). Jouer contre une ligue et non contre
   soi seul est la parade a la non-transitivite mesuree le 27/09 (v2 bat v1 mais recule
   contre le greedy).
2. **Collecter.** Seuls les sieges tenus par `V_k` sont collectes : a chaque noeud de la
   partie, terminal compris, la vue de ce siege et, a la fin, son gain et son ecart de score.
   Chaque vue est doublee par une **permutation aleatoire des familles** (regle C18 : les
   familles sont interchangeables, le gain est invariant) -- dette n° 1 du depot, qui ne
   coute rien ici puisque l'agent n'agit jamais sur l'etat permute.
3. **Apprendre.** `V_{k+1}` part des poids de `V_k` et s'entraine sur les donnees des trois
   dernieres generations. Arret precoce sur les parties tenues a l'ecart de la derniere.
4. **Juger.** Sur des donnes FIXES d'une generation a l'autre : contre 2 greedys, contre
   2 x `c1b` (l'ancre, la meilleure valeur du 27/09) et contre 2 x `V_k`. Tout est ecrit dans
   `experiences/resultats/iteration.jsonl`, une ligne par generation.

Exploration : les sieges de `V_k` jouent un coup uniforme avec une probabilite `eps`.

Lancer :
    COURTISANS_INSTANCE=complete uv run python -m experiences.iteration --duree-max-h 2
"""

from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import torch

from courtisans.cards import Carte, CartePosee
from courtisans.engine import Engine, State
from experiences.arene import _une_donne, bootstrap
from experiences.config import CONFIG
from experiences.pimc import greedy_rollout
from experiences.rapide import appliquer, tenseur_rapide
from experiences.valeur import ENTREE, V, agent_valeur

RACINE = Path("experiences")
MODELES = RACINE / "modeles" / "iteration"
DONNEES = RACINE / "donnees" / "iteration"
JOURNAL = RACINE / "resultats" / "iteration.jsonl"
ANCRE = str(RACINE / "modeles" / "c1b.pt")


def permuter_familles(etat: State, perm: list[int]) -> State:
    """L'etat ou la famille `f` s'appelle `perm[f]`. Pour l'augmentation, jamais pour jouer."""

    def c(x: Carte) -> Carte:
        return Carte(perm[x.famille], x.role, x.exemplaire)

    def cp(p: CartePosee) -> CartePosee:
        return CartePosee(c(p.carte), p.zone, p.poseur)

    m = etat.clone()
    m._pioche = [c(x) for x in m._pioche]
    m._mains = [[c(x) for x in main] for main in m._mains]
    m._posees = [cp(p) for p in m._posees]
    m._defausse = [cp(p) for p in m._defausse]
    m._assassins_en_attente = [cp(p) for p in m._assassins_en_attente]
    return m


def _politique(qui: str, rng: random.Random):
    if qui == "greedy":
        return greedy_rollout(rng)
    return agent_valeur(rng, qui)


def _jouer_lot(args):
    courant, passes, debut, n, eps, augment = args
    moteur = Engine(CONFIG)
    X, G, M = [], [], []
    for donne in range(debut, debut + n):
        rng = random.Random(donne)
        tenus = []
        for _ in range(CONFIG.joueurs):
            u = rng.random()
            if u < 0.60 or (u < 0.85 and not passes):
                tenus.append(courant)
            elif u < 0.85:
                tenus.append(rng.choice(passes))
            else:
                tenus.append("greedy")
        if courant not in tenus:
            tenus[rng.randrange(CONFIG.joueurs)] = courant
        apprenants = [j for j, q in enumerate(tenus) if q == courant]
        pols = [_politique(q, random.Random(rng.random())) for q in tenus]
        etat = moteur.reset(donne)
        vues: list[tuple[int, list[float]]] = []
        while True:
            for j in apprenants:
                vues.append((j, tenseur_rapide(etat, j)))
                for _ in range(augment):
                    perm = list(range(CONFIG.familles))
                    rng.shuffle(perm)
                    vues.append((j, tenseur_rapide(permuter_familles(etat, perm), j)))
            if etat.is_terminal():
                break
            joueur = etat.current_player()
            if joueur in apprenants and rng.random() < eps:
                action = rng.choice(etat.legal_actions())
            else:
                action = pols[joueur](etat)
            appliquer(etat, action)
        gains = etat.returns()
        scores = etat.scores()
        for j, vue in vues:
            X.append(vue)
            G.append(gains[j])
            M.append(scores[j] - max(v for k, v in scores.items() if k != j))
    return (
        np.asarray(X, np.float16).reshape(-1, ENTREE),
        np.asarray(G, np.float32),
        np.asarray(M, np.float32),
    )


def generer(ex, courant, passes, debut, parties, eps, augment, sortie):
    taille = 100
    taches = [
        (courant, passes, debut + i, min(taille, parties - i), eps, augment)
        for i in range(0, parties, taille)
    ]
    xs, gs, ms = [], [], []
    for X, G, M in ex.map(_jouer_lot, taches):
        xs.append(X)
        gs.append(G)
        ms.append(M)
    np.savez(sortie, X=np.concatenate(xs), G=np.concatenate(gs), M=np.concatenate(ms))
    return sum(len(g) for g in gs)


def entrainer(depart: str, fichiers: list[Path], sortie: str, epoques=3, lot=4096, lr=5e-4):
    """Part des poids `depart`. Validation : les 5 % finaux du fichier le plus recent
    (parties contigues, donc d'autres parties que celles de l'apprentissage)."""
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    blocs = [np.load(f) for f in fichiers]
    dernier = blocs[-1]
    n_dernier = len(dernier["G"])
    coupe_d = int(0.95 * n_dernier)
    Xa = np.concatenate([b["X"] for b in blocs[:-1]] + [dernier["X"][:coupe_d]])
    Ya = np.concatenate(
        [np.stack([b["G"], b["M"] / 5.0], 1) for b in blocs[:-1]]
        + [np.stack([dernier["G"][:coupe_d], dernier["M"][:coupe_d] / 5.0], 1)]
    )
    Xv = torch.tensor(dernier["X"][coupe_d:], dtype=torch.float32, device=dev)
    Yv = torch.tensor(dernier["G"][coupe_d:], dtype=torch.float32, device=dev)
    Xt = torch.tensor(Xa, dtype=torch.float16, device=dev)
    Yt = torch.tensor(Ya, dtype=torch.float32, device=dev)
    net = V()
    net.load_state_dict(torch.load(depart, map_location="cpu"))
    net = net.to(dev)
    opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=1e-4)
    n = len(Xt)
    var_v = float(Yv.var())

    def r2():
        net.eval()
        with torch.no_grad():
            mse = float(((net(Xv)[:, 0] - Yv) ** 2).mean())
        net.train()
        return 1 - mse / var_v

    historique = [r2()]
    meilleur, meilleurs_poids = historique[0], {k: v.clone() for k, v in net.state_dict().items()}
    for _ in range(epoques):
        perm = torch.randperm(n, device=dev)
        for i in range(0, n - lot + 1, lot):
            idx = perm[i : i + lot]
            loss = ((net(Xt[idx].float()) - Yt[idx]) ** 2).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
        historique.append(r2())
        if historique[-1] > meilleur:
            meilleur = historique[-1]
            meilleurs_poids = {k: v.clone() for k, v in net.state_dict().items()}
    net.load_state_dict(meilleurs_poids)
    torch.save({k: v.cpu() for k, v in net.state_dict().items()}, sortie)
    return {"echantillons": n, "r2_validation": historique, "r2_retenu": meilleur}


def juger(ex, agent: str, adversaire: str, depart: int, donnes: int):
    spec_a = "experiences.pimc:greedy_rollout" if agent == "greedy" else (
        f"experiences.valeur:agent_valeur:chemin='{agent}'")
    spec_b = "experiences.pimc:greedy_rollout" if adversaire == "greedy" else (
        f"experiences.valeur:agent_valeur:chemin='{adversaire}'")
    taches = [(spec_a, spec_b, d, CONFIG) for d in range(depart, depart + donnes)]
    resultats = list(ex.map(_une_donne, taches, chunksize=2))
    par_donne = [statistics.fmean(g for _, g, _ in res) for _, res in resultats]
    lo, hi = bootstrap(par_donne)
    return {
        "gain": statistics.fmean(par_donne),
        "ic99": [lo, hi],
        "parties": 3 * donnes,
        "donnes": [depart, depart + donnes - 1],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--depart", default=ANCRE, help="poids de la generation 0")
    ap.add_argument("--generations", type=int, default=100)
    ap.add_argument("--duree-max-h", type=float, default=2.0)
    ap.add_argument("--parties", type=int, default=10_000)
    ap.add_argument("--eps", type=float, default=0.05)
    ap.add_argument("--augment", type=int, default=1)
    ap.add_argument("--fenetre", type=int, default=3)
    ap.add_argument("--workers", type=int, default=11)
    ap.add_argument("--donnes-greedy", type=int, default=300)
    ap.add_argument("--donnes-ligue", type=int, default=150)
    a = ap.parse_args()
    if CONFIG.familles != 6:
        raise SystemExit("la boucle vise le jeu complet : COURTISANS_INSTANCE=complete")
    MODELES.mkdir(parents=True, exist_ok=True)
    DONNEES.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    courant = str(MODELES / "gen_00.pt")
    torch.save(torch.load(a.depart, map_location="cpu"), courant)
    generations = [courant]
    fichiers: list[Path] = []
    with ProcessPoolExecutor(a.workers) as ex:
        for k in range(1, a.generations + 1):
            if time.time() - t0 > a.duree_max_h * 3600:
                break
            debut_gen = time.time()
            donnees = DONNEES / f"gen_{k:02d}.npz"
            n = generer(ex, courant, generations[:-1], 8_500_000 + 100_000 * k,
                        a.parties, a.eps, a.augment, donnees)
            fichiers.append(donnees)
            t_gen = time.time() - debut_gen
            nouveau = str(MODELES / f"gen_{k:02d}.pt")
            appr = entrainer(courant, fichiers[-a.fenetre:], nouveau)
            t_appr = time.time() - debut_gen - t_gen
            ligne = {
                "generation": k,
                "modele": nouveau,
                "parties_auto_jeu": a.parties,
                "vues_collectees": n,
                "apprentissage": appr,
                "contre_greedy": juger(ex, nouveau, "greedy", 5_000_000, a.donnes_greedy),
                "contre_ancre_c1b": juger(ex, nouveau, ANCRE, 5_700_000, a.donnes_ligue),
                "contre_precedente": juger(ex, nouveau, courant, 5_800_000 + 1000 * k,
                                           a.donnes_ligue),
                "secondes": {"auto_jeu": round(t_gen), "apprentissage": round(t_appr),
                             "jugement": round(time.time() - debut_gen - t_gen - t_appr),
                             "depuis_debut": round(time.time() - t0)},
                "parametres": vars(a),
            }
            with open(JOURNAL, "a") as f:
                f.write(json.dumps(ligne) + "\n")
            print(json.dumps({c: ligne[c] for c in ("generation", "contre_greedy",
                  "contre_ancre_c1b", "contre_precedente", "secondes")}), flush=True)
            courant = nouveau
            generations.append(courant)
    return 0


if __name__ == "__main__":
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    raise SystemExit(main())
