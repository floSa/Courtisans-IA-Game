"""Deux frontieres du chemin de decision : **quel siege est observe**, et **ou l'on ne decide pas**.

Les deux appartiennent a la meme famille que la preuve P2, et **aucune des deux n'est P2**.
P2 etablit qu'un agent ne lit pas `vue_privilegiee` pendant sa decision. Elle ne dit rien sur
le siege qu'il observe : un agent qui lirait toujours l'info-set du siege 0 respecterait P2
parfaitement -- il ne triche pas, il se trompe de joueur.

La campagne de mutation de l'etape 0 a mesure que ce second point n'etait tenu par rien, sur
`agents/politique_reseau.py` **qui est le chemin de decision de l'agent mesure**, et que la
levee de `perception.percevoir` sur les nœuds sans decision ne l'etait pas davantage, sur
`agents/perception.py` qui est celui de l'etalon.
"""

from __future__ import annotations

import random

import pytest
import torch

from agents import entrainement
from agents import perception as perception_module
from agents import politique_reseau as pr
from agents import reseau as reseau_module
from courtisans.engine import Engine, Phase
from courtisans.infoset import tenseur
from mesure.instance import ENTRAINEMENT_3J

CONFIG = ENTRAINEMENT_3J
APPAREIL = torch.device("cpu")


# ---------------------------------------------------------------------------------
# Le siege observe est celui qui decide
# ---------------------------------------------------------------------------------


def _argmax_legal_depuis_le_siege(
    modele: reseau_module.ReseauPolitiqueValeur, etat, joueur: int
) -> int:
    """Reimplemente le choix deterministe, a la main, depuis l'info-set de `joueur`.

    Reimplemente, et non appele : un cas qui rappellerait `reseau.choisir_le_plus_probable`
    ne comparerait que la fonction a elle-meme. C'est la meme raison qui fait qu'un auditeur
    reimplemente au lieu de relire.
    """
    with torch.no_grad():
        entree = torch.tensor([list(tenseur(etat, joueur))], dtype=torch.float32)
        logits, _ = modele(entree)
    scores = logits[0].tolist()
    legales = etat.legal_actions()
    return min(legales, key=lambda a: (-scores[a], a))


def test_la_politique_du_reseau_observe_le_siege_QUI_DECIDE_et_pas_un_siege_fixe():
    """ETABLIT : la decision du reseau est celle qu'on obtient depuis l'info-set du decideur.

    POPULATION : tous les nœuds de decision de 12 parties completes d'`entrainement-3j`, joues
    par la politique deterministe du reseau -- et le cas compte combien de ces nœuds ont un
    decideur AUTRE que le siege 0, puis exige que ce compte soit non nul.

    Le module ecrit : « Cette fonction ecrit `tenseur(etat, etat.current_player())`. C'est
    exactement la ligne que l'obstacle A rendait dangereuse. » Observer un siege fixe ne
    violerait aucune preuve d'aveuglement -- l'info-set du siege 0 est un info-set legitime --
    et l'agent jouerait pourtant les mains des autres. Le compte des nœuds a decideur non nul
    est publie dans le message d'echec parce qu'un cas qui n'en rencontrerait aucun passerait
    en ne testant rien.
    """
    modele = entrainement.construire(APPAREIL)
    moteur = Engine(CONFIG)
    politique = pr.politique_reseau_deterministe(modele)

    noeuds = 0
    noeuds_hors_siege_zero = 0
    for donne in range(12):
        etat = moteur.reset(donne)
        while not etat.is_terminal():
            decideur = etat.current_player()
            attendu = _argmax_legal_depuis_le_siege(modele, etat, decideur)
            obtenu = politique(etat)
            assert obtenu == attendu, (
                f"donne {donne}, decideur {decideur} : la politique a joue {obtenu}, "
                f"l'info-set du decideur donne {attendu}"
            )
            noeuds += 1
            if decideur != 0:
                noeuds_hors_siege_zero += 1
            etat.apply(obtenu)

    assert noeuds > 0
    assert noeuds_hors_siege_zero > 0, (
        f"{noeuds} nœuds parcourus et pas un seul dont le decideur ne soit le siege 0 : "
        f"le cas ne separe pas 'le siege qui decide' de 'le siege 0'"
    )


