"""Le plafond du R2 monte-t-il avec le VOLUME de donnees ? La question qui decide de l'iteration.

Le balayage precedent dit qu'a 307 000 nœuds, le meilleur regresseur supervise fait +0,106
la ou le critique de la phase 3 fait +0,101. Deux lectures s'affrontent, et elles ne
demandent pas le meme travail :

- **le plafond est a ~0,11 et il tient a l'INFO-SET** : le critique de la phase 3 y est deja,
  aucune reparation de la tete n'y changera rien, et c'est un arbitrage a remonter ;
- **le plafond monte encore avec les donnees** : 307 000 nœuds ne suffisent pas, un run de
  2 h en voit des millions, et la reparation garde un sens.

Ce script les separe : le meme test FIXE, le meme reseau, et quatre volumes d'apprentissage.
Une courbe qui plafonne repond a la premiere ; une courbe qui monte encore repond a la seconde.

**L'arret precoce est choisi SUR LE TEST**, donc les chiffres rendus sont OPTIMISTES -- c'est
volontaire : on cherche une borne haute de ce qu'un regresseur peut faire, et une borne haute
optimiste qui reste basse est un resultat plus fort qu'une mesure honnete qui reste basse.
"""

from __future__ import annotations

import time

import torch
from torch import nn, optim

from agents.politique_reseau import charger
from courtisans.engine import Engine
from courtisans.infoset import tenseur
from mesure import phase3, phase4

APPAREIL = torch.device("cpu")
VOLUMES = (4_000, 16_000, 40_000, 80_000)


def _r2(y, p) -> float:
    return float(1.0 - ((y - p) ** 2).mean() / y.var(unbiased=False))


def main() -> None:
    etat = Engine(phase3.CONFIG).reset(0)
    critique = charger(
        phase4.CHEMIN_AGENT_PHASE3,
        taille_observation=len(tenseur(etat, 0)),
        nb_actions=6 * 2 * (phase3.CONFIG.joueurs - 1),
    )

    test = phase4.echantillon_hors_plage(critique, depart=7_400_000, parties=4_000)
    x_test = torch.tensor([list(o) for o in test.observations], dtype=torch.float32)
    y_test = torch.tensor(test.retours, dtype=torch.float32)
    base = torch.tensor(phase4.valeurs_predites(critique, test.observations))
    etalon = _r2(y_test, base)
    print(f"test FIXE : {len(y_test)} nœuds, seeds 7400000+")
    print(f"ETALON -- critique de la phase 3 : R2 {etalon:+.4f}\n")

    print("parties   nœuds      meilleur R2 TEST   epoque   collecte   ajustement")
    for parties in VOLUMES:
        debut = time.perf_counter()
        ech = phase4.echantillon_hors_plage(critique, depart=7_000_000, parties=parties)
        x = torch.tensor([list(o) for o in ech.observations], dtype=torch.float32)
        y = torch.tensor(ech.retours, dtype=torch.float32)
        collecte = time.perf_counter() - debut

        debut = time.perf_counter()
        torch.manual_seed(0)
        reseau = nn.Sequential(
            nn.Linear(x.shape[1], 128), nn.ReLU(),
            nn.Linear(128, 128), nn.ReLU(),
            nn.Linear(128, 1),
        )
        optimiseur = optim.Adam(reseau.parameters(), lr=1e-3)
        meilleur, meilleure = -9.9, 0
        for epoque in range(12):
            ordre = torch.randperm(len(y))
            for depart in range(0, len(y), 1024):
                indices = ordre[depart : depart + 1024]
                perte = nn.functional.mse_loss(
                    reseau(x[indices]).squeeze(-1), y[indices]
                )
                optimiseur.zero_grad(set_to_none=True)
                perte.backward()
                optimiseur.step()
            with torch.no_grad():
                rt = _r2(y_test, reseau(x_test).squeeze(-1))
            if rt > meilleur:
                meilleur, meilleure = rt, epoque + 1
        print(
            f"{parties:7d}   {len(y):8d}   {meilleur:+15.4f}   {meilleure:6d}   "
            f"{collecte:7.1f} s   {time.perf_counter() - debut:8.1f} s",
            flush=True,
        )


if __name__ == "__main__":
    main()
