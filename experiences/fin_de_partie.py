"""L'agent hybride : l'IA apprise pendant la partie, un calcul quasi exact a la fin.

Idee de l'auteur du jeu (27/09) : la strategie cherchee est « un greedy, mais qui devient
strategique en fin de partie, en fonction des cartes qui restent ». En fin de partie, le
residu est connu, il reste peu d'Espions caches et peu de coups : on peut SIMULER toutes les
suites au lieu de les estimer.

Tant qu'il reste au decideur plus de `tours_fin` tours (celui en cours compris), l'agent joue
l'IA apprise (`agent_valeur`). Ensuite, pour chaque action legale et dans `nb_mondes` mondes
tires a l'aveugle (identite des dos adverses, ordre de la pioche), il joue la partie
JUSQU'AU BOUT -- les adversaires et ses propres coups suivants par la politique `rollout` --
et choisit l'action de meilleur gain moyen (ecart de score en bris d'egalite). Au tout
dernier coup de la partie, il n'y a plus rien a simuler : la moyenne sur les mondes est
l'esperance exacte sous l'incertitude des Espions.
"""

from __future__ import annotations

import random

from agents import greedy
from agents.perception import percevoir
from courtisans.engine import Phase, State
from experiences.pimc import _valeur, determiniser
from experiences.rapide import appliquer
from experiences.valeur import agent_valeur


def fin_de_partie(rng: random.Random, chemin: str, tours_fin: int = 1, nb_mondes: int = 16,
                  rollout: str = "greedy"):
    appris = agent_valeur(rng, chemin)

    def simule(r: random.Random):
        if rollout == "valeur":
            return agent_valeur(r, chemin, mondes_ciblage=2)
        return lambda s: greedy.choisir(percevoir(s, s.current_player()), r)

    def pol(etat: State) -> int:
        moi = etat.current_player()
        legales = etat.legal_actions()
        if len(legales) == 1:
            return legales[0]
        if etat.tours_restants(moi) + (1 if etat.phase() is Phase.CIBLAGE else 0) > tours_fin:
            return appris(etat)
        totaux = dict.fromkeys(legales, 0.0)
        for _ in range(nb_mondes):
            monde = determiniser(etat, moi, rng)
            politique = simule(random.Random(rng.random()))
            for a in legales:
                s = monde.clone()
                appliquer(s, a)
                while not s.is_terminal():
                    appliquer(s, politique(s))
                totaux[a] += _valeur(s, moi)
        m = max(totaux.values())
        return rng.choice([a for a, v in totaux.items() if v == m])

    return pol
