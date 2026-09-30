"""Les trois reserves de la phase 3, levees **avec leur parade** et non avec leur seul rendu.

Une reserve levee dont la mutation survit toujours n'est pas levee : elle est reecrite. Ce
fichier porte, pour chacune des trois, le cas qui la ferait revenir en tombant.

Reserve 1 -- la LATERALITE. Le rapport ecrivait « borne haute a 99 % » pour une borne de
Clopper-Pearson **unilaterale au risque 1 %**. Aucune conclusion ne changeait : l'agent vaut
35,87 % et 3,66 %, il est au-dela de la lecture unilaterale comme de la bilaterale. Mais un
lecteur qui recalcule en bilateral trouve 0,2690 % et 0,0510 % la ou le document publie
0,2338 % et 0,0443 %, et il ne peut pas savoir lequel des deux il tient.

Reserve 2 -- les QUATRE cas du taux degenere, dont le rendu n'en redigeait qu'un.

Reserve 3 -- la parade des intitules, qui ne couvrait qu'une forme d'appel : voir
`tests/mesure/test_phase3_audit.py`, ou la parade vit et ou son cas neuf est pose.
"""

from __future__ import annotations

import math

from mesure import comportements as comp
from mesure import phase3_mesure
from mesure import rapport_phase3


def _compte(succes: int, total: int) -> comp.Compte:
    return comp.Compte(nom="X", succes=succes, total=total, grain="parties", vue="publique")


def _comparaison(agent: comp.Compte, base: comp.Compte) -> phase3_mesure.Comparaison:
    """Une `Comparaison` tranchee par la regle des bornes exactes, cablee comme `comparer`."""
    separation = phase3_mesure.separer_un_taux_degenere(agent, base)
    assert separation is not None
    taux_agent, taux_base = agent.taux(), base.taux()
    return phase3_mesure.Comparaison(
        nom="X",
        agent=agent,
        base=base,
        ecart=(taux_agent - taux_base)
        if taux_agent is not None and taux_base is not None
        else None,
        detectable=None,
        separable=separation.disjoints,
        regle=phase3_mesure.REGLE_BORNES_EXACTES,
        borne_exacte=separation.borne,
        parties_requises=None,
        exclu=None,
        separation=separation,
    )


# ---------------------------------------------------------------------------------
# Reserve 1 -- la lateralite de la borne exacte
# ---------------------------------------------------------------------------------


def test_la_borne_exacte_publiee_est_bien_l_UNILATERALE_et_pas_la_bilaterale():
    """ETABLIT : la borne calculee est celle du risque 1 % **entier dans une queue**.

    POPULATION : les deux zeros reels de la ligne de base de la phase 3 -- `0/1967` et
    `0/10382`.

    Les deux lectures sont recalculees ici a la main, sans passer par le module : la fonction
    doit rendre **l'unilaterale**, et elle doit en etre distinguable. Si les deux nombres
    coincidaient, l'etiquette n'aurait aucune consequence et la reserve n'existerait pas.
    """
    for total, attendu_uni, attendu_bil in ((1967, 0.002338, 0.002690), (10382, 0.000443, 0.000510)):
        rendu = phase3_mesure.borne_haute_exacte_d_un_zero(total)
        unilaterale = 1.0 - 0.01 ** (1.0 / total)
        bilaterale = 1.0 - 0.005 ** (1.0 / total)

        assert math.isclose(rendu, unilaterale, rel_tol=1e-12), (
            f"0/{total} : la fonction rend {rendu:.6%}, l'unilaterale a 1 % vaut "
            f"{unilaterale:.6%}"
        )
        assert not math.isclose(rendu, bilaterale, rel_tol=1e-6), (
            f"0/{total} : unilaterale et bilaterale coincident, le cas ne separe rien"
        )
        assert math.isclose(rendu, attendu_uni, abs_tol=5e-7)
        assert math.isclose(bilaterale, attendu_bil, abs_tol=5e-7)


def test_aucune_borne_exacte_ne_se_publie_sans_dire_de_quel_cote_elle_est_prise():
    """ETABLIT : toute phrase de verdict par bornes exactes porte sa lateralite.

    POPULATION : les quatre cas de taux degenere, rediges par `_phrase_de_borne_exacte`.

    C'est la parade de la reserve 1, et elle est **dans le generateur**, pas dans le document :
    `mesure/resultats/phase3.md` est produit par ce code. Corriger le seul fichier laisserait
    l'etiquette fausse revenir a la generation suivante.
    """
    cas = (
        _comparaison(_compte(1368, 3814), _compte(0, 1967)),
        _comparaison(_compte(0, 1967), _compte(1368, 3814)),
        _comparaison(_compte(20, 20), _compte(700, 1000)),
        _comparaison(_compte(0, 500), _compte(700, 700)),
    )
    for comparaison in cas:
        phrase = rapport_phase3._phrase_de_borne_exacte(comparaison)
        assert "unilaterale" in phrase, (
            f"une borne exacte est publiee sans sa lateralite : {phrase!r}"
        )
        assert "a 99 %" not in phrase, (
            f"« a 99 % » sur une borne unilaterale : l'etiquette dit un intervalle bilateral, "
            f"dont la queue vaut 0,5 % et non 1 %. Phrase : {phrase!r}"
        )


