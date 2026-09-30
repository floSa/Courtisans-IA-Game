"""La mesure finale de la phase 3 : le juge, le pool, et les comportements au meme grain.

Ce module **n'invente aucun compteur et ne redefinit aucun seuil**. Il assemble ce qui existe :

  - le plan et le juge viennent de `mesure/phase3.py`, ecrits et commites avant l'entrainement ;
  - les dix-sept compteurs de comportement viennent de `mesure/comportements.py`, ecrits et
    **audites en phase 2**. Les reecrire ici dupliquerait une definition, ce que le paragraphe 2
    des conventions interdit -- et c'est la mesure qui aurait tort sans que rien ne le signale.

La ligne de base de comportement doit etre REGENEREE, et voici pourquoi
------------------------------------------------------------------------
La phase 2 publie ses compteurs sur deux populations : **un** greedy contre deux aleatoires
(un siege mesure) et **trois** greedys (trois sieges mesures). Aucune des deux n'est la mienne.

Ma composition est **un agent contre deux greedys**, un seul siege mesure. Sa ligne de base --
ce que le greedy obtiendrait a la place de l'agent -- est donc **trois greedys, UN seul siege
compte**. Elle n'existe pas dans le depot :

  - la colonne « 1 greedy, 2 hasards » a la bonne **granularite** mais pas la bonne
    **composition d'adversaires**. Pour `B1-collectif`, dont le numerateur peut etre produit
    entierement par les adversaires, ca change le chiffre ;
  - la colonne « 3 greedys » a la bonne composition mais pas le bon **grain** : elle agrege
    trois sieges mesures, et les lignes `-par-partie` -- « au moins un des N sieges » -- ne
    comptent alors pas la meme chose. `ecart_de_taux` **leve** dans ce cas, et c'est la parade
    posee au tour 2 de la phase 2.

**Ce module regenere donc la troisieme population a un seul siege compte, et rien d'autre ne
change** : memes seeds, meme composition, meme decalage de graine `6000000`. Seuls les sieges
**comptes** changent. Si autre chose bougeait, la ligne de base bougerait pour une seconde
raison et on ne saurait plus laquelle.

Ce qui n'est pas compare, et pourquoi -- deux criteres independants
---------------------------------------------------------------------
**Le budget.** Les marqueurs « hors budget » et « aveugle par le bas » sont des proprietes du
couple `(ligne, budget)`, pas de la ligne. Recalcules au budget de la phase 3 par
`mesure/phase3_budget_des_comportements.py` : **8 lignes hors budget** au lieu de 19, **0
aveugle** au lieu de 2.

**Le texte de la definition.** `B4-tout-dos` et `B5-renfort` ne se comparent pas entre
compositions differentes, et ca ne depend d'aucun budget : leurs taux bougent sous d'autres
agents pour une raison qui n'est pas l'habilete. Le critere se decide sur le TEXTE -- la
definition nomme-t-elle un autre joueur ? `B1-collectif` oui, ces deux-la non.

Les deux criteres sont **independants**. `B4-tout-dos` entre dans le budget a 6 000 parties et
reste exclu par le texte.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from mesure import comportements as comp
from mesure import dimensionnement as dim
from mesure import phase2, phase3

#: Le decalage de graine de la troisieme population de la phase 2. **Recopie tel quel**, et
#: c'est la contrainte : regenerer avec un autre decalage donnerait d'autres parties, donc une
#: ligne de base qui bouge pour une seconde raison.
DECALAGE_TROIS_GREEDYS = phase2.DECALAGE_POLITIQUE_3_GREEDYS

#: Les donnes de la campagne finale, et les deux decalages des compositions du pool.
#:
#: **TROUVE PAR MON PROPRE CONTROLE D'AUDIT, avant la mesure.** La premiere version partait a
#: `30000` et decalait les compositions du pool de `+100 000` et `+200 000`, ce qui les placait
#: a `130000` et `230000+` -- **dans la plage d'entrainement**. L'entrainement part a `100 000`
#: et, a 229 parties par seconde pendant 7 200 secondes, consomme jusqu'a environ `1 749 000`.
#: La mesure contre deux aleatoires et celles contre les checkpoints auraient donc juge l'agent
#: sur des donnes qu'il avait vues, ce qui lui aurait donne un avantage qui n'est pas de
#: l'habilete -- et le chiffre aurait ete juste sur une population que sa phrase ne nomme pas.
#:
#: **Les SIX familles de plages de mesure sont desormais toutes sous 100 000**, la ou
#: l'entrainement ne va jamais. Six familles, **treize plages** : les checkpoints du pool en
#: comptent huit a eux seuls. Le compte annonce ici disait « quatre » et etait dementi par la
#: liste qui le suivait -- un compte n'est pas une liste de noms, et le defaut etait dans le
#: texte qui documentait la correction. Les noms, donc, et tous :
#:
#:   dimensionnement       20 000 -  21 999   (2 000 donnes)
#:   garde-fou             40 000 -  40 599   (600 donnes, les memes a chaque checkpoint)
#:   verdict               60 000 -  61 999   (2 000 donnes, un agent contre deux greedys)
#:   pool aleatoire        70 000 -  70 499   (500 donnes)
#:   pool checkpoints      80 000 + 1 000 x i (500 donnes chacune, HUIT plages)
#:   variante deterministe 90 000 -  91 999   (2 000 donnes)
#:
#: et, au-dessus de la barre et seule a y etre :
#:
#:   entrainement         100 000 +           (jamais en dessous)
#:
#: La disjonction est verifiee **au niveau des donnes et pas des seuls seeds** : l'audit a
#: hache les 14 600 pioches de mesure et les 1 486 336 pioches d'entrainement, et compte
#: **0 collision**.
DEPART_CAMPAGNE_FINALE = 60_000

#: Le decalage de la composition contre deux aleatoires.
DECALAGE_POOL_ALEATOIRE = 10_000

#: Le decalage du premier checkpoint, puis 1 000 par checkpoint suivant.
DECALAGE_POOL_CHECKPOINTS = 20_000
PAS_ENTRE_CHECKPOINTS = 1_000

#: Le decalage de la variante **deterministe** de l'agent. Rapportee a cote de la mesure de
#: reference, **jamais a sa place** -- exactement le statut du greedy a departage deterministe
#: en phase 2. L'indice d'une action de pose encode l'assignation, la position au banquet et
#: l'adversaire vise, donc une preference stable pour l'action la plus probable peut fabriquer
#: un artefact dans B2, B3 et B6. Son ecart avec la reference est un chiffre, pas un doublon.
DECALAGE_VARIANTE_DETERMINISTE = 30_000


@dataclass(frozen=True)
class Mesure:
    """Ce qu'une composition rend : son verdict, son dimensionnement, ses comportements.

    Attributes:
        intitule: la composition, en toutes lettres. Jamais deduite du contexte.
        verdict: gain moyen, part fractionnee, part stricte, gains par siege.
        dimensionnement: `sigma`, `rho`, effet de plan **remesures sur cette composition**.
        comportements: les dix-sept compteurs, aux deux grains.
        nb_donnes: le nombre de donnes.
        nb_parties: le nombre de parties. `nb_donnes x 3`.
        campagne: les parties brutes.

    **La campagne brute est gardee**, et ce n'est pas un oubli de nettoyage : c'est le
    **support** de tout ce qui precede. Sans elle, « la somme des gains vaut-elle zero dans
    chaque partie ? » et « chaque siege est-il occupe une fois par donne ? » ne sont plus des
    questions verifiables -- il ne reste que des agregats qui se confirment eux-memes. La
    phase 2 liberait ses campagnes pour tenir en memoire ; a 6 000 parties ce n'est pas
    necessaire, et l'auditabilite vaut mieux.
    """

    intitule: str
    verdict: phase3.Verdict
    dimensionnement: phase3.Dimensionnement
    comportements: dict[str, comp.Compte]
    nb_donnes: int
    nb_parties: int
    campagne: phase3.Campagne


def groupes_pour_m4(campagne: phase3.Campagne) -> list[phase2.Groupe]:
    """Traduit une campagne de la phase 3 en `Groupe` de la phase 2, pour `mesurer_m4`.

    **Une traduction, pas une reimplementation.** Les compteurs de la phase 2 prennent des
    `Groupe`, et ce sont eux qu'il faut faire tourner : ils sont audites, et trois tours d'audit
    ont porte sur leurs denominateurs.

    Le seul point delicat est le **grain** : `Groupe.sieges_mesures` porte, pour chaque trace,
    le **tuple** des sieges comptes. Ma campagne compte **un** siege par partie, donc chaque
    trace donne `(siege,)` -- un tuple d'un element, pas l'entier. Un entier passerait
    silencieusement dans `tous_les_comportements` et compterait autre chose.
    """
    return [
        phase2.Groupe(
            seed=donne,
            traces=traces,
            sieges_mesures=tuple((siege,) for siege in sieges),
        )
        for donne, traces, sieges in zip(
            campagne.donnes, campagne.traces, campagne.sieges_mesures, strict=True
        )
    ]


def mesurer(
    agent: phase3.Fabrique,
    adversaire: phase3.Fabrique,
    donnes: int,
    intitule: str,
    depart: int,
    decalage_agent: int = phase3.DECALAGE_AGENT,
    decalage_adversaire: int = phase3.DECALAGE_DEPARTAGE,
) -> Mesure:
    """Joue une composition, la juge, la dimensionne et compte ses comportements.

    `sigma` et `rho` sont **remesures ici**, sur la composition reelle. Ceux de la
    pre-inscription sont mesures sous l'hypothese nulle et n'ont aucune raison de valoir sous
    un agent different : l'ecart entre le SUPPOSE et le MESURE doit etre un chiffre, pas un
    oubli.
    """
    campagne = phase3.jouer_composition(
        agent=agent,
        adversaire=adversaire,
        donnes=donnes,
        intitule=intitule,
        depart=depart,
        decalage_agent=decalage_agent,
        decalage_adversaire=decalage_adversaire,
    )
    comportements = phase2.mesurer_m4(groupes_pour_m4(campagne))
    comp.verifier_inclusion_b1(comportements)
    return Mesure(
        intitule=intitule,
        verdict=phase3.juger(campagne),
        dimensionnement=phase3.dimensionner(campagne),
        comportements=comportements,
        nb_donnes=len(campagne.donnes),
        nb_parties=campagne.nb_parties,
        campagne=campagne,
    )


def ligne_de_base_trois_greedys_un_siege(donnes: int) -> dict[str, comp.Compte]:
    """La troisieme population de la phase 2, **regeneree a UN seul siege compte**.

    **Memes seeds, meme composition, meme decalage de graine.** Seuls les sieges COMPTES
    changent : `campagne_b(nb_greedys=3)` mesure les trois, et cette fonction n'en compte qu'un
    par partie -- celui qui tourne, donc les trois sont couverts a parts egales sur une donne.

    C'est la ligne de base de ma composition au grain de ma composition, et il n'y en a pas
    d'autre dans le depot.

    Raises:
        ValueError: si l'inclusion `B1-collectif >= B1-motif` tombe, sur l'un des deux grains.
            La chute de cette inclusion a deja revele un compteur faux une fois.
    """
    groupes = phase2.campagne_b(donnes, nb_greedys=3)
    reduits = [
        phase2.Groupe(
            seed=groupe.seed,
            traces=groupe.traces,
            # `campagne_b(nb_greedys=3)` rend `(0, 1, 2)` pour chaque trace. On garde le siege
            # dont l'indice est celui du replicat : la trace 0 compte le siege 0, la trace 1 le
            # siege 1, la trace 2 le siege 2. Chaque siege est donc compte exactement une fois
            # par donne, comme dans la composition de la phase 3.
            sieges_mesures=tuple(
                (replicat,) for replicat in range(len(groupe.traces))
            ),
        )
        for groupe in groupes
    ]
    comptes = phase2.mesurer_m4(reduits)
    comp.verifier_inclusion_b1(comptes)
    return comptes


@dataclass(frozen=True)
class Comparaison:
    """Un compteur, chez l'agent et chez sa ligne de base, avec ce que l'ecart vaut.

    Attributes:
        nom: le compteur.
        agent: son compte chez l'agent.
        base: son compte chez la ligne de base, **au meme grain**.
        ecart: `taux(agent) - taux(base)`, ou `None` si l'un des deux n'a pas de taux.
        detectable: l'ecart de taux detectable au budget de la campagne, calcule sur les
            **deux** effectifs -- voir `ecart_detectable_deux_echantillons`.
        separable: `True` separable, `False` non separable, **`None` = aucune regle n'a pu
            conclure**. Les trois etats sont distincts, et le troisieme n'est pas le second.
            L'audit du tour 2 a trouve l'inverse ici : `detectable is None` sur un taux
            degenere produisait `separable = False`, imprime « non separable a ce budget ».
            **C'est une conclusion, et elle n'avait pas ete calculee** -- sur les deux lignes
            que le rapport argumente en toutes lettres, et faussement : elles SONT separables,
            par la borne exacte de leur zero.
        regle: le nom de la regle qui a tranche -- voir `REGLES`. Publie a cote du verdict :
            deux lignes du meme tableau peuvent etre separees par deux regles differentes, et
            le lecteur doit savoir laquelle.
        borne_exacte: pour une ligne tranchee par `REGLE_BORNES_EXACTES`, la borne du cote
            degenere -- borne **haute** d'un zero, borne **basse** d'un cent. `None` sinon.
        separation: la `SeparationExacte` entiere de cette ligne, ou `None`. **Elle porte le
            COTE degenere, que `borne_exacte` seule ne dit pas** -- et c'est la reserve 2 de
            la phase 3 : le rendu ne recevait qu'un nombre, donc il ecrivait « le zero de la
            ligne de base » sur les quatre cas, y compris quand le degenere est du cote de
            l'agent, ou quand c'est un cent, ou quand les deux cotes le sont. Un rendu ne peut
            pas nommer ce qu'on ne lui donne pas ; le defaut etait dans le cablage, pas dans
            la phrase.
        parties_requises: pour une ligne **non separable**, le nombre de parties qu'il
            faudrait de chaque cote pour separer l'ecart observe. `None` sinon. C'est la
            regle « hors budget » de la pre-inscription, rendue lisible au lieu d'etre une
            branche que rien ne pouvait atteindre.
        exclu: la raison de l'exclusion, ou `None` si la ligne est comparee.
    """

    nom: str
    agent: comp.Compte
    base: comp.Compte
    ecart: float | None
    detectable: float | None
    separable: bool | None
    regle: str
    borne_exacte: float | None
    parties_requises: int | None
    exclu: str | None
    separation: "SeparationExacte | None" = None


#: Les compteurs exclus **par le texte de leur definition**, quel que soit le budget. Le critere
#: est : la definition nomme-t-elle un autre joueur ? `B1-collectif` oui, ces deux-la non, et
#: leurs taux bougent sous une autre composition pour une raison qui n'est pas l'habilete.
EXCLUS_PAR_LE_TEXTE: tuple[str, ...] = ("B4-tout-dos", "B5-renfort")


#: Les trois regles qui peuvent trancher une ligne, et leurs noms publies.
#:
#: **Il y en a trois parce qu'une seule ne suffit pas, et le tour 2 l'a paye.** La regle
#: normale ne sait pas traiter un taux degenere -- variance binomiale nulle, donc « tout est
#: detectable », ce qui est exactement faux --, et `ecart_detectable_deux_echantillons` rend
#: `None` pour cette raison. Ce `None` etait ensuite imprime « non separable a ce budget »,
#: qui est une **conclusion** que rien n'avait calculee. Il faut donc que le verdict porte le
#: nom de la regle qui l'a rendu : sans lui, deux verdicts identiques peuvent venir de deux
#: raisonnements differents, et l'un des deux peut etre l'absence de raisonnement.
REGLE_DETECTABLE = "detectable a deux echantillons"
REGLE_BORNES_EXACTES = "bornes exactes -- un taux degenere"
REGLE_EXCLUE = "exclue avant comparaison"
REGLE_AUCUNE = "AUCUNE -- non conclu"
REGLES: tuple[str, ...] = (
    REGLE_DETECTABLE,
    REGLE_BORNES_EXACTES,
    REGLE_EXCLUE,
    REGLE_AUCUNE,
)


def borne_haute_exacte_d_un_zero(total: int, risque: float = dim.RISQUE) -> float:
    """La borne haute exacte du taux vrai quand on a observe **zero succes sur `total`**.

    C'est la borne de Clopper-Pearson, et dans ce cas degenere elle s'ecrit en une ligne :
    la probabilite de n'observer aucun succes sur `total` tirages independants de taux `p`
    vaut `(1 - p)**total`, et la borne est le `p` qui rend cette probabilite egale au risque.
    D'ou `1 - risque**(1/total)`. **Aucune approximation normale**, ce qui est exactement le
    point : c'est parce que l'approximation normale s'effondre sur un zero que cette
    fonction existe.

    Sur les deux zeros de la ligne de base de la phase 3, a 99 % : `0/1967` donne **0,2338 %**
    et `0/10382` donne **0,0443 %**. L'agent y vaut 35,87 % et 3,66 %. Les deux lignes sont
    donc separables **de tres loin**, et le tableau du tour 2 les declarait « non separables ».

    Raises:
        ValueError: si `total` n'est pas strictement positif, ou si `risque` n'est pas dans
            `]0 ; 1[`. Un zero sur zero observation n'est pas un zero : c'est une absence, et
            elle n'a pas de borne.
    """
    if total <= 0:
        raise ValueError(
            f"borne_haute_exacte_d_un_zero demande un effectif strictement positif : "
            f"total={total}. Zero succes sur zero occasion n'est pas un taux nul, c'est une "
            f"absence d'occasion, et elle ne se borne pas."
        )
    if not 0.0 < risque < 1.0:
        raise ValueError(f"le risque doit etre dans ]0 ; 1[ : risque={risque}")
    return 1.0 - risque ** (1.0 / total)


def borne_basse_exacte_d_un_cent(total: int, risque: float = dim.RISQUE) -> float:
    """La borne basse exacte du taux vrai quand on a observe **`total` succes sur `total`**.

    Le symetrique exact de `borne_haute_exacte_d_un_zero`, et elle existe pour la meme raison :
    le tableau de la phase 3 ne porte aucun taux a 100 %, mais `ecart_detectable_deux_echantillons`
    rend `None` sur ce cas comme sur l'autre, et une phase suivante qui en produirait un
    retomberait sur le defaut qu'on vient de corriger. La regle est ecrite pour les deux bouts.

    Raises:
        ValueError: aux memes conditions que sa symetrique.
    """
    if total <= 0:
        raise ValueError(
            f"borne_basse_exacte_d_un_cent demande un effectif strictement positif : "
            f"total={total}"
        )
    if not 0.0 < risque < 1.0:
        raise ValueError(f"le risque doit etre dans ]0 ; 1[ : risque={risque}")
    return risque ** (1.0 / total)


@dataclass(frozen=True)
class SeparationExacte:
    """Ce qu'un taux degenere permet de conclure, et par quels deux nombres.

    Attributes:
        cote: « agent » ou « ligne de base » -- lequel des deux porte le taux degenere.
        borne: la borne exacte de ce cote (haute pour un zero, basse pour un cent).
        borne_de_l_autre: la borne de l'intervalle de l'autre cote qui lui fait face --
            **sa borne basse** si le degenere est un zero, sa borne haute si c'est un cent.
        disjoints: les deux bornes se croisent-elles ? Si non, l'ecart est etabli.
    """

    cote: str
    borne: float
    borne_de_l_autre: float
    disjoints: bool


def separer_un_taux_degenere(
    agent: comp.Compte, base: comp.Compte, risque: float = dim.RISQUE
) -> SeparationExacte | None:
    """Trancher une ligne dont **exactement un** des deux cotes vaut 0 % ou 100 %.

    **La docstring de `ecart_detectable_deux_echantillons` prescrivait ce traitement depuis le
    tour 2 -- « un zero observe se traite par sa borne exacte » -- et personne ne le calculait.**
    Une prescription qu'aucun code n'exerce est du meme genre que la branche « hors budget » du
    defaut 6 : elle fait croire qu'un traitement s'applique.

    La regle, en deux bornes qui ne se rencontrent pas
    --------------------------------------------------
    Le cote degenere recoit sa borne de Clopper-Pearson **unilaterale** au risque `risque` --
    1 % dans toute la queue qui compte. L'autre recoit la borne de son intervalle normal
    **bilateral** au meme `risque`, donc 0,5 % dans la queue qui regarde vers le degenere. Si
    les deux ne se croisent pas, l'ecart est etabli.

    **Les deux queues ne valent donc pas le meme nombre, et c'est dit plutot que lisse** : le
    cote normal est traite plus severement que le cote exact. Ecrire « au meme risque » aurait
    ete faux d'un facteur deux sur une des deux queues. Cela va dans le sens du conservatisme,
    et le total reste borne par 1,5 %.

    **Deux intervalles qui ne se recouvrent pas donnent un test plus severe que leur risque
    nominal, pas plus lache** : c'est le sens de la lecture par recouvrement, et c'est
    justement pourquoi le paragraphe 4 refuse de l'employer sur des ecarts APPARIES, ou elle
    ignore la correlation et perd de la puissance. Ici les deux cotes sont independants et la
    marge est enorme -- 35,87 % contre 0,2338 % --, donc le conservatisme ne coute rien. C'est
    une regle differente de celle du reste du tableau, et elle est **publiee sous son nom**
    pour cela : `REGLE_BORNES_EXACTES`.

    Les quatre cas, parce qu'il y en a quatre et qu'en oublier un fait lever le rapport
    ----------------------------------------------------------------------------------------
    **Un seul** cote degenere : le cas ci-dessus, et le seul que la phase 3 rencontre.
    **Les deux, au meme bout** -- `0 %` contre `0 %` : l'ecart vaut exactement zero, il n'y a
    rien a etablir, et c'est une conclusion, pas une absence de conclusion. **Les deux, aux
    bouts opposes** -- `0 %` contre `100 %` : les deux bornes exactes sont disjointes par
    construction, et la ligne est separable. **Aucun** : cette regle ne s'applique pas.

    Le deuxieme cas merite d'etre nomme, parce que l'oublier coutait cher : `comparer` l'aurait
    rendu « non conclu », et le rendu du rapport **leve** sur une ligne non conclue. Une ligne
    parfaitement banale -- un comportement qu'aucun des deux joueurs ne manifeste jamais --
    aurait fait tomber la generation du rapport entier.

    Rend `None` si aucun cote n'est degenere, ou si un effectif est nul.
    """
    taux_agent, taux_base = agent.taux(), base.taux()
    if taux_agent is None or taux_base is None:
        return None
    agent_degenere = taux_agent <= 0.0 or taux_agent >= 1.0
    base_degenere = taux_base <= 0.0 or taux_base >= 1.0
    if not agent_degenere and not base_degenere:
        return None

    if agent_degenere and base_degenere:
        if taux_agent == taux_base:
            # Meme bout : l'ecart est exactement nul. Conclusion, et non absence de conclusion.
            borne = (
                borne_haute_exacte_d_un_zero(base.total, risque)
                if taux_base <= 0.0
                else borne_basse_exacte_d_un_cent(base.total, risque)
            )
            return SeparationExacte(
                cote="les deux", borne=borne, borne_de_l_autre=borne, disjoints=False
            )
        # Bouts opposes : les deux bornes exactes ne peuvent pas se croiser.
        zero, cent = (
            (agent, base) if taux_agent <= 0.0 else (base, agent)
        )
        haute = borne_haute_exacte_d_un_zero(zero.total, risque)
        basse = borne_basse_exacte_d_un_cent(cent.total, risque)
        return SeparationExacte(
            cote="les deux", borne=haute, borne_de_l_autre=basse, disjoints=basse > haute
        )

    if base_degenere:
        cote, degenere, autre = "ligne de base", base, agent
        taux_degenere, taux_autre = taux_base, taux_agent
    else:
        cote, degenere, autre = "agent", agent, base
        taux_degenere, taux_autre = taux_agent, taux_base

    demi = dim.quantile_bilateral(risque) * (
        taux_autre * (1 - taux_autre) / autre.total
    ) ** 0.5
    if taux_degenere <= 0.0:
        borne = borne_haute_exacte_d_un_zero(degenere.total, risque)
        borne_de_l_autre = taux_autre - demi
        disjoints = borne_de_l_autre > borne
    else:
        borne = borne_basse_exacte_d_un_cent(degenere.total, risque)
        borne_de_l_autre = taux_autre + demi
        disjoints = borne_de_l_autre < borne
    return SeparationExacte(
        cote=cote, borne=borne, borne_de_l_autre=borne_de_l_autre, disjoints=disjoints
    )


def ecart_detectable_deux_echantillons(
    agent: comp.Compte,
    nb_parties_agent: int,
    base: comp.Compte,
    nb_parties_base: int,
    budget: int,
) -> float | None:
    """L'ecart de taux detectable entre DEUX echantillons dont les effectifs different.

    **`phase2.ecart_de_taux_detectable` suppose deux echantillons de MEME effectif** -- son
    erreur-type vaut `sqrt(2 p (1-p) / effectif)`, ou le facteur 2 est celui d'une difference
    entre deux mesures de meme taille et de meme taux. C'est vrai des populations de la
    phase 2 ; c'est faux ici, et l'audit du tour 1 l'a chiffre. Les denominateurs d'action
    dependent de la politique : `B4-strict` compte **3 814** occasions chez l'agent contre
    **1 967** dans la ligne de base, et son detectable publie valait **2,37 pt** quand la vraie
    valeur est **3,96** -- une sous-estimation de 40 %. `B4-departage` 3,90 contre 4,52,
    `B4-contre-nature` 3,75 contre 2,65, `B4-meurtre-couteux` 1,01 contre 0,71, `B5-renfort`
    1,67 contre 1,56.

    **Deux des 34 lignes changent de statut, et cette phrase disait le contraire.** L'audit du
    tour 1 avait verifie « aucune » sur la formule ; l'audit du tour 2 a vu ce que la formule
    fait des deux zeros de la ligne de base. `B4-contre-nature` et `B4-meurtre-couteux` sortent
    de cette fonction avec `None` -- taux degenere --, et sortaient de `comparer` etiquetees
    « non separable a ce budget ». Elles sont separables, par `separer_un_taux_degenere` :
    35,87 % contre une borne haute exacte de 0,2338 %, et 3,66 % contre 0,0443 %.

    Les trois autres lignes aux effectifs inegaux ne changent pas de statut. Un chiffre publie
    faux se corrige meme quand il ne renverse rien -- c'est celui-la qu'une phase suivante
    citera --, mais **une conclusion publiee fausse se corrige d'abord**.

    La variance est donc celle d'une difference de deux binomiales independantes,
    `p_a q_a / n_a + p_b q_b / n_b`, chacune avec **son** taux et **son** effectif.

    `phase2.ecart_de_taux_detectable` n'est pas modifiee : elle porte les chiffres d'un
    livrable audite, et les deplacer deplacerait l'etalon de toutes les phases qui les citent.

    Rend `None` dans les memes deux cas qu'elle, et pour la meme raison : un effectif attendu
    sous 1, ou un taux exactement 0 ou 1 -- ou la variance binomiale est nulle, donc ou la
    formule normale rendrait « tout est detectable », ce qui est exactement faux.

    **Un zero observe se traite par sa borne exacte, et c'est `separer_un_taux_degenere` qui
    le fait.** Cette phrase etait ici des le tour 2, sans qu'aucun code ne l'exerce : la ligne
    repartait « non separable » faute de detectable. Une prescription qu'aucun appelant
    n'honore est du meme genre que la branche « hors budget » du defaut 6.
    """
    taux_agent, taux_base = agent.taux(), base.taux()
    if taux_agent is None or taux_base is None:
        return None
    effectif_agent = budget * phase2.observations_par_partie(agent, nb_parties_agent)
    effectif_base = budget * phase2.observations_par_partie(base, nb_parties_base)
    if effectif_agent < 1 or effectif_base < 1:
        return None
    if taux_agent <= 0.0 or taux_agent >= 1.0 or taux_base <= 0.0 or taux_base >= 1.0:
        return None
    variance = (
        taux_agent * (1 - taux_agent) / effectif_agent
        + taux_base * (1 - taux_base) / effectif_base
    )
    quantile = dim.quantile_bilateral(dim.RISQUE) + dim.quantile_de_puissance(dim.PUISSANCE)
    return quantile * variance**0.5


def parties_requises(
    agent: comp.Compte,
    nb_parties_agent: int,
    base: comp.Compte,
    nb_parties_base: int,
    ecart: float,
) -> int | None:
    """Combien de parties il faudrait, **de chaque cote**, pour separer l'ecart observe.

    **C'est ce que la regle « hors budget » de la pre-inscription voulait dire, et elle ne
    pouvait pas le dire.** Le paragraphe 9.2 annoncait que les huit lignes hors budget a
    6 000 parties ne seraient pas comparees, et les nommait ; mais `comparer` appelait
    `phase2.budget_d_un_compteur` avec `ecart=None`, donc `parties` valait `None`, donc
    `hors_budget` valait **toujours faux** et la branche qui excluait etait **inatteignable**.
    Verifie a un budget d'une seule partie : aucune ligne n'en sortait.

    Deux choses en decoulent, et il faut les separer.

    **Un.** La branche morte est retiree. Un critere qui ne peut pas se declencher est pire que
    pas de critere : il fait croire qu'un filtre s'exerce.

    **Deux.** Les huit noms de la pre-inscription etaient calcules sur l'ecart **greedy contre
    hasard** de la phase 2. Ce n'est pas l'ecart de cette phase, qui est **agent contre ligne
    de base** : la liste ne se transporte pas, et l'appliquer telle quelle aurait exclu des
    lignes sur la foi d'un ecart mesure sur une autre population -- la faute maison, encore.
    Le critere qui s'exerce reellement ici est `|ecart| > detectable`, qui est **le meme
    critere** exprime sur l'ecart effectivement mesure : `parties_requises(ecart) > budget`
    equivaut a `|ecart| < detectable`. Cette fonction le rend **lisible** au lieu de le laisser
    implicite, en publiant le nombre de parties que chaque ligne non separable demanderait.

    Rend `None` si l'ecart est nul ou si l'un des taux est degenere.
    """
    if ecart == 0:
        return None
    taux_agent, taux_base = agent.taux(), base.taux()
    if taux_agent is None or taux_base is None:
        return None
    if taux_agent <= 0.0 or taux_agent >= 1.0 or taux_base <= 0.0 or taux_base >= 1.0:
        return None
    par_partie_agent = phase2.observations_par_partie(agent, nb_parties_agent)
    par_partie_base = phase2.observations_par_partie(base, nb_parties_base)
    if par_partie_agent <= 0 or par_partie_base <= 0:
        return None
    quantile = dim.quantile_bilateral(dim.RISQUE) + dim.quantile_de_puissance(dim.PUISSANCE)
    # `n` parties de chaque cote donnent une variance
    # `p_a q_a / (n x u_a) + p_b q_b / (n x u_b)` : on resout en `n`.
    facteur = (
        taux_agent * (1 - taux_agent) / par_partie_agent
        + taux_base * (1 - taux_base) / par_partie_base
    )
    return max(1, math.ceil((quantile / ecart) ** 2 * facteur))


def comparer(
    agent: dict[str, comp.Compte],
    base: dict[str, comp.Compte],
    nb_parties_agent: int,
    nb_parties_base: int,
    budget: int,
) -> list[Comparaison]:
    """Compare deux jeux de compteurs **au meme grain**, ligne a ligne.

    `comp.ecart_de_taux` **leve** si les grains different : elle est appelee plutot que
    contournee, et une ligne dont le grain differe fait donc tomber la mesure au lieu de
    produire un nombre qu'il faudrait relire.

    Les exclusions sont **calculees**, jamais recopiees : le marqueur de budget vient de
    `phase2.budget_d_un_compteur` au budget reel de la campagne, et l'exclusion textuelle vient
    de la liste nommee ci-dessus.

    Le denominateur par partie n'est PAS re-verifie ici, et c'est delibere
    -----------------------------------------------------------------------
    Une premiere version de ce module ajoutait sa propre garde : « une ligne `-par-partie` doit
    valoir 1,0 observation par partie ». **Elle etait redondante.**
    `phase2.observations_par_partie` porte deja exactement ce controle et **leve**, avec un
    message plus precis -- « son denominateur EST le nombre de parties, or il vaut N contre M
    parties ». C'est la parade que l'audit du tour 2 de la phase 2 a imposee, apres qu'un
    facteur trois indu eut survecu a deux verifications reussies.

    Ecrire une seconde garde pour la meme regle est exactement ce que le paragraphe 2 des
    conventions interdit : deux definitions finissent par ne plus etre d'accord, et c'est la
    plus recente qui a tort sans que rien ne le signale. `budget_d_un_compteur`, appele
    ci-dessous, passe par `observations_par_partie` : le controle s'exerce, a son site unique.
    """
    resultats: list[Comparaison] = []
    for nom in sorted(set(agent) & set(base)):
        compte_agent, compte_base = agent[nom], base[nom]
        budget_agent = phase2.budget_d_un_compteur(
            compte_agent, nb_parties_agent, None, budget=budget
        )
        exclu: str | None = None
        if nom in EXCLUS_PAR_LE_TEXTE:
            exclu = "texte de la definition : elle ne nomme aucun autre joueur"
        elif budget_agent.aveugle_par_le_bas:
            exclu = f"aveugle par le bas a {budget} parties"

        # `ecart_de_taux` LEVE si les grains different. On ne l'attrape pas : un grain qui
        # differe est un defaut a corriger, pas une cellule a remplir.
        ecart = comp.ecart_de_taux(compte_agent, compte_base)
        detectable = ecart_detectable_deux_echantillons(
            compte_agent, nb_parties_agent, compte_base, nb_parties_base, budget
        )

        # **Une ligne sort d'ici avec le NOM de la regle qui l'a tranchee, ou avec l'aveu
        # qu'aucune ne l'a fait.** `separable = False` ne s'atteint que par un calcul qui a
        # conclu ; l'absence de calcul vaut `None`, et le rendu leve dessus.
        separable: bool | None
        borne_exacte: float | None = None
        separation: SeparationExacte | None = None
        if exclu is not None:
            separable, regle = None, REGLE_EXCLUE
        elif ecart is None:
            separable, regle = None, REGLE_AUCUNE
        elif detectable is not None:
            separable, regle = abs(ecart) > detectable, REGLE_DETECTABLE
        else:
            # `detectable is None` : la formule normale ne sait pas traiter cette ligne. Un
            # taux degenere se traite par sa borne exacte -- c'est ce que la docstring de
            # `ecart_detectable_deux_echantillons` prescrit depuis le tour 2, et ce que rien
            # ne faisait. Les autres causes de `None` -- un effectif attendu sous 1 -- n'ont
            # pas de regle de rechange, et la ligne repart NON CONCLUE.
            exacte = separer_un_taux_degenere(compte_agent, compte_base)
            if exacte is None:
                separable, regle = None, REGLE_AUCUNE
            else:
                separable, regle = exacte.disjoints, REGLE_BORNES_EXACTES
                borne_exacte = exacte.borne
                separation = exacte

        requises = (
            parties_requises(
                compte_agent, nb_parties_agent, compte_base, nb_parties_base, ecart
            )
            if separable is False and regle == REGLE_DETECTABLE and ecart is not None
            else None
        )
        resultats.append(
            Comparaison(
                nom=nom,
                agent=compte_agent,
                base=compte_base,
                ecart=ecart,
                detectable=detectable,
                separable=separable,
                regle=regle,
                borne_exacte=borne_exacte,
                parties_requises=requises,
                exclu=exclu,
                separation=separation,
            )
        )
    return resultats


def politique_de_checkpoint(chemin: str) -> phase3.Fabrique:
    """Une fabrique de politique a partir d'un checkpoint, pour les mesures contre le pool."""
    from agents import entrainement
    from agents.politique_reseau import charger, politique_reseau
    from courtisans.engine import Engine
    from courtisans.infoset import tenseur

    etat = Engine(entrainement.CONFIG).reset(0)
    modele = charger(
        chemin,
        taille_observation=len(tenseur(etat, 0)),
        nb_actions=6 * 2 * (entrainement.CONFIG.joueurs - 1),
    )
    return lambda alea: politique_reseau(modele, alea)


