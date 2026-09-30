"""Le R2 du critique de la phase 3, HORS PLAGE, sur MON echantillon -- le terme apparie.

Le seuil intermediaire de l'iteration 1 est un ECART APPARIE entre deux critiques mesures sur
le MEME echantillon hors plage. Ce script produit le terme « avant » et, surtout, il fixe
l'echantillon : sans lui, l'ecart comparerait deux critiques sur deux populations.

L'ECHANTILLON EST FIXE, ET C'EST UN CHOIX QUI SE PAIE
-----------------------------------------------------
Les nœuds sont ceux que la politique de `final.pt` visite, hors plage d'entrainement. Les deux
critiques sont ensuite evalues sur **ces memes observations**. C'est ce qui rend l'appariement
possible -- et c'est aussi une limite nommee : l'agent neuf visitera une AUTRE distribution
d'etats, et ce chiffre ne dit rien de sa qualite de prediction sur la sienne. Il dit « sur une
distribution de reference fixee, lequel des deux critiques predit le mieux ». Le seuil qui
tranche l'iteration reste le jeu.

Trois passes, sur trois blocs de seeds disjoints.
"""

from __future__ import annotations

import statistics
import sys
import time

import torch

from agents import entrainement
from agents.politique_reseau import charger
from courtisans.engine import Engine
from courtisans.infoset import tenseur
from mesure import phase3

FINAL = "models/phase3/final.pt"
APPAREIL = torch.device("cpu")

#: Hors plage d'entrainement, et distinct de tout ce que la phase 3 a utilise :
#: 100 000+ pour l'entrainement, 60 000+ pour le verdict, 70 000+ pour le pool,
#: 40 000+ pour le garde-fou, 5 000 000+ pour le hors-plage de l'auditeur.
DEPART_HORS_PLAGE = 7_000_000
#: Les trois passes prennent trois blocs DISJOINTS. Une vague de 2 000 parties consomme
#: 2 000 donnes, donc 100 000 d'ecart les separe largement.
ECART_ENTRE_PASSES = 100_000


def _modele(chemin: str):
    etat = Engine(phase3.CONFIG).reset(0)
    return charger(
        chemin,
        taille_observation=len(tenseur(etat, 0)),
        nb_actions=6 * 2 * (phase3.CONFIG.joueurs - 1),
    )


def valeurs_predites(modele, observations: list[list[float]]) -> list[float]:
    """`V(s)` du critique sur des observations deja collectees, par lots."""
    predites: list[float] = []
    with torch.no_grad():
        for debut in range(0, len(observations), 4096):
            lot = torch.tensor(
                observations[debut : debut + 4096], dtype=torch.float32, device=APPAREIL
            )
            _, valeurs = modele(lot)
            predites += valeurs.reshape(-1).tolist()
    return predites


def r2(retours: list[float], predites: list[float]) -> tuple[float, float, float]:
    """`(R2, MSE, variance des retours)` -- la methode de la phase 3, telle quelle."""
    mse = statistics.fmean((r - v) ** 2 for r, v in zip(retours, predites))
    variance = statistics.pvariance(retours)
    return 1.0 - mse / variance, mse, variance


def main(parties: int) -> None:
    modele = _modele(FINAL)
    for passe in range(3):
        depart = DEPART_HORS_PLAGE + passe * ECART_ENTRE_PASSES
        debut = time.perf_counter()
        # Pool vide : les trois sieges sont joues par la politique courante, donc c'est du
        # self-play a trois copies de `final.pt` -- la composition de l'auditeur.
        trajectoires, jouees = entrainement.jouer_une_vague(
            modele, [], parties, depart, APPAREIL
        )
        ecoule = time.perf_counter() - debut
        retours = list(trajectoires.gains)
        predites = valeurs_predites(modele, trajectoires.observations)
        coefficient, mse, variance = r2(retours, predites)

        # Controle : `valeurs` collectees pendant la vague et `V(s)` recalcule apres coup
        # doivent coincider. S'ils divergent, l'un des deux ne mesure pas ce qu'on croit.
        ecart_max = max(
            abs(a - b) for a, b in zip(trajectoires.valeurs, predites)
        )
        print(
            f"passe {passe + 1} : {jouees} parties, {len(retours)} nœuds, seeds {depart}+  "
            f"MSE {mse:.4f}  Var {variance:.4f}  R2 {coefficient:+.4f}  "
            f"[controle V : ecart max {ecart_max:.2e}]  -- {ecoule:.1f} s",
            flush=True,
        )


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 500)
