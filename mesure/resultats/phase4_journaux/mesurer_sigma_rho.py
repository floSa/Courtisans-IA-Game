"""Sigma et rho de MA composition, sous l'hypothese nulle.

La composition qui decide l'iteration 1 est « 1 agent contre 2 copies de l'agent de la
phase 3, sieges permutes ». Son dimensionnement se lit sous l'HYPOTHESE NULLE : l'agent
mesure est lui aussi une copie de l'agent de la phase 3. C'est la meme construction que la
phase 3, qui a dimensionne sur « 1 greedy contre 2 greedys ».

Trois passes, parce qu'aucune duree ni aucun chiffre de ce projet ne se cite sur une seule.
"""

from __future__ import annotations

import random
import sys
import time
from pathlib import Path

import torch

from agents.politique_reseau import charger, politique_reseau
from courtisans.engine import Engine
from courtisans.infoset import tenseur
from mesure import phase3

FINAL = "models/phase3/final.pt"
#: Le decalage de seeds de l'iteration 1. Distinct de tous ceux de la phase 3 : 60000 pour le
#: verdict, 70000 pour le pool, 40000 pour le garde-fou, 5000000 pour le hors-plage de l'audit.
DEPART_DIMENSIONNEMENT = 6_000_000
DECALAGE_ADVERSAIRE = 6_500_000


def _modele():
    etat = Engine(phase3.CONFIG).reset(0)
    return charger(
        FINAL,
        taille_observation=len(tenseur(etat, 0)),
        nb_actions=6 * 2 * (phase3.CONFIG.joueurs - 1),
    )


def main(donnes: int) -> None:
    modele = _modele()
    resultats = []
    for passe in range(3):
        depart = DEPART_DIMENSIONNEMENT + passe * 100_000
        debut = time.perf_counter()
        campagne = phase3.jouer_composition(
            agent=lambda alea: politique_reseau(modele, alea),
            adversaire=lambda alea: politique_reseau(modele, alea),
            donnes=donnes,
            intitule=(
                f"1 copie de final.pt contre 2 copies de final.pt (hypothese nulle de "
                f"l'iteration 1), {donnes} donnes, seeds {depart}+"
            ),
            depart=depart,
            decalage_adversaire=DECALAGE_ADVERSAIRE + passe * 100_000,
        )
        dim = phase3.dimensionner(campagne)
        ecoule = time.perf_counter() - debut
        resultats.append((dim, ecoule))
        print(
            f"passe {passe + 1} : {dim.nb_parties} parties  "
            f"gain {dim.gain.moyenne:+.4f} IC [{dim.gain.intervalle[0]:+.4f} ; "
            f"{dim.gain.intervalle[1]:+.4f}]  sigma {dim.sigma_gain:.4f}  "
            f"rho {dim.rho:+.4f}  effet {dim.effet_de_plan:.4f}  -- {ecoule:.1f} s",
            flush=True,
        )

    sigmas = [d.sigma_gain for d, _ in resultats]
    rhos = [d.rho for d, _ in resultats]
    effets = [d.effet_de_plan for d, _ in resultats]
    gains = [d.gain.moyenne for d, _ in resultats]
    durees = [t for _, t in resultats]
    print()
    print(f"sigma  : {sigmas}   etendue {min(sigmas):.4f}-{max(sigmas):.4f}")
    print(f"rho    : {rhos}   etendue {min(rhos):+.4f}-{max(rhos):+.4f}")
    print(f"effet  : {effets}   etendue {min(effets):.4f}-{max(effets):.4f}")
    print(f"gain   : {gains}   (attendu ~0 : trois copies du meme agent)")
    print(f"duree  : {[round(t, 1) for t in durees]} s   etendue "
          f"{min(durees):.1f}-{max(durees):.1f} s pour {resultats[0][0].nb_parties} parties")
    print()
    for cible in (6_000, 12_000, 24_000):
        detectables = [d.ecart_detectable(cible) for d, _ in resultats]
        print(
            f"ecart detectable a {cible:6d} parties : "
            f"{min(detectables):+.4f} a {max(detectables):+.4f}"
        )


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 200)
