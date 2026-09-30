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
                  rollout: str = "greedy", statuts: bool = False):
    """`statuts=True` : le reseau est un `experiences.statuts.Reseau` (agent a tete de statuts,
    statuts x1 + valeur x10) au lieu d'un `valeur.V`."""
    if statuts:
        from experiences.statuts import agent_statuts

        def jouer(r, mondes_ciblage=8):
            return agent_statuts(r, chemin, poids_statuts=1, poids_valeur=10,
                                 mondes_ciblage=mondes_ciblage)
    else:
        def jouer(r, mondes_ciblage=8):
            return agent_valeur(r, chemin, mondes_ciblage=mondes_ciblage)
    appris = jouer(rng)

    def simule(r: random.Random):
        if rollout == "valeur":
            return jouer(r, mondes_ciblage=2)
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


def greedy_departage(rng: random.Random, chemin: str):
    """Le greedy, dont les EGALITES sont departagees par le reseau au lieu du hasard.

    Mesure ce que rapporte le seul departage : le greedy a plusieurs coups optimaux dans
    93 % des premieres decisions et plus d'une fois sur deux ensuite
    (`experiences/ressemblance.py`). Hors egalite, il joue exactement comme le greedy.
    """
    appris = agent_valeur(rng, chemin)
    from experiences.rapide import tenseur_rapide
    from experiences.valeur import _charger

    net = _charger(chemin)

    def pol(etat: State) -> int:
        moi = etat.current_player()
        legales = etat.legal_actions()
        if len(legales) == 1:
            return legales[0]
        valeurs = greedy.evaluer_actions(percevoir(etat, moi))
        m = max(valeurs.values())
        optimaux = [a for a, v in valeurs.items() if v == m]
        if len(optimaux) == 1:
            return optimaux[0]
        if etat.phase() is Phase.CIBLAGE:
            # Au ciblage, l'apres-coup sur l'etat reel revelerait un dos tue : on passe par
            # l'agent aveugle, restreint aux coups optimaux du greedy.
            choix = appris(etat)
            return choix if choix in optimaux else rng.choice(optimaux)
        import numpy as np
        import torch

        vues = []
        for a in optimaux:
            s = etat.clone()
            appliquer(s, a)
            vues.append(tenseur_rapide(s, moi))
        with torch.no_grad():
            p = net(torch.from_numpy(np.asarray(vues, dtype=np.float32)))
        score = (p[:, 0] + 0.05 * p[:, 1]).tolist()
        mm = max(score)
        return rng.choice([a for a, x in zip(optimaux, score, strict=True) if x == mm])

    return pol