# ---------------------------------------------------------------------------------
# Reserve 2 -- les quatre cas, et le rendu qui n'en redigeait qu'un
# ---------------------------------------------------------------------------------


def test_un_zero_du_cote_de_l_AGENT_n_est_pas_attribue_a_la_ligne_de_base():
    """ETABLIT : le verdict nomme le cote qui porte reellement le taux degenere.

    POPULATION : la ligne symetrique du cas reel de la phase 3 -- l'agent a `0/1967`, la ligne
    de base a `1368/3814`.

    Le rendu ecrivait « le zero **de la ligne de base** » en dur. Sur cette ligne-ci, la phrase
    aurait nomme le mauvais camp -- et elle aurait ete lue comme « l'agent fait ce que le
    greedy ne fait jamais » quand c'est exactement l'inverse. Une phrase fausse dans un tableau
    juste est plus dangereuse qu'un tableau faux : rien ne la contredit.
    """
    phrase = rapport_phase3._phrase_de_borne_exacte(
        _comparaison(_compte(0, 1967), _compte(1368, 3814))
    )
    assert "de agent" in phrase or "de l'agent" in phrase, phrase
    assert "ligne de base" not in phrase, (
        f"le zero est du cote de l'agent et la phrase l'attribue a la ligne de base : {phrase!r}"
    )


def test_un_taux_a_CENT_POUR_CENT_n_est_pas_annonce_comme_un_zero():
    """ETABLIT : un cote a 100 % est annonce comme tel, avec une borne BASSE.

    POPULATION : un agent a `20/20` contre une ligne de base a `700/1000`.

    La phase 3 ne porte aucun taux a 100 %, et c'est precisement pourquoi ce cas manquait.
    `borne_basse_exacte_d_un_cent` existe depuis le tour 2 « pour une phase suivante qui en
    produirait un » -- et le rendu, lui, aurait annonce « le zero » avec une « borne haute ».
    Deux mots faux sur un nombre juste.
    """
    phrase = rapport_phase3._phrase_de_borne_exacte(
        _comparaison(_compte(20, 20), _compte(700, 1000))
    )
    assert "cent pour cent" in phrase, phrase
    assert "borne basse" in phrase, phrase
    assert "le zero" not in phrase, phrase


def test_les_deux_cotes_degeneres_au_MEME_bout_sont_annonces_comme_un_ecart_nul():
    """ETABLIT : deux cotes a 0 % rendent un verdict d'ecart nul, sans parler d'un intervalle.

    POPULATION : `0/500` contre `0/700` -- un comportement qu'aucun des deux joueurs ne
    manifeste jamais, ce qui est parfaitement banal.

    C'est le cas que le calcul avait failli oublier et que le rendu avait oublie : il aurait
    parle de « l'intervalle de l'autre cote », qui n'existe pas -- l'autre cote est degenere
    lui aussi et n'a pas d'intervalle normal.
    """
    phrase = rapport_phase3._phrase_de_borne_exacte(
        _comparaison(_compte(0, 500), _compte(0, 700))
    )
    assert "exactement nul" in phrase, phrase
    assert "intervalle de l'autre cote" not in phrase, phrase


def test_les_deux_cotes_degeneres_aux_bouts_OPPOSES_sont_separables_par_construction():
    """ETABLIT : `0 %` contre `100 %` est annonce separable, et sans nommer un seul cote.

    POPULATION : `0/500` contre `700/700`.
    """
    phrase = rapport_phase3._phrase_de_borne_exacte(
        _comparaison(_compte(0, 500), _compte(700, 700))
    )
    assert "**separable**" in phrase, phrase
    assert "bouts opposes" in phrase, phrase


def test_un_seul_cote_degenere_dont_les_bornes_SE_CROISENT_n_est_PAS_separable():
    """ETABLIT : la branche a un seul degenere rend `disjoints = False` quand les bornes se croisent.

    POPULATION : un agent a `30/100` = 30,0 % contre une ligne de base a `0/20`. La borne
    exacte du zero vaut **20,57 %** ; la borne basse de l'intervalle normal de l'agent vaut
    **18,20 %**. Elles se croisent, donc l'ecart n'est pas etabli.

    **C'est la parade qui manquait, et c'est pour ca que la mutation survivait.** Les quatre
    cas etaient testes, mais **tous avec des donnees separables** du cote a un seul degenere :
    un calcul qui rendrait « disjoints » sur cette branche quoi qu'il arrive passait les quatre.
    Un predicat ne se teste pas sur les seules donnees qui le rendent vrai.

    Les deux bornes sont recalculees ici a la main : le cas ne demande pas au module de se
    confirmer lui-meme.
    """
    agent, base = _compte(30, 100), _compte(0, 20)
    separation = phase3_mesure.separer_un_taux_degenere(agent, base)
    assert separation is not None

    borne_du_zero = 1.0 - 0.01 ** (1.0 / 20)
    taux = 30 / 100
    demi = 2.5758293035489004 * (taux * (1 - taux) / 100) ** 0.5
    borne_de_l_agent = taux - demi
    assert borne_de_l_agent < borne_du_zero, (
        f"les bornes recalculees ne se croisent pas ({borne_de_l_agent:.4%} contre "
        f"{borne_du_zero:.4%}) : le cas ne teste pas ce qu'il annonce"
    )

    assert not separation.disjoints, (
        f"la borne du zero vaut {separation.borne:.4%} et celle de l'autre cote "
        f"{separation.borne_de_l_autre:.4%} : elles se croisent, et l'ecart est declare etabli"
    )
    assert separation.cote == "ligne de base"

    phrase = rapport_phase3._phrase_de_borne_exacte(_comparaison(agent, base))
    assert phrase.startswith("non separable"), phrase