# ---------------------------------------------------------------------------------
# Le pilote de la mesure finale
# ---------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Joue toutes les compositions, compare les comportements, ecrit le rapport.

    **L'ordre compte, et il est celui de la pre-inscription.** Le juge d'abord -- un agent
    contre deux greedys --, le pool ensuite, la ligne de base regeneree enfin. Aucun seuil
    n'est relu apres avoir vu un chiffre.

    Reproduire :

        UV_LINK_MODE=copy uv run python -m mesure.phase3_mesure --donnes 2000
    """
    import argparse
    import json
    import sys
    import time
    from pathlib import Path

    from mesure import rapport_phase3

    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("--dossier", type=Path, default=Path("models/phase3"))
    analyseur.add_argument("--donnes", type=int, default=2000)
    analyseur.add_argument("--donnes-pool", type=int, default=500)
    analyseur.add_argument(
        "--sortie", type=Path, default=Path("mesure/resultats/phase3.md")
    )
    arguments = analyseur.parse_args(argv)

    reconfigurer = getattr(sys.stdout, "reconfigure", None)
    if reconfigurer is not None:
        reconfigurer(encoding="utf-8")

    final = arguments.dossier / "final.pt"
    if not final.exists():
        raise SystemExit(
            f"aucun agent entraine en {final} : lancer `agents.campagne` d'abord. "
            f"Mesurer un reseau non entraine rendrait un chiffre juste sur une population "
            f"qui n'est pas celle que la phase 3 annonce."
        )
    agent = politique_de_checkpoint(str(final))

    durees: list[tuple[str, float]] = []

    def chronometre(nom: str, action):  # noqa: ANN001, ANN202
        debut = time.perf_counter()
        resultat = action()
        durees.append((nom, time.perf_counter() - debut))
        print(f"  {nom} : {durees[-1][1]:.1f} s", flush=True)
        return resultat

    print("# Mesure de la phase 3", flush=True)

    # --- 1. Le juge, et lui seul -------------------------------------------------------
    contre_greedys = chronometre(
        "1 agent contre 2 greedys",
        lambda: mesurer(
            agent=agent,
            adversaire=phase3.greedy_de_reference,
            donnes=arguments.donnes,
            intitule="1 agent entraine contre 2 greedys, sieges permutes",
            depart=DEPART_CAMPAGNE_FINALE,
        ),
    )

    # --- 2. Le pool, chaque composition nommee -----------------------------------------
    pool: list[Mesure] = [contre_greedys]
    pool.append(
        chronometre(
            "1 agent contre 2 aleatoires",
            lambda: mesurer(
                agent=agent,
                adversaire=phase3.uniforme,
                donnes=arguments.donnes_pool,
                intitule=(
                    "1 agent entraine FINAL contre 2 aleatoires, 500 donnes, seeds 70000+ "
                    "(la composition du garde-fou, mesuree sur l'agent final)"
                ),
                depart=DEPART_CAMPAGNE_FINALE + DECALAGE_POOL_ALEATOIRE,
                decalage_adversaire=phase3.DECALAGE_UNIFORME,
            ),
        )
    )
    from agents.politique_reseau import charger, politique_reseau_deterministe
    from courtisans.engine import Engine
    from courtisans.infoset import tenseur

    etat_zero = Engine(phase3.CONFIG).reset(0)
    modele_final = charger(
        str(final),
        taille_observation=len(tenseur(etat_zero, 0)),
        nb_actions=6 * 2 * (phase3.CONFIG.joueurs - 1),
    )
    pool.append(
        chronometre(
            "1 agent DETERMINISTE contre 2 greedys",
            lambda: mesurer(
                agent=lambda _alea: politique_reseau_deterministe(modele_final),
                adversaire=phase3.greedy_de_reference,
                donnes=arguments.donnes,
                intitule=(
                    "1 agent entraine, variante DETERMINISTE, contre 2 greedys "
                    "(robustesse -- jamais a la place de la reference)"
                ),
                depart=DEPART_CAMPAGNE_FINALE + DECALAGE_VARIANTE_DETERMINISTE,
            ),
        )
    )

    checkpoints = sorted(arguments.dossier.glob("checkpoint_*.pt"))
    for indice, chemin in enumerate(checkpoints):
        fige = politique_de_checkpoint(str(chemin))
        pool.append(
            chronometre(
                f"1 agent contre 2 x {chemin.name}",
                lambda fige=fige, chemin=chemin, indice=indice: mesurer(
                    agent=agent,
                    adversaire=fige,
                    donnes=arguments.donnes_pool,
                    intitule=f"1 agent entraine contre 2 copies de `{chemin.name}`",
                    depart=(
                        DEPART_CAMPAGNE_FINALE
                        + DECALAGE_POOL_CHECKPOINTS
                        + PAS_ENTRE_CHECKPOINTS * indice
                    ),
                ),
            )
        )

    # --- 3. La ligne de base regeneree, a UN seul siege compte -------------------------
    base = chronometre(
        "ligne de base : 3 greedys, 1 siege compte",
        lambda: ligne_de_base_trois_greedys_un_siege(arguments.donnes),
    )
    comparaisons = comparer(
        contre_greedys.comportements,
        base,
        nb_parties_agent=contre_greedys.nb_parties,
        nb_parties_base=arguments.donnes * phase3.CONFIG.joueurs,
        budget=contre_greedys.nb_parties,
    )

    # --- 4. Le journal du run, complete de sa serie par donne ---------------------------
    #
    # `completer` rejoue l'evaluation du garde-fou de chaque checkpoint pour retrouver la part
    # fractionnee **donne par donne**, et LEVE si les nombres deja journalises ne sont pas
    # reproduits a l'identique. Ce n'est donc pas une nouvelle mesure : c'est la meme, dont on
    # garde de quoi calculer un ECART APPARIE. Sans elle, la section 4 ne pourrait publier que
    # des niveaux -- et c'est en lisant des niveaux comme des ecarts que le premier tour a
    # conclu « il progressait encore au dernier ».
    from agents import campagne as campagne_module
    from mesure import phase3_courbe

    journal = arguments.dossier / "journal.jsonl"
    jalons = (
        chronometre(
            "courbe : serie par donne des checkpoints",
            lambda: phase3_courbe.completer(
                arguments.dossier, campagne_module.DONNES_GARDE_FOU
            ),
        )
        if journal.exists()
        else []
    )

    # --- 5. L'audit, joue SUR le resultat mais ecrit AVANT lui ------------------------
    from mesure import phase3_audit

    controles = chronometre(
        "auto-audit",
        lambda: phase3_audit.auditer(
            mesure=contre_greedys,
            campagne=contre_greedys.campagne,
            pool=pool,
            comparaisons=comparaisons,
            base=base,
            nb_parties_base=arguments.donnes * phase3.CONFIG.joueurs,
            donnes_calibration=arguments.donnes,
            donnes_pool=arguments.donnes_pool,
            nb_checkpoints=len(checkpoints),
            parties_entrainement=(jalons[-1]["parties"] if jalons else 0),
            # La composition du garde-fou est publiee au paragraphe 4 mais n'est pas dans le
            # pool : sans elle, R2 ne voyait pas qu'elle portait le meme nom qu'une ligne du
            # pool. Le nom vient de son site unique, il n'est pas recopie.
            intitules_hors_pool=[campagne_module.intitule_du_garde_fou()],
        ),
    )
    for controle in controles:
        if not controle.passe:
            print(f"  !! CONTROLE EN ECHEC -- {controle.code} {controle.intitule}", flush=True)

    # --- 6. Les durees, ACCUMULEES sur les passes ------------------------------------
    #
    # Le paragraphe 0.2 exige au moins TROIS passes avec leur etendue. Une passe unique ne se
    # cite pas -- c'est le cinquieme defaut mineur que j'ai releve dans le rapport de la
    # phase 2, et le repeter dans le mien serait la faute que ce projet nomme le plus souvent :
    # la correction est le lieu du defaut suivant.
    #
    # Chaque passe ajoute une ligne au journal des durees ; le rapport lit **toutes** les
    # lignes et publie l'etendue. Trois lancements de cette commande suffisent donc, sans
    # qu'aucun chiffre ne soit recopie a la main.
    chemin_durees = arguments.dossier / "durees.jsonl"
    with chemin_durees.open("a", encoding="utf-8") as fichier:
        fichier.write(json.dumps(dict(durees), ensure_ascii=False) + "\n")
    passes = [
        json.loads(x)
        for x in chemin_durees.read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]

    texte = rapport_phase3.rapport(contre_greedys, pool, comparaisons, jalons, controles)
    texte += rapport_phase3.section_durees(passes)
    rapport_phase3.ecrire(texte, arguments.sortie)
    print(f"# Rapport ecrit en {arguments.sortie}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DECALAGE_POOL_ALEATOIRE",
    "DECALAGE_POOL_CHECKPOINTS",
    "DECALAGE_VARIANTE_DETERMINISTE",
    "DEPART_CAMPAGNE_FINALE",
    "PAS_ENTRE_CHECKPOINTS",
    "EXCLUS_PAR_LE_TEXTE",
    "Comparaison",
    "Mesure",
    "comparer",
    "groupes_pour_m4",
    "ligne_de_base_trois_greedys_un_siege",
    "main",
    "mesurer",
    "politique_de_checkpoint",
]
