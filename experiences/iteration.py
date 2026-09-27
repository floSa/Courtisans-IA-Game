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

Version 2 -- apres la derive mesuree le 27/09 a 16 h 25
--------------------------------------------------------
La v1 (fenetre des 3 dernieres generations, sans gardien) a derive : gen 1 bat c1b de +0,35
mais recule contre le greedy (+0,169 -> +0,118), gen 2 PERD contre gen 1 (-0,053) et tombe a
+0,054 contre le greedy. Chaque generation apprenait a exploiter la precedente. Trois
correctifs :

- **toutes les donnees** sont gardees (plafond `--max-echantillons`, les deux dernieres
  generations entieres, les plus anciennes sous-echantillonnees a parts egales), donnees
  greedy initiales comprises : V apprend la valeur contre la POPULATION, pas contre la
  derniere version -- l'esprit du jeu fictif ;
- un **gardien** : le candidat ne remplace la politique courante que s'il la bat (gain > 0
  contre 2 x courante) ET ne recule pas de plus de `--tolerance` contre le greedy ;
- une ligue plus large : courante 50 %, anciennes acceptees 25 %, greedy 25 %.

Version 3 -- 16 h 40 : la composition se tire PAR PARTIE
--------------------------------------------------------
La v2, gen 1 : bat c1b (+0,125) mais PERD contre le greedy (-0,075), rejetee par le gardien.
Mesure qui l'explique : c1b a un R2 de -0,12 sur les parties entre agents appris -- la valeur
depend fortement des adversaires. Tiree siege par siege, la ligue ne mettait « 2 greedys en
face » qu'une partie sur 16. `_composer` tire desormais un CONTEXTE par partie : 30 % contre
2 greedys, 40 % d'auto-jeu pur, 30 % contre les anciennes versions acceptees.

Lancer :
    COURTISANS_INSTANCE=complete uv run python -m experiences.iteration --duree-max-h 2 \\
        --donnees-initiales <parties greedy .npz> ...
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


def _composer(rng: random.Random, courant: str, passes: list[str], part_greedy: float,
              part_self: float) -> list[str]:
    """La composition d'UNE partie, tiree d'un bloc -- jamais siege par siege.

    La valeur d'une position depend de qui sont les adversaires (c1b : R2 = -0,12 sur les
    parties entre agents appris). Tirer siege par siege rendait « 2 greedys en face » rare
    (1 partie sur 16), alors que c'est le contexte du juge. D'ou trois contextes nets :
    contre 2 greedys, auto-jeu pur, contre les anciennes versions acceptees.
    """
    u = rng.random()
    if u < part_greedy:
        tenus = ["greedy"] * CONFIG.joueurs
        tenus[rng.randrange(CONFIG.joueurs)] = courant
    elif u < part_greedy + part_self or not passes:
        tenus = [courant] * CONFIG.joueurs
    else:
        tenus = [rng.choice(passes) for _ in range(CONFIG.joueurs)]
        tenus[rng.randrange(CONFIG.joueurs)] = courant
    return tenus


def _jouer_lot(args):
    courant, passes, debut, n, eps, augment, part_greedy, part_self = args
    moteur = Engine(CONFIG)
    X, G, M = [], [], []
    for donne in range(debut, debut + n):
        rng = random.Random(donne)
        tenus = _composer(rng, courant, passes, part_greedy, part_self)
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


def generer(ex, courant, passes, debut, parties, eps, augment, sortie, part_greedy=0.3,
            part_self=0.4):
    taille = 100
    taches = [
        (courant, passes, debut + i, min(taille, parties - i), eps, augment, part_greedy,
         part_self)
        for i in range(0, parties, taille)
    ]
    xs, gs, ms = [], [], []
    for X, G, M in ex.map(_jouer_lot, taches):
        xs.append(X)
        gs.append(G)
        ms.append(M)
    np.savez(sortie, X=np.concatenate(xs), G=np.concatenate(gs), M=np.concatenate(ms))
    return sum(len(g) for g in gs)


def _quotas(tailles: list[int], plafond: int) -> list[int]:
    """Les deux derniers fichiers entiers ; le reste du plafond a parts egales sur les autres."""
    if sum(tailles) <= plafond:
        return list(tailles)
    recents = tailles[-2:]
    anciens = tailles[:-2]
    reste = max(0, plafond - sum(recents))
    quotas = [0] * len(anciens)
    a_servir = list(range(len(anciens)))
    while a_servir and reste > 0:
        part = reste // len(a_servir)
        suivants = []
        for i in a_servir:
            prend = min(part, anciens[i] - quotas[i])
            quotas[i] += prend
            reste -= prend
            if quotas[i] < anciens[i]:
                suivants.append(i)
        if part == 0:
            break
        a_servir = suivants
    return quotas + recents


