"""D'ou vient la perte de valeur ? Combien de nœuds a chaque rang de decision, et quelle MSE.

Le profil de l'auditeur montre que le critique fait 0,30 la ou l'irreductible vaut 0,0075.
Il ne dit pas POURQUOI. Une explication tient en un nombre : si les nœuds tardifs sont une
minorite, la MSE moyenne -- ce que l'optimiseur minimise -- est dominee par les nœuds precoces,
et rien ne pousse le critique a bien predire la ou c'est predictible.

Ce script mesure la part de chaque rang dans la population ET dans la perte totale.
"""

from __future__ import annotations

import statistics
import sys

import torch

from agents import entrainement
from agents.politique_reseau import charger
from courtisans.engine import Engine
from courtisans.infoset import tenseur
from mesure import phase3, phase4

APPAREIL = torch.device("cpu")


def main(parties: int) -> None:
    etat = Engine(phase3.CONFIG).reset(0)
    modele = charger(
        phase4.CHEMIN_AGENT_PHASE3,
        taille_observation=len(tenseur(etat, 0)),
        nb_actions=6 * 2 * (phase3.CONFIG.joueurs - 1),
    )
    trajectoires, jouees = entrainement.jouer_une_vague(
        modele, [], parties, phase4.DEPART_HORS_PLAGE, APPAREIL
    )
    predites = phase4.valeurs_predites(modele, trajectoires.observations)
    retours = list(trajectoires.gains)

    # Le rang de decision DU SIEGE : les nœuds d'un couple (donne, siege) sont ranges dans
    # l'ordre du lock-step, donc leur ordre d'apparition est l'ordre des decisions.
    rangs: list[int] = []
    compteur: dict[tuple[int, int], int] = {}
    for donne, siege in zip(trajectoires.donnes, trajectoires.sieges):
        cle = (donne, siege)
        rangs.append(compteur.get(cle, 0))
        compteur[cle] = rangs[-1] + 1

    par_rang: dict[int, list[tuple[float, float]]] = {}
    for rang, retour, predite in zip(rangs, retours, predites):
        par_rang.setdefault(rang, []).append((retour, predite))

    total_erreur = sum((r - v) ** 2 for r, v in zip(retours, predites))
    print(f"{jouees} parties, {len(retours)} nœuds, seeds {phase4.DEPART_HORS_PLAGE}+")
    print(f"MSE globale {total_erreur / len(retours):.4f}   "
          f"Var des retours {statistics.pvariance(retours):.4f}   "
          f"R2 {phase4.r2(retours, predites):+.4f}")
    print()
    print("rang   nœuds   part_pop   Var(R)    MSE     R2_local   part de la PERTE totale")
    for rang in sorted(par_rang):
        couples = par_rang[rang]
        rs = [r for r, _ in couples]
        erreur = sum((r - v) ** 2 for r, v in couples)
        variance = statistics.pvariance(rs) if len(rs) > 1 else 0.0
        mse = erreur / len(couples)
        r2_local = (1 - mse / variance) if variance > 0 else float("nan")
        print(
            f"{rang:4d}  {len(couples):6d}   {len(couples) / len(retours):7.2%}  "
            f"{variance:7.4f}  {mse:7.4f}  {r2_local:+8.4f}   {erreur / total_erreur:7.2%}"
        )


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 4000)