def test_un_seul_cote_a_CENT_dont_les_bornes_se_croisent_n_est_pas_separable_non_plus():
    """ETABLIT : la meme branche, du cote du cent, refuse aussi de conclure quand les bornes se croisent.

    POPULATION : un agent a `20/20` = 100 % contre une ligne de base a `18/20` = 90 %.

    Le symetrique du cas precedent. Les deux branches du meme `if` sont ecrites separement, et
    tester l'une ne dit rien de l'autre.
    """
    separation = phase3_mesure.separer_un_taux_degenere(_compte(20, 20), _compte(18, 20))
    assert separation is not None
    assert separation.cote == "agent"
    assert not separation.disjoints, (
        f"borne basse du cent {separation.borne:.4%}, borne haute de l'autre "
        f"{separation.borne_de_l_autre:.4%} : elles se croisent"
    )


# ---------------------------------------------------------------------------------
# Reserve 3 -- le nom du garde-fou porte sa POPULATION, et pas seulement sa composition
# ---------------------------------------------------------------------------------


def test_le_nom_du_garde_fou_porte_le_nombre_de_donnes_et_le_depart_des_seeds():
    """ETABLIT : l'intitule contient l'agent, le nombre de donnes et le depart des seeds.

    POPULATION : `intitule_du_garde_fou` a son defaut et a trois autres nombres de donnes.

    La docstring l'ecrit en toutes lettres : « Le nom porte donc desormais **l'agent, le
    nombre de donnes et le depart des seeds** ». Rien ne le tenait.

    **C'est une parade DIFFERENTE de celle des doublons, et le rejeu du 24/08 l'a montre.**
    La parade des intitules ne mord que sur une COLLISION : deux campagnes qui portent le meme
    nom. Un nom vide de sa population ne collisionne avec rien tant que son quasi-jumeau du
    pool -- « 1 agent entraine FINAL contre 2 aleatoires, 500 donnes, seeds 70000+ » -- garde
    le sien. La mutation `intitule-du-garde-fou-sans-population` a donc survecu a l'elargissement
    de la parade des doublons, qui traitait pourtant bien l'angle mort que la reserve nommait.

    **Deux parades pour un meme defaut, et elles ne se remplacent pas** : l'une empeche deux
    campagnes de porter le meme nom, l'autre empeche un nom de ne rien dire. La faute de la
    phase 3 -- 70,13 % et 70,03 % publies sous le meme intitule -- demandait les deux.
    """
    from agents import campagne as campagne_module

    nom = campagne_module.intitule_du_garde_fou()
    assert str(campagne_module.DONNES_GARDE_FOU) in nom, (
        f"le nom ne porte pas son nombre de donnes ({campagne_module.DONNES_GARDE_FOU}) : "
        f"{nom!r}"
    )
    assert str(campagne_module.DEPART_DONNE_GARDE_FOU) in nom, (
        f"le nom ne porte pas le depart de ses seeds "
        f"({campagne_module.DEPART_DONNE_GARDE_FOU}) : {nom!r}"
    )
    assert "agent" in nom, f"le nom ne dit pas quel agent est mesure : {nom!r}"


def test_deux_populations_differentes_ne_peuvent_pas_porter_le_meme_nom_de_garde_fou():
    """ETABLIT : changer le nombre de donnes change l'intitule.

    POPULATION : quatre appels a `intitule_du_garde_fou`, a 100, 500, 600 et 1200 donnes.

    C'est la propriete qui compte, et elle est plus forte que « le nom contient tel nombre » :
    **deux campagnes qui ne partagent pas leur population ne doivent pas partager leur nom.**
    C'est exactement la faute de la phase 3 -- 600 donnes en 40000+ d'un cote, 500 donnes en
    70000+ de l'autre, 70,13 % et 70,03 % publies sous le meme intitule, et le controle R2
    « les noms sont distincts » qui ne voyait rien.

    Un nom qui ne varie pas avec sa population rend cette faute reproductible sans qu'aucun
    controle ne bouge.
    """
    from agents import campagne as campagne_module

    noms = {
        donnes: campagne_module.intitule_du_garde_fou(donnes)
        for donnes in (100, 500, 600, 1200)
    }
    assert len(set(noms.values())) == len(noms), (
        f"deux populations distinctes portent le meme nom : {noms}"
    )
