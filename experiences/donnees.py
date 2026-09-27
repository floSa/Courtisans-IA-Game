"""Donnees de valeur : (vue d'un siege a un noeud, gain final de ce siege, ecart de score).

Chaque noeud d'une partie -- terminal compris -- donne un exemple par siege, vu par CE
siege (`infoset.tenseur`, donc sans fuite). Politique : fabrique passee en argument.
Donnes 8_000_000+ : disjointes de l'arene (5_000_000+).
"""
import argparse
import random
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from courtisans.engine import Engine
from experiences.arene import fabrique
from experiences.config import CONFIG as C
from experiences.rapide import tenseur_rapide as tenseur


def _lot(args):
    spec, debut, n, eps = args
    e = Engine(C)
    X, G, M = [], [], []
    for d in range(debut, debut + n):
        rng = random.Random(d)
        pols = [fabrique(spec)(random.Random(10 * d + j)) for j in range(C.joueurs)]
        s = e.reset(d)
        vues = []
        while True:
            vues.append([tenseur(s, j) for j in range(C.joueurs)])
            if s.is_terminal():
                break
            a = rng.choice(s.legal_actions()) if rng.random() < eps else pols[s.current_player()](s)
            s.apply(a)
        g = s.returns()
        sc = s.scores()
        for v in vues:
            for j in range(C.joueurs):
                X.append(v[j])
                G.append(g[j])
                M.append(sc[j] - max(x for k, x in sc.items() if k != j))
    return (np.asarray(X, np.float16), np.asarray(G, np.float32), np.asarray(M, np.float32))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--spec", default="experiences.pimc:greedy_rollout")
    p.add_argument("--parties", type=int, default=40000)
    p.add_argument("--depart", type=int, default=8_000_000)
    p.add_argument("--eps", type=float, default=0.0)
    p.add_argument("--workers", type=int, default=11)
    p.add_argument("--sortie", required=True)
    a = p.parse_args()
    taille = 250
    taches = [(a.spec, a.depart + i, min(taille, a.parties - (i - 0)), a.eps)
              for i in range(0, a.parties, taille)]
    xs, gs, ms = [], [], []
    with ProcessPoolExecutor(a.workers) as ex:
        for X, G, M in ex.map(_lot, taches):
            xs.append(X)
            gs.append(G)
            ms.append(M)
    X = np.concatenate(xs)
    G = np.concatenate(gs)
    M = np.concatenate(ms)
    print(X.shape, float(np.abs(X).max()), G.mean(), M.std())
    np.savez(a.sortie, X=X, G=G, M=M)


if __name__ == "__main__":
    main()