def test_la_politique_STOCHASTIQUE_observe_elle_aussi_le_siege_qui_decide():
    """ETABLIT : la porte d'entree ECHANTILLONNEE lit l'info-set du decideur, elle aussi.

    POPULATION : tous les nœuds de decision de 12 parties completes, joues par
    `politique_reseau` -- **la variante qui echantillonne**, celle que `evaluer_le_garde_fou`
    et la mesure appellent reellement. La deterministe, elle, est « rapportee a cote, jamais a
    sa place ».

    **Ce cas existe parce que le premier ne suffisait pas, et le rejeu du 24/08 l'a montre.**
    Un cas avait ete ecrit pour ce trou, et la mutation `politique-reseau-observe-le-siege-zero`
    **a survecu quand meme** : le cas ne parcourait que `politique_reseau_deterministe`. Le
    module a DEUX portes d'entree, la docstring enonce son invariant pour les deux -- « cette
    fonction ecrit `tenseur(etat, etat.current_player())` » -- et un cas qui n'en visite qu'une
    laisse l'autre a decouvert. Celle qui restait a decouvert etait celle qui mesure.

    La comparaison porte sur le COLLAGE et non sur le tirage : le choix est refait en passant
    a `reseau.choisir` l'info-set du decideur et un generateur de meme graine. Ce qui est
    tenu ici est « quel info-set est passe », qui est tout ce que ce module decide.
    """
    modele = entrainement.construire(APPAREIL)
    moteur = Engine(CONFIG)

    noeuds = 0
    noeuds_hors_siege_zero = 0
    for donne in range(12):
        etat = moteur.reset(donne)
        while not etat.is_terminal():
            decideur = etat.current_player()
            graine = 7_000 + 97 * donne + noeuds
            obtenu = pr.politique_reseau(modele, random.Random(graine))(etat)
            attendu = reseau_module.choisir(
                modele,
                tenseur(etat, decideur),
                etat.legal_actions(),
                random.Random(graine),
            )
            assert obtenu == attendu, (
                f"donne {donne}, decideur {decideur} : la politique echantillonnee a joue "
                f"{obtenu}, l'info-set du decideur avec le meme alea donne {attendu}"
            )
            noeuds += 1
            if decideur != 0:
                noeuds_hors_siege_zero += 1
            etat.apply(obtenu)

    assert noeuds > 0
    assert noeuds_hors_siege_zero > 0, (
        f"{noeuds} nœuds parcourus et pas un seul dont le decideur ne soit le siege 0"
    )


def test_toute_observation_construite_par_ce_module_porte_le_siege_QUI_DECIDE():
    """ETABLIT : sur les deux portes d'entree, `tenseur` n'est jamais appele sur un autre siege.

    POPULATION : tous les appels a `tenseur` faits par `agents/politique_reseau.py` pendant
    12 parties jouees par la politique echantillonnee et 12 par la deterministe.

    Les deux cas precedents tiennent chacun une porte, en refaisant le calcul. Celui-ci tient
    **la regle**, en regardant l'argument lui-meme : quel que soit le nombre de portes que ce
    module gagnera, aucune ne peut demander l'info-set d'un siege qui ne decide pas sans que
    ce cas tombe. Les deux formes ne sont pas redondantes -- une reimplementation prouve que
    le resultat est le bon, un temoin prouve que la REGLE est tenue partout.
    """
    vrai = pr.tenseur
    demandes: list[tuple[int, int]] = []

    def temoin(etat, joueur):
        demandes.append((etat.current_player(), joueur))
        return vrai(etat, joueur)

    moteur = Engine(CONFIG)
    modele = entrainement.construire(APPAREIL)
    fabriques = (
        lambda: pr.politique_reseau(modele, random.Random(4242)),
        lambda: pr.politique_reseau_deterministe(modele),
    )

    ancien = pr.tenseur
    pr.tenseur = temoin
    try:
        for fabrique in fabriques:
            politique = fabrique()
            for donne in range(12):
                etat = moteur.reset(donne)
                while not etat.is_terminal():
                    etat.apply(politique(etat))
    finally:
        pr.tenseur = ancien

    assert demandes, "aucune observation construite : le cas ne teste rien"
    fautifs = [(decideur, joueur) for decideur, joueur in demandes if decideur != joueur]
    assert not fautifs, (
        f"{len(fautifs)} observation(s) sur {len(demandes)} portent un siege qui ne decide "
        f"pas -- (decideur, siege observe) : {sorted(set(fautifs))}"
    )
    hors_zero = [d for d, _ in demandes if d != 0]
    assert hors_zero, (
        f"{len(demandes)} observations et pas une seule hors du siege 0 : le cas ne separe "
        f"pas 'le siege qui decide' de 'le siege 0'"
    )


