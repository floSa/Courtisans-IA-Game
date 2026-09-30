"""Le PLANCHER par rang de decision : la variance qu'aucun critique ne peut predire.

La methode est celle de l'auditeur de la phase 3 : rejouer **le meme etat** plusieurs fois
sous la politique de l'agent, et prendre la variance des retours obtenus. Ce qui reste est
irreductible -- pas parce que le critique est mauvais, mais parce que la suite de la partie
n'est pas determinee par l'etat.

Le plancher est mesure sur l'ETAT COMPLET, donc sur plus qu'un info-set : un critique aveugle
fera moins bien. C'est une BORNE, et elle ne sert pas de cible.

Ce que ce script ajoute au profil de l'auditeur : le plancher **par rang de decision du
siege**, pour que la ponderation de la perte se pose sur une mesure et non sur une intuition.
"""

from __future__ import annotations

import random
import statistics
import sys
import time

import torch

from agents.politique_reseau import charger, politique_reseau
from courtisans.engine import Engine
from courtisans.infoset import tenseur
from mesure import phase3, phase4

APPAREIL = torch.device("cpu")
DEPART = 7_500_000


def main(nb_etats: int, replicats: int) -> None:
    moteur = Engine(phase3.CONFIG)
    etat_zero = moteur.reset(0)
    modele = charger(
        phase4.CHEMIN_AGENT_PHASE3,
        taille_observation=len(tenseur(etat_zero, 0)),
        nb_actions=6 * 2 * (phase3.CONFIG.joueurs - 1),
    )
    alea = random.Random(20260824)
    debut = time.perf_counter()

    # 1. Collecter des etats de decision, avec le rang du siege qui y decide.
    captures: list[tuple[object, int, int]] = []  # (etat clone, siege, rang)
    donne = DEPART
    while len(captures) < nb_etats:
        etat = moteur.reset(donne)
        donne += 1
        politique = politique_reseau(modele, random.Random(donne))
        rangs: dict[int, int] = {}
        while not etat.is_terminal():
            siege = etat.current_player()
            rang = rangs.get(siege, 0)
            rangs[siege] = rang + 1
            if alea.random() < 0.25 and len(captures) < nb_etats:
                captures.append((etat.clone(), siege, rang))
            etat.apply(politique(etat))

    # 2. Rejouer chaque etat `replicats` fois, avec un alea DIFFERENT a chaque fois.
    par_rang: dict[int, list[float]] = {}
    for numero, (etat_capture, siege, rang) in enumerate(captures):
        retours: list[float] = []
        for replicat in range(replicats):
            copie = etat_capture.clone()
            politique = politique_reseau(
                modele, random.Random(90_000_000 + numero * 1000 + replicat)
            )
            while not copie.is_terminal():
                copie.apply(politique(copie))
            retours.append(copie.returns()[siege])
        par_rang.setdefault(rang, []).append(statistics.pvariance(retours))

    ecoule = time.perf_counter() - debut
    print(
        f"{len(captures)} etats x {replicats} replicats = "
        f"{len(captures) * replicats} parties rejouees -- {ecoule:.1f} s"
    )
    print()
    print("rang   etats   plancher Var(R|s)   (moyenne des variances par etat)")
    planchers: dict[int, float] = {}
    for rang in sorted(par_rang):
        variances = par_rang[rang]
        plancher = statistics.fmean(variances)
        planchers[rang] = plancher
        print(f"{rang:4d}  {len(variances):6d}   {plancher:15.4f}")
    print()
    print("rang   plancher   poids = 1/plancher   poids normalise")
    total = sum(1.0 / max(p, 1e-3) for p in planchers.values())
    for rang, plancher in sorted(planchers.items()):
        poids = 1.0 / max(plancher, 1e-3)
        print(f"{rang:4d}  {plancher:9.4f}   {poids:17.3f}   {poids / total:14.4f}")


if __name__ == "__main__":
    main(
        int(sys.argv[1]) if len(sys.argv) > 1 else 300,
        int(sys.argv[2]) if len(sys.argv) > 2 else 24,
    )
