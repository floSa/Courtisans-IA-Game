"""Agent de recherche PIMC (Perfect Information Monte Carlo) pour Courtisans.

Principe : a chaque decision, on echantillonne K mondes compatibles avec ce que le
decideur sait (identite des Espions adverses + ordre de la pioche), on joue chaque action
legale dans chaque monde, puis on termine la partie avec une politique de rollout
(le greedy de reference pour les trois sieges). On choisit l'action de meilleur gain moyen.

Aveuglement : la determinisation ne lit dans l'etat que ce que le decideur connait
(cartes visibles, sa main, ses propres Espions, la defausse publique, les positions des
dos). L'identite des dos adverses et l'ordre de la pioche sont re-tires au hasard.
"""

from __future__ import annotations

import random
from collections.abc import Callable

from agents import greedy
from agents.perception import percevoir
from courtisans import rules
from courtisans.cards import CartePosee, Role
from courtisans.engine import Phase, State

Politique = Callable[[State], int]


def determiniser(etat: State, moi: int, rng: random.Random) -> State:
    """Un monde tire uniformement parmi ceux compatibles avec la vue de `moi`."""
    vp = etat.vue_privilegiee()
    for j, main in enumerate(vp.mains):
        if j != moi and main:
            raise AssertionError("main adverse non vide pendant une decision")
    cachees = [
        i
        for i, p in enumerate(vp.posees)
        if p.carte.role is Role.ESPION and p.poseur != moi
    ]
    connues = set(vp.mains[moi])
    connues.update(p.carte for i, p in enumerate(vp.posees) if i not in set(cachees))
    connues.update(p.carte for p in vp.defausse)
    inconnues = [c for c in rules.paquet(etat.config) if c not in connues]
    assert len(inconnues) == len(vp.pioche) + len(cachees)
    espions = [c for c in inconnues if c.role is Role.ESPION]
    rng.shuffle(espions)
    affectes = espions[: len(cachees)]
    reste = [c for c in inconnues if c not in set(affectes)]
    rng.shuffle(reste)
    posees = list(vp.posees)
    for i, carte in zip(cachees, affectes, strict=True):
        p = posees[i]
        posees[i] = CartePosee(carte, p.zone, p.poseur)
    # Assassins en attente : visibles, donc inchanges ; on les re-pointe sur les objets
    # du nouveau plateau par egalite de valeur.
    monde = etat.clone()
    monde._posees = posees
    monde._pioche = reste
    return monde


def greedy_rollout(rng: random.Random) -> Politique:
    def pol(etat: State) -> int:
        return greedy.choisir(percevoir(etat, etat.current_player()), rng)

    return pol


def jouer_jusquau_bout(etat: State, politique: Politique) -> list[float]:
    while not etat.is_terminal():
        etat.apply(politique(etat))
    return etat.returns()


def _valeur(etat: State, moi: int) -> float:
    """Gain final + un depart infinitesimal par l'ecart de score (bris d'egalite)."""
    g = etat.returns()[moi]
    s = etat.scores()
    ecart = s[moi] - max(v for j, v in s.items() if j != moi)
    return g + 0.001 * ecart


def pimc(
    nb_mondes: int,
    rng: random.Random,
    rollout: Callable[[random.Random], Politique] = greedy_rollout,
    ciblage_pimc: bool = True,
) -> Politique:
    def pol(etat: State) -> int:
        moi = etat.current_player()
        legales = etat.legal_actions()
        if len(legales) == 1:
            return legales[0]
        if etat.phase() is Phase.CIBLAGE and not ciblage_pimc:
            return greedy.choisir(percevoir(etat, moi), rng)
        totaux = dict.fromkeys(legales, 0.0)
        for _ in range(nb_mondes):
            monde = determiniser(etat, moi, rng)
            politique = rollout(random.Random(rng.random()))
            for a in legales:
                s = monde.clone()
                s.apply(a)
                while not s.is_terminal():
                    s.apply(politique(s))
                totaux[a] += _valeur(s, moi)
        meilleur = max(totaux.values())
        return rng.choice([a for a, v in totaux.items() if v == meilleur])

    return pol
