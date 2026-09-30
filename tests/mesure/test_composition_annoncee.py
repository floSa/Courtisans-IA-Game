"""La composition ANNONCEE est celle qui est jouee : deux adversaires, deux aleas.

`phase3.jouer_composition` est appelee par `mesure/phase3_mesure.py` -- le juge -- et par
`agents/campagne.py` -- le garde-fou. C'est donc le chemin du chiffre qui decide, et de celui
qui peut arreter un run.

Ce que la docstring promet : « Les deux [adversaires] recoivent des aleas **distincts** : deux
copies d'une politique aleatoire partageant un generateur joueraient de facon correlee, ce qui
n'est pas la composition annoncee. » Le commentaire du corps le redit autrement : « Un alea par
(donne, siege de l'agent, place) : deux adversaires ne partagent jamais de generateur. »

Deux adversaires correles ne sont pas deux adversaires. Le gain publie serait celui d'une autre
composition que celle que son intitule nomme -- **la faute maison du projet**, un chiffre exact
sur une population que sa phrase ne nomme pas.
"""

from __future__ import annotations

import random

from mesure import phase3
from mesure.instance import ENTRAINEMENT_3J

CONFIG = ENTRAINEMENT_3J


def test_les_deux_adversaires_d_une_partie_ne_partagent_ni_generateur_ni_etat():
    """ETABLIT : dans chaque partie, les deux adversaires recoivent deux generateurs distincts.

    POPULATION : les 4 donnes x 3 sieges = 12 parties d'une campagne, soit **24 adversaires**
    instancies ; chacun est examine deux fois, par identite d'objet et par etat interne.

    Les deux controles ne sont pas redondants et ne prennent pas la meme faute : passer deux
    fois le MEME objet se voit a l'identite ; passer deux objets construits sur la MEME graine
    ne se voit qu'a l'etat interne, et produit exactement la meme correlation. Une composition
    peut donc etre fausse sans qu'aucun objet ne soit partage.
    """
    appels: list[tuple[str, random.Random]] = []

    def adversaire_temoin(alea: random.Random):
        appels.append(("adversaire", alea))
        return lambda etat: etat.legal_actions()[0]

    def agent_temoin(alea: random.Random):
        appels.append(("agent", alea))
        return lambda etat: etat.legal_actions()[0]

    phase3.jouer_composition(
        agent=agent_temoin,
        adversaire=adversaire_temoin,
        donnes=4,
        intitule="temoin : 1 agent contre 2 adversaires, 4 donnes",
        depart=0,
    )

    # Les politiques sont construites dans l'ordre des PLACES, pas « l'agent d'abord » : le
    # siege mesure est a la place `siege`, donc au rang 0, 1 ou 2 selon la partie. Le
    # decoupage se fait donc par paquets de `joueurs`, jamais sur le rang de l'agent.
    parties = [
        appels[i : i + CONFIG.joueurs]
        for i in range(0, len(appels), CONFIG.joueurs)
    ]
    assert len(parties) == 4 * CONFIG.joueurs, (
        f"{len(parties)} parties instrumentees, attendu {4 * CONFIG.joueurs}"
    )
    for numero, partie in enumerate(parties):
        adversaires = [alea for role, alea in partie if role == "adversaire"]
        assert len(adversaires) == CONFIG.joueurs - 1, (
            f"partie {numero} : {len(adversaires)} adversaires instancies"
        )
        premier, second = adversaires
        assert premier is not second, (
            f"partie {numero} : le MEME generateur est passe aux deux adversaires -- "
            f"ils tirent la meme suite et jouent correles"
        )
        assert premier.getstate() != second.getstate(), (
            f"partie {numero} : deux generateurs distincts mais de MEME etat initial -- "
            f"ils tirent la meme suite, la correlation est identique au cas precedent"
        )


def test_aucun_alea_d_adversaire_n_est_reutilise_dans_toute_la_campagne():
    """ETABLIT : les 24 adversaires d'une campagne portent 24 etats initiaux deux a deux distincts.

    POPULATION : la meme campagne de 4 donnes x 3 sieges, tous adversaires confondus.

    Le cas precedent regarde DANS une partie ; celui-ci regarde ENTRE les parties. La docstring
    indexe l'alea par `(donne, siege de l'agent, place)` : les trois composantes sont
    necessaires, et un index qui en oublierait une ferait rejouer la meme suite d'un siege a
    l'autre ou d'une donne a l'autre. Les trois sieges d'une donne ne seraient alors plus trois
    permutations independantes, et l'agregation « sur les trois sieges » compterait trois fois
    la meme partie.
    """
    etats: list[tuple] = []

    def adversaire_temoin(alea: random.Random):
        etats.append(alea.getstate())
        return lambda etat: etat.legal_actions()[0]

    phase3.jouer_composition(
        agent=lambda alea: (lambda etat: etat.legal_actions()[0]),
        adversaire=adversaire_temoin,
        donnes=4,
        intitule="temoin : unicite des aleas adverses sur toute la campagne",
        depart=0,
    )

    attendu = 4 * CONFIG.joueurs * (CONFIG.joueurs - 1)
    assert len(etats) == attendu
    assert len(set(etats)) == attendu, (
        f"{attendu - len(set(etats))} adversaires sur {attendu} rejouent une suite deja "
        f"tiree ailleurs dans la campagne"
    )


def test_l_agent_et_les_adversaires_ne_partagent_pas_non_plus_leur_alea():
    """ETABLIT : l'alea du siege mesure est distinct de ceux des deux adversaires.

    POPULATION : les 12 parties de la meme campagne, soit 12 agents et 24 adversaires.

    La separation des aleas est une regle du projet et pas seulement une precaution locale --
    « l'alea de tirage, distinct de celui de la donne et de celui d'un eventuel adversaire.
    Sans cette separation, on ne saurait pas laquelle des trois fait varier un chiffre ». Le
    decalage des graines existe pour ca (`decalage_agent`, `decalage_adversaire`) et rien ne
    verifiait qu'il tenait.
    """
    appels: list[tuple[str, tuple]] = []

    def agent_temoin(alea: random.Random):
        appels.append(("agent", alea.getstate()))
        return lambda etat: etat.legal_actions()[0]

    def adversaire_temoin(alea: random.Random):
        appels.append(("adversaire", alea.getstate()))
        return lambda etat: etat.legal_actions()[0]

    phase3.jouer_composition(
        agent=agent_temoin,
        adversaire=adversaire_temoin,
        donnes=4,
        intitule="temoin : l'agent ne partage pas l'alea de ses adversaires",
        depart=0,
    )

    parties = [
        appels[i : i + CONFIG.joueurs]
        for i in range(0, len(appels), CONFIG.joueurs)
    ]
    assert len(parties) == 4 * CONFIG.joueurs
    for numero, partie in enumerate(parties):
        (agent,) = [etat for role, etat in partie if role == "agent"]
        adversaires = [etat for role, etat in partie if role == "adversaire"]
        assert len(adversaires) == CONFIG.joueurs - 1
        assert agent not in adversaires, (
            f"partie {numero} : le siege mesure tire la meme suite qu'un de ses adversaires"
        )
