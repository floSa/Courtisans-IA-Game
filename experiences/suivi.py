"""Resume lisible d'une boucle d'auto-jeu : une ligne par generation.

    uv run python -m experiences.suivi experiences/resultats/iteration3.jsonl
"""
import json
import sys


def _f(d, k):
    if k not in d:
        return "        --        "
    g, (lo, hi) = d[k]["gain"], d[k]["ic99"]
    return f"{g:+.3f} [{lo:+.3f};{hi:+.3f}]"


def main(chemin):
    print(f"{'gen':>3} {'verdict':>8}  {'contre 2 greedys':^21} {'contre 2 courants':^21} "
          f"{'contre 2 c1b':^21} {'R2':>6} {'min':>5}")
    for ligne in open(chemin):
        d = json.loads(ligne)
        verdict = "depart" if d["generation"] == 0 else ("ACCEPTE" if d["accepte"] else "rejete")
        r2 = d.get("apprentissage", {}).get("r2_retenu")
        duree = d.get("secondes", {}).get("depuis_debut")
        print(f"{d['generation']:>3} {verdict:>8}  {_f(d, 'contre_greedy'):^21} "
              f"{_f(d, 'contre_courant'):^21} {_f(d, 'contre_ancre_c1b'):^21} "
              f"{'' if r2 is None else f'{r2:.3f}':>6} "
              f"{'' if duree is None else duree // 60:>5}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "experiences/resultats/iteration3.jsonl")
