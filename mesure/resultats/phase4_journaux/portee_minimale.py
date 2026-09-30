"""La portee minimale du garde-fou, RECALCULEE sur mon budget. Ne pas transcrire 3.

La regle du protocole : *un garde-fou ne peut chercher qu'un progres plus grand que l'ecart
detectable a son propre budget*, et la barre se lit sur la grandeur testee -- la demi-largeur
de l'IC de l'ECART APPARIE, jamais l'ecart detectable iid d'un NIVEAU.

Mon budget du garde-fou est **identique a celui de la phase 3** : 600 donnes, seeds 40000+,
8 checkpoints, correction de Bonferroni au risque 0,01/8. Il l'est parce que le prompt de
l'iteration 1 me l'interdit de le changer -- c'est une variable de plus, et il n'y en a qu'une.

Mais « identique » est une hypothese, pas une mesure. Ce script la verifie en recalculant les
sept demi-largeurs sur le journal du run de la phase 3, avec le code de bootstrap d'aujourd'hui.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from agents import campagne as campagne_module
from mesure import bootstrap as boot
from mesure import phase3

JOURNAL = Path("models/phase3/journal.jsonl")


def main() -> None:
    jalons = [json.loads(ligne) for ligne in JOURNAL.read_text().splitlines() if ligne.strip()]
    print(f"{len(jalons)} jalons lus dans {JOURNAL}")
    portee = campagne_module.PORTEE_DU_GARDE_FOU

    demi_largeurs: list[float] = []
    progres: list[float] = []
    for jalon in jalons:
        numero = jalon["numero"]
        if numero < campagne_module.PREMIER_CHECKPOINT_QUI_DECLENCHE:
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
        demi = (haut - bas) / 2.0
        demi_largeurs.append(demi)
        print(
            f"  checkpoint {numero} vs {numero - portee} : ecart {apparie.moyenne:+.4%} "
            f"IC [{bas:+.4%} ; {haut:+.4%}]  demi-largeur {demi:.4%}  "
            f"progres_etabli={apparie.progres_etabli}"
        )

    for avant, apres in zip(jalons, jalons[1:]):
        progres.append(apres["part_fractionnee"] - avant["part_fractionnee"])

    barre = sum(demi_largeurs) / len(demi_largeurs)
    par_checkpoint = sum(progres) / len(progres)
    print()
    print(f"demi-largeurs des {len(demi_largeurs)} ecarts apparies : "
          f"{min(demi_largeurs):.4%} a {max(demi_largeurs):.4%}, moyenne {barre:.4%}")
    print(f"progres par checkpoint : {min(progres):+.4%} a {max(progres):+.4%}, "
          f"moyenne {par_checkpoint:+.4%}")
    print(f"  (soit ({jalons[-1]['part_fractionnee']:.4%} - "
          f"{jalons[0]['part_fractionnee']:.4%}) / {len(progres)})")
    print()
    calculee = campagne_module.portee_minimale(barre, par_checkpoint)
    print(f"portee_minimale({barre:.4f} ; {par_checkpoint:.4f}) = {calculee}")
    print(f"PORTEE_DU_GARDE_FOU en vigueur = {portee}")
    print()
    print("A portee p, le garde-fou cherche un progres de p x le progres par checkpoint :")
    for p in (1, 2, 3, 4):
        cherche = p * par_checkpoint
        verdict = "SOUS la barre -- se declencherait sur un agent sain" if cherche < barre else "au-dessus de la barre"
        print(f"  p={p} : cherche {cherche:+.4%} contre une barre de {barre:.4%}  -- {verdict}")


if __name__ == "__main__":
    main()
