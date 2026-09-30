"""Le meme diagnostic, balaye : taille du reseau, volume de donnees, arret precoce.

Le premier essai dit qu'un regresseur plus gros sur-apprend au lieu de generaliser. Trois
confusions possibles, et il faut les ecarter une par une avant d'en conclure quoi que ce soit :

1. **trop peu de donnees** -- 77 000 nœuds, c'est peu ;
2. **trop de capacite** -- un reseau plus petit generaliserait peut-etre mieux ;
3. **trop d'epoques** -- le meilleur R2 de test est peut-etre atteint tot, puis perdu.

Le jeu de test vient toujours de seeds DISJOINTS, et il ne change pas d'un essai a l'autre :
comparer des R2 mesures sur deux tests differents ne dirait rien.
"""

from __future__ import annotations

import sys
import time

import torch
from torch import nn, optim

from agents.politique_reseau import charger
from courtisans.engine import Engine
from courtisans.infoset import tenseur
from mesure import phase3, phase4

APPAREIL = torch.device("cpu")


def _donnees(modele, depart: int, parties: int):
    ech = phase4.echantillon_hors_plage(modele, depart=depart, parties=parties)
    return (
        torch.tensor([list(o) for o in ech.observations], dtype=torch.float32),
        torch.tensor(ech.retours, dtype=torch.float32),
        ech,
    )


def _r2(y, p) -> float:
    return float(1.0 - ((y - p) ** 2).mean() / y.var(unbiased=False))


def main() -> None:
    etat = Engine(phase3.CONFIG).reset(0)
    critique = charger(
        phase4.CHEMIN_AGENT_PHASE3,
        taille_observation=len(tenseur(etat, 0)),
        nb_actions=6 * 2 * (phase3.CONFIG.joueurs - 1),
    )
    debut = time.perf_counter()
    x_grand, y_grand, ech_grand = _donnees(critique, 7_000_000, 16_000)
    x_test, y_test, ech_test = _donnees(critique, 7_400_000, 4_000)
    base = torch.tensor(phase4.valeurs_predites(critique, ech_test.observations))
    print(f"apprentissage disponible : {len(y_grand)} nœuds (16 000 parties, seeds 7000000+)")
    print(f"test FIXE                : {len(y_test)} nœuds (4 000 parties, seeds 7400000+)")
    print(f"collecte : {time.perf_counter() - debut:.1f} s")
    print(f"\nETALON -- critique de la phase 3 sur ce test : R2 {_r2(y_test, base):+.4f}\n")

    print("largeur  nœuds     meilleur R2 TEST   a l'epoque   R2 final   (apprentissage final)")
    for largeur in (32, 64, 256):
        for fraction in (0.25, 1.0):
            nb = int(len(y_grand) * fraction)
            x, y = x_grand[:nb], y_grand[:nb]
            torch.manual_seed(0)
            reseau = nn.Sequential(
                nn.Linear(x.shape[1], largeur), nn.ReLU(),
                nn.Linear(largeur, largeur), nn.ReLU(),
                nn.Linear(largeur, 1),
            )
            optimiseur = optim.Adam(reseau.parameters(), lr=1e-3)
            meilleur, meilleure_epoque, final, appris = -9.9, 0, 0.0, 0.0
            for epoque in range(20):
                ordre = torch.randperm(nb)
                for depart in range(0, nb, 1024):
                    indices = ordre[depart : depart + 1024]
                    perte = nn.functional.mse_loss(
                        reseau(x[indices]).squeeze(-1), y[indices]
                    )
                    optimiseur.zero_grad(set_to_none=True)
                    perte.backward()
                    optimiseur.step()
                with torch.no_grad():
                    rt = _r2(y_test, reseau(x_test).squeeze(-1))
                    ra = _r2(y, reseau(x).squeeze(-1))
                if rt > meilleur:
                    meilleur, meilleure_epoque = rt, epoque + 1
                final, appris = rt, ra
            print(
                f"{largeur:7d}  {nb:7d}   {meilleur:+15.4f}   {meilleure_epoque:10d}   "
                f"{final:+8.4f}   {appris:+18.4f}"
            )


if __name__ == "__main__":
    main()
