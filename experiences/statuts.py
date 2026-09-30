"""Le « greedy probabiliste » : prevoir le STATUT FINAL des familles, en deduire le score espere.

Le greedy compte les points avec les statuts d'AUJOURD'HUI. Le score final se calcule pourtant
exactement a partir de deux choses : le statut final de chaque famille, et les cartes posees
dans les domaines. Ici un reseau predit, pour chaque famille, P(Obscurite / Indifferente /
Lumiere) a la fin de la partie ; le score espere de chaque siege s'en deduit par calcul :

    E[score_k] = somme_f  valeur des cartes visibles de f dans le domaine de k
                          x ( P(Lumiere_f) - P(Obscurite_f) )

Trois usages :
- `generer`     : des parties -> (vue, statuts finaux, domaines visibles, gain, ecart) ;
- `entrainer`   : le reseau a tetes (gain, ecart, statuts) -- ou sans la tete de statuts, le
                  temoin ;
- `evaluer`     : la predictibilite du statut par tour restant, contre « le statut actuel
                  restera » ;
- `agent_statuts` : l'agent, note chaque action par l'ecart espere de sa vue d'apres-coup.

Donnes de generation 9_000_000+ : disjointes de l'arene (5_000_000+) et de `donnees` (8_000_000+).
"""
from __future__ import annotations

import argparse
import random
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import torch
from torch import nn

from courtisans import rules
from courtisans.cards import ROLES_CACHES, VALEURS, GenreZone, Position
from courtisans.engine import Engine, Phase
from experiences.arene import fabrique
from experiences.config import CONFIG as C
from experiences.pimc import determiniser
from experiences.rapide import appliquer
from experiences.rapide import tenseur_rapide as tenseur

F = C.familles
J = C.joueurs
ENTREE = len(tenseur(Engine(C).reset(0), 0))
SORTIES = 2 + 3 * F  # gain, ecart / 5, puis 3 logits par famille (Obscurite, Indifferente, Lumiere)


def vue_domaines(etat, joueur):
    """(signe actuel des familles, valeurs visibles par domaine), tels que `joueur` les voit.

    Meme convention que `rapide.tenseur_rapide` : les dos adverses ne comptent pas ; les
    domaines sont indexes RELATIVEMENT a `joueur` (0 = le sien). Aucune regle reecrite : c'est
    le decompte de `tenseur_rapide`, isole.
    """
    infl = [0] * F
    dom = np.zeros((J, F), np.float32)
    for p in etat._posees:
        c, z = p.carte, p.zone
        if c.role in ROLES_CACHES and p.poseur != joueur:
            continue
        v = VALEURS[c.role]
        if z.genre is GenreZone.BANQUET:
            infl[c.famille] += v if z.position is Position.ESTIME else -v
        else:
            dom[(z.proprietaire - joueur) % J, c.famille] += v
    signe = np.array([1 if d >= 1 else (-1 if d <= -1 else 0) for d in infl], np.int8)
    return signe, dom


def _lot(args):
    """`contextes` : [(poids, [spec par siege])] -- un contexte tire par partie, sieges melanges."""
    contextes, debut, n, eps = args
    e = Engine(C)
    cle = ("X", "S", "SA", "D", "G", "M", "TR", "P")
    out = {k: [] for k in cle}
    for d in range(debut, debut + n):
        rng = random.Random(d)
        specs = list(rng.choices([c[1] for c in contextes], [c[0] for c in contextes])[0])
        rng.shuffle(specs)
        pols = [fabrique(specs[j])(random.Random(10 * d + j)) for j in range(J)]
        s = e.reset(d)
        vues = []
        while True:
            vues.append([(tenseur(s, j), *vue_domaines(s, j), s.tours_restants(j))
                         for j in range(J)])
            if s.is_terminal():
                break
            a = rng.choice(s.legal_actions()) if rng.random() < eps else pols[s.current_player()](s)
            s.apply(a)
        g = s.returns()
        sc = s.scores()
        final = rules.statuts(s._posees, F)
        sf = np.array([int(final[f]) + 1 for f in range(F)], np.int8)
        for v in vues:
            for j in range(J):
                x, signe, dom, tr = v[j]
                out["X"].append(x)
                out["S"].append(sf)
                out["SA"].append(signe + 1)
                out["D"].append(dom)
                out["G"].append(g[j])
                out["M"].append(sc[j] - max(y for k, y in sc.items() if k != j))
                out["TR"].append(tr)
                out["P"].append(d)
    return {
        "X": np.asarray(out["X"], np.float16), "S": np.asarray(out["S"], np.int8),
        "SA": np.asarray(out["SA"], np.int8), "D": np.asarray(out["D"], np.float16),
        "G": np.asarray(out["G"], np.float32), "M": np.asarray(out["M"], np.float32),
        "TR": np.asarray(out["TR"], np.int8), "P": np.asarray(out["P"], np.int32),
    }