def test_l_observation_du_reseau_ne_coincide_pas_avec_celle_du_siege_zero():
    """ETABLIT : sur les nœuds a decideur non nul, l'info-set du siege 0 n'est PAS le meme.

    POPULATION : les nœuds de decision de 12 parties dont le decideur n'est pas le siege 0.

    C'est le controle de non-vacuite du cas precedent, et il se mesure au lieu de se supposer.
    Si les info-sets des trois sieges etaient identiques, observer le siege 0 serait sans
    consequence et le cas precedent passerait sur du code faux.
    """
    moteur = Engine(CONFIG)
    alea = random.Random(11)
    compares = 0
    differents = 0
    for donne in range(12):
        etat = moteur.reset(donne)
        while not etat.is_terminal():
            decideur = etat.current_player()
            if decideur != 0:
                compares += 1
                if list(tenseur(etat, decideur)) != list(tenseur(etat, 0)):
                    differents += 1
            etat.apply(alea.choice(etat.legal_actions()))

    assert compares > 0
    assert differents == compares, (
        f"{compares - differents} nœuds sur {compares} ont le meme info-set vu du decideur "
        f"et vu du siege 0 : sur ceux-la, se tromper de siege serait indetectable"
    )


# ---------------------------------------------------------------------------------
# Les nœuds ou un agent ne decide pas
# ---------------------------------------------------------------------------------


def test_percevoir_leve_sur_un_noeud_de_chance_reel():
    """ETABLIT : `percevoir` leve sur un nœud de distribution produit par le moteur.

    POPULATION : l'etat initial de `reset_par_hasard`, qui est un nœud de chance, pour chacun
    des trois sieges.

    La clause `Raises:` dit pourquoi : « Un agent n'y decide rien, et rendre une `Perception`
    vide masquerait un pilote de partie fautif. » Le nœud est pris du moteur et non fabrique :
    un etat construit a la main pourrait etre impossible, et la levee ne prouverait alors rien
    sur les parties reelles.
    """
    etat = Engine(CONFIG).reset_par_hasard()
    assert etat.phase() is Phase.CHANCE
    for joueur in range(CONFIG.joueurs):
        with pytest.raises(ValueError, match="ne decide pas en phase CHANCE"):
            perception_module.percevoir(etat, joueur)


def test_percevoir_leve_sur_un_etat_terminal_reel():
    """ETABLIT : `percevoir` leve sur un etat terminal atteint en jouant une partie entiere.

    POPULATION : l'etat final de trois donnes jouees jusqu'au bout, pour chacun des trois sieges.

    Meme clause, meme raison. Les deux phases sont testees separement parce qu'un code qui ne
    garderait qu'une des deux passerait un cas qui les melange.
    """
    moteur = Engine(CONFIG)
    alea = random.Random(5)
    for donne in range(3):
        etat = moteur.reset(donne)
        while not etat.is_terminal():
            etat.apply(alea.choice(etat.legal_actions()))
        assert etat.phase() is Phase.TERMINAL
        for joueur in range(CONFIG.joueurs):
            with pytest.raises(ValueError, match="ne decide pas en phase TERMINAL"):
                perception_module.percevoir(etat, joueur)
