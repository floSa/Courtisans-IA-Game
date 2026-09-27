"""L'instance jouee, choisie par COURTISANS_INSTANCE : 'reduite' (defaut, 40 cartes) ou
'complete' (90 cartes, 3 joueurs, 10 tours -- le vrai jeu)."""
import os

from courtisans.cards import Role
from courtisans.config import GameConfig
from mesure.instance import ENTRAINEMENT_3J

COMPLETE_3J = GameConfig(familles=6, roles=tuple(Role), exemplaires=3, joueurs=3)
CONFIG = COMPLETE_3J if os.environ.get("COURTISANS_INSTANCE") == "complete" else ENTRAINEMENT_3J
