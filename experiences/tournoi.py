"""Tournoi : chaque agent contre deux copies de chaque autre, sur les memes donnes.

Rend une matrice « ligne contre 2 x colonne » de gains moyens (niveau nul 0) et un
classement par la moyenne de ligne. A trois joueurs aucun adversaire unique n'ordonne les
agents (non-transitivite mesuree le 27/09) : ce tableau est le juge qui la montre.

    COURTISANS_INSTANCE=complete uv run python -m experiences.tournoi greedy \\
        experiences/modeles/c1b.pt experiences/modeles/iteration/gen_05.pt --donnes 100
"""

from __future__ import annotations

import argparse
import json
import statistics
from concurrent.futures import ProcessPoolExecutor

from experiences.arene import WORKERS_DEFAUT, _une_donne, basse_priorite, bootstrap
from experiences.config import CONFIG


def spec(agent: str) -> str:
    if agent == "greedy":
        return "experiences.pimc:greedy_rollout"
    return f"experiences.valeur:agent_valeur:chemin='{agent}'"


def nom(agent: str) -> str:
    return agent.rsplit("/", 1)[-1].removesuffix(".pt")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("agents", nargs="+")
    ap.add_argument("--donnes", type=int, default=100)
    ap.add_argument("--depart", type=int, default=5_900_000)
    ap.add_argument("--workers", type=int, default=WORKERS_DEFAUT)
    ap.add_argument("--sortie", default="experiences/resultats/tournoi.jsonl")
    a = ap.parse_args()
    paires = [(x, y) for x in a.agents for y in a.agents if x != y]
    matrice: dict[tuple[str, str], dict] = {}
    with ProcessPoolExecutor(a.workers, initializer=basse_priorite) as ex:
        for x, y in paires:
            taches = [(spec(x), spec(y), d, CONFIG) for d in range(a.depart, a.depart + a.donnes)]
            res = list(ex.map(_une_donne, taches, chunksize=2))
            par_donne = [statistics.fmean(g for _, g, _ in r) for _, r in res]
            lo, hi = bootstrap(par_donne)
            matrice[(x, y)] = {"gain": statistics.fmean(par_donne), "ic99": [lo, hi]}
            print(f"{nom(x):>10} contre 2 x {nom(y):<10} {matrice[(x, y)]['gain']:+.3f} "
                  f"[{lo:+.3f} ; {hi:+.3f}]", flush=True)
    classement = sorted(
        a.agents,
        key=lambda x: -statistics.fmean(matrice[(x, y)]["gain"] for y in a.agents if y != x),
    )
    print("\nclassement (moyenne de ligne) :")
    for x in classement:
        m = statistics.fmean(matrice[(x, y)]["gain"] for y in a.agents if y != x)
        print(f"  {nom(x):>10} {m:+.3f}")
    with open(a.sortie, "a") as f:
        f.write(json.dumps({
            "instance": f"{CONFIG.familles} familles, {CONFIG.joueurs} joueurs",
            "donnes": [a.depart, a.depart + a.donnes - 1],
            "matrice": {f"{nom(x)} | 2 x {nom(y)}": v for (x, y), v in matrice.items()},
            "classement": [nom(x) for x in classement],
        }) + "\n")


if __name__ == "__main__":
    main()
