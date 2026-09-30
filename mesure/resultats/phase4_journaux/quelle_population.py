"""Quelle population donne « sept ecarts apparies, 3,56 a 4,06, moyenne 3,83 » ?

`agents/campagne.py` fonde la portee du garde-fou sur cette phrase. A portee 3 et 8 jalons, il
n'y a que CINQ ecarts -- les checkpoints 4 a 8. Sept ecarts, c'est la portee UN, les paires
consecutives. Ce script mesure les deux populations et dit laquelle porte le chiffre publie.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from agents import campagne as campagne_module
from mesure import bootstrap as boot
from mesure import phase3

JOURNAL = Path("models/phase3/journal.jsonl")


def demi_largeurs(jalons, portee: int) -> list[float]:
    resultat = []
    for jalon in jalons:
        numero = jalon["numero"]
        if numero - portee < 1:
            continue
        reference = jalons[numero - portee - 1]
        apparie = boot.bootstrap_apparie_par_donne(
            reference["parts_par_donne"],
            jalon["parts_par_donne"],
            phase3.RECHANTILLONS,
            random.Random(phase3.graine_du_garde_fou(numero)),
            risque=0.01 / campagne_module.CHECKPOINTS_ATTENDUS,
        )
        bas, haut = apparie.intervalle
        resultat.append((haut - bas) / 2.0)
    return resultat


def main() -> None:
    jalons = [json.loads(l) for l in JOURNAL.read_text().splitlines() if l.strip()]
    for portee in (1, 2, 3):
        demis = demi_largeurs(jalons, portee)
        moyenne = sum(demis) / len(demis)
        print(
            f"portee {portee} : {len(demis)} ecarts, demi-largeurs "
            f"{min(demis):.4%} a {max(demis):.4%}, moyenne {moyenne:.4%}"
        )
    print()
    print("publie dans agents/campagne.py : « sept ecarts apparies [...] de 3,56 a 4,06 "
          "points [...] donc 3,83 en moyenne »")


if __name__ == "__main__":
    main()