def generer_contextes(contextes, parties, depart, eps, workers, sortie):
    taille = 100
    taches = [(contextes, depart + i, min(taille, parties - i), eps)
              for i in range(0, parties, taille)]
    morceaux = []
    with ProcessPoolExecutor(workers) as ex:
        for r in ex.map(_lot, taches):
            morceaux.append(r)
    data = {k: np.concatenate([m[k] for m in morceaux]) for k in morceaux[0]}
    print({k: v.shape for k, v in data.items()}, "gain moyen", data["G"].mean(), flush=True)
    np.savez(sortie, **data)


def generer(a):
    generer_contextes([(1, [a.spec] * J)], a.parties, a.depart, a.eps, a.workers, a.sortie)


class Reseau(nn.Module):
    def __init__(self, largeur=512):
        super().__init__()
        self.f = nn.Sequential(
            nn.Linear(ENTREE, largeur), nn.ReLU(),
            nn.Linear(largeur, largeur), nn.ReLU(),
            nn.Linear(largeur, 256), nn.ReLU(),
            nn.Linear(256, SORTIES),
        )

    def forward(self, x):
        return self.f(x)

    @staticmethod
    def separer(p):
        return p[:, :2], p[:, 2:].reshape(-1, F, 3)


def _charger_donnees(chemins, plafond=None):
    """Concatene les fichiers. Au-dela de `plafond` vues, le DERNIER fichier est garde entier et
    les autres sont sous-echantillonnes PAR PARTIE (une partie sur m), a parts egales."""
    parts = [dict(np.load(c)) for c in chemins]
    if plafond and sum(len(p["X"]) for p in parts) > plafond:
        reste = plafond - len(parts[-1]["X"])
        anciens = sum(len(p["X"]) for p in parts[:-1])
        m = max(1, int(np.ceil(anciens / max(reste, 1))))
        for i, p in enumerate(parts[:-1]):
            garde = (p["P"] % m) == 0
            parts[i] = {k: v[garde] for k, v in p.items()}
        print(f"plafond {plafond}: anciens sous-echantillonnes 1 partie sur {m}", flush=True)
    return {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}


def _coupe(d, part=0.92):
    """Premier indice de test : coupe sur une frontiere de PARTIE, jamais au milieu d'une."""
    i = int(part * len(d["P"]))
    while i < len(d["P"]) and d["P"][i] == d["P"][i - 1]:
        i += 1
    return i