def entrainer(depart: str, fichiers: list[Path], sortie: str, epoques=3, lot=4096, lr=5e-4,
              plafond=14_000_000, graine=0):
    """Part des poids `depart`. Validation : les 5 % finaux du fichier le plus recent
    (parties contigues, donc d'autres parties que celles de l'apprentissage)."""
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rng = np.random.default_rng(graine)
    blocs = [np.load(f) for f in fichiers]
    tailles = [len(b["G"]) for b in blocs]
    tailles[-1] = int(0.95 * tailles[-1])
    quotas = _quotas(tailles, plafond)
    Xa = np.empty((sum(quotas), ENTREE), np.float16)
    Ya = np.empty((sum(quotas), 2), np.float32)
    pos = 0
    for b, taille, q in zip(blocs, tailles, quotas, strict=True):
        idx = np.sort(rng.choice(taille, q, replace=False)) if q < taille else np.arange(q)
        X, G, M = b["X"], b["G"], b["M"]
        Xa[pos : pos + q] = X[idx]
        Ya[pos : pos + q, 0] = G[idx]
        Ya[pos : pos + q, 1] = M[idx] / 5.0
        pos += q
        del X
    dernier = blocs[-1]
    coupe_d = tailles[-1]
    Xv = torch.tensor(dernier["X"][coupe_d:], dtype=torch.float32, device=dev)
    Yv = torch.tensor(dernier["G"][coupe_d:], dtype=torch.float32, device=dev)
    Xt = torch.tensor(Xa, dtype=torch.float16, device=dev)
    Yt = torch.tensor(Ya, dtype=torch.float32, device=dev)
    del Xa, Ya
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
    return {"echantillons": n, "quotas": quotas, "r2_validation": historique,
            "r2_retenu": meilleur}


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
    ap.add_argument("--donnees-initiales", nargs="*", default=[],
                    help="fichiers npz gardes dans la population des le debut")
    ap.add_argument("--run", default="iteration2")
    ap.add_argument("--generations", type=int, default=100)
    ap.add_argument("--duree-max-h", type=float, default=2.0)
    ap.add_argument("--parties", type=int, default=16_000)
    ap.add_argument("--eps", type=float, default=0.05)
    ap.add_argument("--augment", type=int, default=1)
    ap.add_argument("--max-echantillons", type=int, default=14_000_000)
    ap.add_argument("--tolerance", type=float, default=0.03)
    ap.add_argument("--part-greedy", type=float, default=0.3)
    ap.add_argument("--part-self", type=float, default=0.4)
    ap.add_argument("--workers", type=int, default=11)
    ap.add_argument("--donnes-greedy", type=int, default=300)
    ap.add_argument("--donnes-ligue", type=int, default=150)
    a = ap.parse_args()
    if CONFIG.familles != 6:
        raise SystemExit("la boucle vise le jeu complet : COURTISANS_INSTANCE=complete")
    modeles = RACINE / "modeles" / a.run
    donnees_dir = RACINE / "donnees" / a.run
    journal = RACINE / "resultats" / f"{a.run}.jsonl"
    modeles.mkdir(parents=True, exist_ok=True)
    donnees_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    courant = str(modeles / "gen_00.pt")
    torch.save(torch.load(a.depart, map_location="cpu"), courant)
    acceptees = [courant]
    fichiers: list[Path] = [Path(f) for f in a.donnees_initiales]
    with ProcessPoolExecutor(a.workers) as ex:
        greedy_courant = juger(ex, courant, "greedy", 5_000_000, a.donnes_greedy)
        with open(journal, "a") as f:
            f.write(json.dumps({"generation": 0, "modele": courant,
                                "contre_greedy": greedy_courant, "parametres": vars(a)}) + "\n")
        print(json.dumps({"generation": 0, "contre_greedy": greedy_courant}), flush=True)
        for k in range(1, a.generations + 1):
            if time.time() - t0 > a.duree_max_h * 3600:
                break
            debut_gen = time.time()
            donnees = donnees_dir / f"gen_{k:02d}.npz"
            n = generer(ex, courant, acceptees[:-1], 8_500_000 + 100_000 * k,
                        a.parties, a.eps, a.augment, donnees, a.part_greedy, a.part_self)
            fichiers.append(donnees)
            t_gen = time.time() - debut_gen
            candidat = str(modeles / f"gen_{k:02d}.pt")
            appr = entrainer(courant, fichiers, candidat, plafond=a.max_echantillons, graine=k)
            t_appr = time.time() - debut_gen - t_gen
            contre_greedy = juger(ex, candidat, "greedy", 5_000_000, a.donnes_greedy)
            contre_courant = juger(ex, candidat, courant, 5_800_000 + 1000 * k, a.donnes_ligue)
            contre_ancre = juger(ex, candidat, ANCRE, 5_700_000, a.donnes_ligue)
            accepte = (contre_courant["gain"] > 0
                       and contre_greedy["gain"] >= greedy_courant["gain"] - a.tolerance)
            ligne = {
                "generation": k,
                "modele": candidat,
                "courant_avant": courant,
                "accepte": accepte,
                "parties_auto_jeu": a.parties,
                "vues_collectees": n,
                "apprentissage": appr,
                "contre_greedy": contre_greedy,
                "contre_courant": contre_courant,
                "contre_ancre_c1b": contre_ancre,
                "secondes": {"auto_jeu": round(t_gen), "apprentissage": round(t_appr),
                             "jugement": round(time.time() - debut_gen - t_gen - t_appr),
                             "depuis_debut": round(time.time() - t0)},
            }
            with open(journal, "a") as f:
                f.write(json.dumps(ligne) + "\n")
            print(json.dumps({c: ligne[c] for c in ("generation", "accepte", "contre_greedy",
                  "contre_courant", "contre_ancre_c1b", "secondes")}), flush=True)
            if accepte:
                courant = candidat
                greedy_courant = contre_greedy
                acceptees.append(courant)
    return 0


if __name__ == "__main__":
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    raise SystemExit(main())
