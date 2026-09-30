"""Arene : un agent contre deux adversaires, sieges permutes, en parallele.

Juge : gain moyen de l'agent (niveau nul exact 0 a 3 joueurs), IC bootstrap par donne.
Donnes : plage 5_000_000+ par defaut, disjointe des plages de mesure du depot.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import random
import statistics
import sys
import time
from concurrent.futures import ProcessPoolExecutor

from courtisans.engine import Engine
from experiences.config import CONFIG as ENTRAINEMENT_3J

CONFIG = ENTRAINEMENT_3J

#: La moitie des coeurs par defaut, en priorite minimale : les mesures tournent en arriere-plan
#: sans geler la machine de l'auteur. Surchargeable par --workers.
WORKERS_DEFAUT = max(1, (os.cpu_count() or 2) // 2)


def basse_priorite():
    """Initialiseur des processus de calcul : priorite minimale (nice 19)."""
    os.nice(19)


def fabrique(spec: str):
    """'module:fonction:arg1,arg2' -> fonction(rng) -> politique."""
    mod, fn, *args = spec.split(":")
    f = getattr(importlib.import_module(mod), fn)
    kw = {}
    if args and args[0]:
        for paire in args[0].split(","):
            k, v = paire.split("=")
            kw[k] = eval(v)  # noqa: S307 -- outil local
    return lambda rng: f(rng=rng, **kw)


def _une_donne(args):
    agent_spec, adv_spec, donne, config = args
    moteur = Engine(config)
    res = []
    for siege in range(config.joueurs):
        pols = []
        for place in range(config.joueurs):
            graine = 1_000_003 * donne + 17 * siege + place
            spec = agent_spec if place == siege else adv_spec
            pols.append(fabrique(spec)(random.Random(graine)))
        etat = moteur.reset(donne)
        while not etat.is_terminal():
            etat.apply(pols[etat.current_player()](etat))
        g = etat.returns()
        s = etat.scores()
        res.append((siege, g[siege], s[siege] - max(v for j, v in s.items() if j != siege)))
    return donne, res


def bootstrap(par_donne, n=5000, rng=None):
    rng = rng or random.Random(0)
    moy = []
    k = len(par_donne)
    for _ in range(n):
        moy.append(statistics.fmean(par_donne[rng.randrange(k)] for _ in range(k)))
    moy.sort()
    return moy[int(0.005 * n)], moy[int(0.995 * n) - 1]


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("agent")
    p.add_argument("--adv", default="experiences.pimc:greedy_rollout")
    p.add_argument("--donnes", type=int, default=100)
    p.add_argument("--depart", type=int, default=5_000_000)
    p.add_argument("--workers", type=int, default=WORKERS_DEFAUT)
    p.add_argument("--sortie", default=None)
    a = p.parse_args(argv)
    t0 = time.time()
    taches = [(a.agent, a.adv, d, CONFIG) for d in range(a.depart, a.depart + a.donnes)]
    resultats = []
    with ProcessPoolExecutor(a.workers, initializer=basse_priorite) as ex:
        for r in ex.map(_une_donne, taches, chunksize=1):
            resultats.append(r)
    par_donne = [statistics.fmean(g for _, g, _ in res) for _, res in resultats]
    gains = [g for _, res in resultats for _, g, _ in res]
    ecarts = [e for _, res in resultats for _, _, e in res]
    victoires = [1.0 if g > 0.9 else 0.0 for g in gains]
    par_siege = {
        s: statistics.fmean(g for _, res in resultats for ss, g, _ in res if ss == s)
        for s in range(CONFIG.joueurs)
    }
    lo, hi = bootstrap(par_donne)
    sortie = {
        "agent": a.agent,
        "adv": a.adv,
        "donnes": a.donnes,
        "parties": len(gains),
        "gain_moyen": statistics.fmean(gains),
        "ic99": [lo, hi],
        "victoire_seule": statistics.fmean(victoires),
        "ecart_score_moyen": statistics.fmean(ecarts),
        "par_siege": par_siege,
        "depart": a.depart,
        # Une valeur par donne, dans l'ordre : permet l'ecart APPARIE entre deux agents
        # mesures sur les memes donnes (experiences.apparie).
        "par_donne": par_donne,
        "secondes": time.time() - t0,
    }
    print(json.dumps({k: v for k, v in sortie.items() if k != "par_donne"}, indent=1))
    if a.sortie:
        with open(a.sortie, "a") as f:
            f.write(json.dumps(sortie) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