def entrainer(chemins, sortie, epoques=6, lot=4096, lr=1e-3, statuts=True, poids_statuts=1.0,
              plafond=None):
    d = _charger_donnees(chemins, plafond)
    n, coupe = len(d["X"]), _coupe(d)
    dev = torch.device("cuda")
    Xt = torch.tensor(d["X"], dtype=torch.float16, device=dev)
    Y = torch.tensor(np.stack([d["G"], d["M"] / 5.0], 1), device=dev)
    S = torch.tensor(d["S"], dtype=torch.long, device=dev)
    net = Reseau().to(dev)
    opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, lr, total_steps=epoques * (coupe // lot))
    ce = nn.CrossEntropyLoss()
    for ep in range(epoques):
        perm = torch.randperm(coupe, device=dev)
        net.train()
        for i in range(0, coupe - lot + 1, lot):
            idx = perm[i:i + lot]
            v, s = Reseau.separer(net(Xt[idx].float()))
            perte = ((v - Y[idx]) ** 2).mean()
            if statuts:
                perte = perte + poids_statuts * ce(s.reshape(-1, 3), S[idx].reshape(-1))
            opt.zero_grad()
            perte.backward()
            opt.step()
            sched.step()
        net.eval()
        with torch.no_grad():
            pv, ps = [], []
            for i in range(coupe, n, 65536):
                a, b = Reseau.separer(net(Xt[i:i + 65536].float()))
                pv.append(a)
                ps.append(b)
            pv, ps = torch.cat(pv), torch.cat(ps)
            yt = Y[coupe:]
            r2_gain = 1 - float(((pv[:, 0] - yt[:, 0]) ** 2).sum() / ((yt[:, 0] - yt[:, 0].mean()) ** 2).sum())
            ll = float(ce(ps.reshape(-1, 3), S[coupe:].reshape(-1)))
            acc = float((ps.argmax(-1) == S[coupe:]).float().mean())
        print(f"epoque {ep} perte {float(perte):.4f} | test : R2 gain {r2_gain:.4f} "
              f"logloss statuts {ll:.4f} precision {acc:.4f}", flush=True)
    torch.save(net.cpu().state_dict(), sortie)
    return coupe, n


def _predire(chemin, X, lot=65536):
    net = Reseau()
    net.load_state_dict(torch.load(chemin, map_location="cpu"))
    net.eval().cuda()
    v, s = [], []
    with torch.no_grad():
        for i in range(0, len(X), lot):
            pv, ps = Reseau.separer(net(torch.tensor(X[i:i + lot], dtype=torch.float32).cuda()))
            v.append(pv.cpu())
            s.append(torch.softmax(ps, -1).cpu())
    return torch.cat(v).numpy(), torch.cat(s).numpy()


def ecart_espere(P, D):
    """Ecart espere du siege 0 (l'observateur) : E[score_0] - max_k E[score_k], k != 0.

    `P` : (n, F, 3) probabilites de statut ; `D` : (n, J, F) valeurs visibles par domaine.
    """
    signe = P[:, :, 2] - P[:, :, 0]
    e = (D.astype(np.float32) * signe[:, None, :]).sum(-1)
    return e[:, 0] - e[:, 1:].max(1)


def r2(y, p):
    return 1 - float(((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum())


def evaluer(chemin, donnees, temoin=None, coupe_depuis=None):
    """La table de la predictibilite. `coupe_depuis` : indice de test (defaut : les 8 % de fin)."""
    d = _charger_donnees([donnees])
    i0 = _coupe(d) if coupe_depuis is None else coupe_depuis
    t = {k: v[i0:] for k, v in d.items()}
    pv, P = _predire(chemin, t["X"])
    S, SA, TR = t["S"], t["SA"], t["TR"]
    cls = P.argmax(-1)
    logp = np.log(np.take_along_axis(P, S[..., None].astype(int), -1)[..., 0] + 1e-9)
    print(f"{len(S)} vues de test | statut final : "
          f"{np.bincount(S.ravel(), minlength=3) / S.size}")
    print(f"{'tours restants':>14} {'n':>8} {'acc reseau':>11} {'acc « actuel »':>15} "
          f"{'logloss':>8} {'logloss constante':>18}")
    for tr in sorted(set(TR.tolist())):
        m = TR == tr
        freq = np.bincount(S[m].ravel(), minlength=3) / S[m].size
        ll_cst = -float(np.mean(np.log(freq[S[m].astype(int)] + 1e-9)))
        print(f"{tr:>14} {m.sum():>8} {(cls[m] == S[m]).mean():>11.3f} "
              f"{(SA[m] == S[m]).mean():>15.3f} {-logp[m].mean():>8.3f} {ll_cst:>18.3f}")
    tout = f"TOUT {'':>9}{(cls == S).mean():>11.3f} {(SA == S).mean():>15.3f} {-logp.mean():>8.3f}"
    print(tout)
    M = t["M"]
    est = ecart_espere(P, t["D"])
    ligne = f"R2 de l'ecart final : via statuts {r2(M, est):.4f} | tete ecart {r2(M, pv[:, 1] * 5):.4f}"
    ligne += f" | statut actuel (= greedy) {r2(M, ecart_espere(np.eye(3)[SA], t['D'])):.4f}"
    print(ligne)
    print(f"R2 du gain (tete gain) {r2(t['G'], pv[:, 0]):.4f}")
    if temoin:
        pt, _ = _predire(temoin, t["X"])
        print(f"TEMOIN (sans tete de statuts) : R2 gain {r2(t['G'], pt[:, 0]):.4f} "
              f"| R2 ecart {r2(M, pt[:, 1] * 5):.4f}")
    # Par tranche de tours restants : R2 de l'ecart, statuts vs greedy
    print(f"{'tours restants':>14} {'R2 statuts':>11} {'R2 greedy':>10} {'R2 tete ecart':>14}")
    base = ecart_espere(np.eye(3)[SA], t["D"])
    for lo, hi in ((0, 0), (1, 1), (2, 3), (4, 6), (7, 10)):
        m = (TR >= lo) & (TR <= hi)
        if m.sum() > 100:
            print(f"{f'{lo}-{hi}':>14} {r2(M[m], est[m]):>11.3f} {r2(M[m], base[m]):>10.3f} "
                  f"{r2(M[m], pv[m, 1] * 5):>14.3f}")


_CACHE = {}


def _net(chemin):
    if chemin not in _CACHE:
        torch.set_num_threads(1)
        net = Reseau()
        net.load_state_dict(torch.load(chemin, map_location="cpu"))
        net.eval()
        _CACHE[chemin] = net
    return _CACHE[chemin]


def agent_statuts(rng, chemin, poids_valeur=0.0, poids_statuts=1.0, poids_ecart=0.05,
                  mondes_ciblage=8):
    """Note chaque action par l'ecart espere de la vue d'apres-coup, via les statuts finaux.

    `poids_valeur` : part de la tete de gain ajoutee au score (0 = les statuts seuls) ;
    `poids_statuts` : part de l'ecart espere via les statuts (0 = la valeur seule, comme
    `valeur.agent_valeur`, avec `poids_ecart` sur la tete d'ecart).
    Meme discipline que `valeur.agent_valeur` : au ciblage, noter en moyenne sur des mondes
    tires a l'aveugle, sinon la victime d'un dos serait vue avant le choix.
    """
    net = _net(chemin)

    def pol(etat):
        moi = etat.current_player()
        legales = etat.legal_actions()
        if len(legales) == 1:
            return legales[0]
        mondes = ([determiniser(etat, moi, rng) for _ in range(mondes_ciblage)]
                  if etat.phase() is Phase.CIBLAGE else [etat])
        vues, doms = [], []
        for monde in mondes:
            for a in legales:
                s = monde.clone()
                appliquer(s, a)
                vues.append(tenseur(s, moi))
                doms.append(vue_domaines(s, moi)[1])
        with torch.no_grad():
            pv, ps = Reseau.separer(net(torch.from_numpy(np.asarray(vues, np.float32))))
        P = torch.softmax(ps, -1).numpy()
        score = (poids_statuts * ecart_espere(P, np.asarray(doms))
                 + poids_valeur * (pv[:, 0].numpy() + poids_ecart * pv[:, 1].numpy()))
        score = score.reshape(len(mondes), len(legales)).mean(0)
        m = score.max()
        return rng.choice([a for a, x in zip(legales, score, strict=True) if x >= m - 1e-9])

    return pol


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    g = sp.add_parser("generer")
    g.add_argument("--spec", default="experiences.pimc:greedy_rollout")
    g.add_argument("--parties", type=int, default=12000)
    g.add_argument("--depart", type=int, default=9_000_000)
    g.add_argument("--eps", type=float, default=0.1)
    g.add_argument("--workers", type=int, default=11)
    g.add_argument("--sortie", required=True)
    t = sp.add_parser("entrainer")
    t.add_argument("sortie")
    t.add_argument("donnees", nargs="+")
    t.add_argument("--epoques", type=int, default=6)
    t.add_argument("--sans-statuts", action="store_true")
    e = sp.add_parser("evaluer")
    e.add_argument("modele")
    e.add_argument("donnees")
    e.add_argument("--temoin")
    e.add_argument("--tout", action="store_true", help="tout le fichier est du test")
    a = ap.parse_args()
    if a.cmd == "generer":
        generer(a)
    elif a.cmd == "entrainer":
        entrainer(a.donnees, a.sortie, a.epoques, statuts=not a.sans_statuts)
    else:
        evaluer(a.modele, a.donnees, a.temoin, coupe_depuis=0 if a.tout else None)


if __name__ == "__main__":
    main()
