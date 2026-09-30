"""Le signal est-il dans l'info-set, ou le critique est-il seulement mal entraine ?

**Le diagnostic decisif, et il ne coute pas un entrainement.** On prend les nœuds hors plage
deja collectes -- `(info-set, retour)` --, on y ajuste une regression supervisee ordinaire,
et on lit son R2 sur un jeu de test DISJOINT.

Ce que chaque issue etablirait :

- **R2 de test proche de +0,10** : l'info-set ne porte pas plus d'information que ce que le
  critique en tire. Le probleme serait l'OBSERVATION, et aucune reparation de la tete n'y
  changerait rien -- il faudrait remonter au paragraphe 4.2, ce qui n'est pas cette iteration.
- **R2 de test franchement au-dessus** : l'information EST dans l'info-set, un regresseur
  ordinaire la trouve, et le critique de PPO ne la trouve pas. Le probleme serait alors
  l'OPTIMISATION ou la CAPACITE -- les points 4 et 5 --, pas la cible.

Le jeu de test vient de **seeds disjoints**, pas d'une coupe au hasard dans le meme bloc :
deux nœuds d'une meme partie portent le meme retour, et une coupe au hasard les separerait de
part et d'autre, ce qui ferait fuir la reponse dans le jeu de test.
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


def _echantillon(modele, depart: int, parties: int):
    ech = phase4.echantillon_hors_plage(modele, depart=depart, parties=parties)
    x = torch.tensor([list(o) for o in ech.observations], dtype=torch.float32)
    y = torch.tensor(ech.retours, dtype=torch.float32)
    return ech, x, y


def _r2(y: torch.Tensor, predites: torch.Tensor) -> float:
    return float(1.0 - ((y - predites) ** 2).mean() / y.var(unbiased=False))


def main(parties: int, largeur: int, epoques: int) -> None:
    etat = Engine(phase3.CONFIG).reset(0)
    critique = charger(
        phase4.CHEMIN_AGENT_PHASE3,
        taille_observation=len(tenseur(etat, 0)),
        nb_actions=6 * 2 * (phase3.CONFIG.joueurs - 1),
    )
    ech_a, x_a, y_a = _echantillon(critique, 7_000_000, parties)
    ech_t, x_t, y_t = _echantillon(critique, 7_300_000, parties // 2)
    print(f"apprentissage : {len(y_a)} nœuds, seeds 7000000+")
    print(f"test          : {len(y_t)} nœuds, seeds 7300000+  (blocs DISJOINTS)")

    with torch.no_grad():
        base_a = torch.tensor(phase4.valeurs_predites(critique, ech_a.observations))
        base_t = torch.tensor(phase4.valeurs_predites(critique, ech_t.observations))
    print(f"\ncritique de la phase 3 : R2 apprentissage {_r2(y_a, base_a):+.4f}   "
          f"R2 TEST {_r2(y_t, base_t):+.4f}")

    torch.manual_seed(0)
    regresseur = nn.Sequential(
        nn.Linear(x_a.shape[1], largeur), nn.ReLU(),
        nn.Linear(largeur, largeur), nn.ReLU(),
        nn.Linear(largeur, 1),
    )
    optimiseur = optim.Adam(regresseur.parameters(), lr=1e-3)
    debut = time.perf_counter()
    nb = len(y_a)
    for epoque in range(epoques):
        ordre = torch.randperm(nb)
        for depart in range(0, nb, 1024):
            indices = ordre[depart : depart + 1024]
            perte = nn.functional.mse_loss(
                regresseur(x_a[indices]).squeeze(-1), y_a[indices]
            )
            optimiseur.zero_grad(set_to_none=True)
            perte.backward()
            optimiseur.step()
        if epoque % 5 == 4 or epoque == epoques - 1:
            with torch.no_grad():
                ra = _r2(y_a, regresseur(x_a).squeeze(-1))
                rt = _r2(y_t, regresseur(x_t).squeeze(-1))
            print(f"  epoque {epoque + 1:3d} : R2 apprentissage {ra:+.4f}   R2 TEST {rt:+.4f}")

    print(f"\najustement supervise : {time.perf_counter() - debut:.1f} s, "
          f"largeur {largeur}, {epoques} epoques")


if __name__ == "__main__":
    main(
        int(sys.argv[1]) if len(sys.argv) > 1 else 4000,
        int(sys.argv[2]) if len(sys.argv) > 2 else 256,
        int(sys.argv[3]) if len(sys.argv) > 3 else 30,
    )
