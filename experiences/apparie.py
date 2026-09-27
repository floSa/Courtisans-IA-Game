"""Ecart APPARIE entre deux mesures d'arene faites sur les memes donnes.

    uv run python -m experiences.apparie experiences/resultats/fin_de_partie.jsonl 3 5

compare les lignes 3 et 5 (numerotees a partir de 1) du fichier : moyenne de (A - B) par
donne, IC 99 % bootstrap par donne. L'appariement retire la variance des donnes, qui domine.
"""
import json
import sys

from experiences.arene import bootstrap


def main(chemin, i, j):
    lignes = [json.loads(x) for x in open(chemin)]
    a, b = lignes[int(i) - 1], lignes[int(j) - 1]
    if a.get("depart") != b.get("depart") or len(a["par_donne"]) != len(b["par_donne"]):
        raise SystemExit("les deux mesures ne portent pas sur les memes donnes")
    diff = [x - y for x, y in zip(a["par_donne"], b["par_donne"], strict=True)]
    lo, hi = bootstrap(diff)
    print(f"A = {a['agent'][-60:]}\nB = {b['agent'][-60:]}")
    moyenne = sum(diff) / len(diff)
    print(f"A - B = {moyenne:+.4f}  IC99 [{lo:+.4f} ; {hi:+.4f}]  sur {len(diff)} donnes")


if __name__ == "__main__":
    main(*sys.argv[1:4])
