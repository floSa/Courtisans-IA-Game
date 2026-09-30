"""Le rapport de la phase 3. **Ecrit en UTF-8 depuis Python, jamais par une redirection.**

C'est le defaut mineur 2 de la phase 2, ferme au debut de celle-ci : le rapport de la phase 2
partait sur la sortie standard et c'est la console qui decidait de son encodage. Ce
generateur-ci ecrit son fichier lui-meme, avec `encoding="utf-8"` explicite. Il ne peut pas
naitre en cp1252.

Aucune interpretation : chaque chiffre porte sa decomposition, sa composition et son
denominateur. Les seuils rappeles sont ceux de `mesure/phase3_hypothese_et_instrument.md`,
commite **avant** l'entrainement.
"""

from __future__ import annotations

import pathlib
from collections.abc import Sequence

from mesure import phase3, phase3_mesure


def _pct(valeur: float | None) -> str:
    return "-" if valeur is None else f"{valeur * 100:.2f} %"


def _pt(valeur: float | None) -> str:
    return "-" if valeur is None else f"{valeur * 100:+.2f} pt"


#: La lateralite de la borne de Clopper-Pearson, ecrite **une fois** et jamais sous-entendue.
#:
#: **Reserve 1 de la phase 3.** Le rapport ecrivait « borne haute a 99 % » quatre fois pour une
#: borne **unilaterale** prise au risque 1 %. Un lecteur qui recalcule lit « 99 % » comme un
#: intervalle bilateral, dont la queue vaut 0,5 %, et il trouve **0,2690 %** (0/1967) et
#: **0,0510 %** (0/10382) la ou le document publie 0,2338 % et 0,0443 %.
#:
#: **Aucune conclusion ne change** -- l'agent vaut 35,87 % et 3,66 %, il est au-dela des deux
#: lectures --, mais un chiffre juste sous une etiquette fausse est exactement la faute que ce
#: projet passe son temps a chasser : un nombre exact sur une population que sa phrase ne
#: nomme pas.
LATERALITE_EXACTE = "unilaterale au risque 1 % (Clopper-Pearson)"


def _phrase_de_borne_exacte(comparaison) -> str:
    """La phrase d'un verdict par bornes exactes -- **les quatre cas, pas un seul.**

    **Reserve 2 de la phase 3.** Cette phrase etait ecrite en dur pour le seul cas que la
    phase 3 rencontre : « le zero **de la ligne de base** ». Trois des quatre cas en sortaient
    faux, et aucun n'etait faux *aujourd'hui* -- ils l'auraient ete a la premiere phase qui en
    produit un :

    - un zero du cote de l'**agent** aurait ete attribue a la ligne de base ;
    - un taux a **100 %** aurait ete annonce « le zero », avec une « borne haute » quand c'est
      une borne basse ;
    - **deux** cotes degeneres auraient fait parler d'un « intervalle de l'autre cote » qui
      n'existe pas.

    Le rendu ne pouvait pas faire mieux : `Comparaison` ne lui passait qu'un nombre. Le defaut
    vivait dans le cablage, et c'est la que la parade est posee -- voir `Comparaison.separation`.
    """
    separation = getattr(comparaison, "separation", None)
    borne = _borne(comparaison.borne_exacte)
    taux_agent = comparaison.agent.taux()
    taux_base = comparaison.base.taux()

    def _degenere(taux) -> bool:
        return taux is not None and (taux <= 0.0 or taux >= 1.0)

    if separation is not None and separation.cote == "les deux":
        if taux_agent == taux_base:
            return (
                f"**non separable** -- les deux cotes valent {_pct(taux_agent)} : l'ecart est "
                f"exactement nul, et c'est une conclusion, pas une absence de conclusion"
            )
        return (
            f"**separable** -- par bornes exactes : les deux cotes sont degeneres a des bouts "
            f"opposes ({_pct(taux_agent)} contre {_pct(taux_base)}), et leurs bornes exactes "
            f"{LATERALITE_EXACTE} ne peuvent pas se croiser"
        )

    if separation is not None:
        cote = separation.cote
        taux_du_cote = taux_agent if cote == "agent" else taux_base
        taux_de_l_autre = taux_base if cote == "agent" else taux_agent
    else:  # pragma: no cover -- une ligne exacte porte toujours sa separation
        cote = "ligne de base" if _degenere(taux_base) else "agent"
        taux_du_cote = taux_base if cote == "ligne de base" else taux_agent
        taux_de_l_autre = taux_agent if cote == "ligne de base" else taux_base

    zero = taux_du_cote is not None and taux_du_cote <= 0.0
    cote = "l'agent" if cote == "agent" else "la ligne de base"
    quoi = "le zero" if zero else "le cent pour cent"
    sens = "borne haute" if zero else "borne basse"
    ou = "en deca" if zero else "au-dela"
    if comparaison.separable:
        return (
            f"**separable** -- par bornes exactes : {quoi} de {cote} a pour {sens} exacte "
            f"{LATERALITE_EXACTE} **{borne}**, et l'autre cote vaut "
            f"{_pct(taux_de_l_autre)}"
        )
    return (
        f"non separable -- {sens} exacte {LATERALITE_EXACTE} de {quoi} de {cote}, {borne}, "
        f"croise l'intervalle de l'autre cote, qui reste {ou}"
    )


def _borne(valeur: float | None) -> str:
    """Une borne exacte, a QUATRE decimales. Deux ne suffisent pas ici.

    `0,0443 %` s'arrondit en `0,04 %` au format ordinaire, et un lecteur y lit un zero
    arrondi -- exactement ce que la borne sert a exclure. Une borne dont la lecture depend de
    son arrondi ne borne rien.
    """
    return "-" if valeur is None else f"{valeur * 100:.4f} %"


def _titre(texte: str) -> str:
    return f"\n## {texte}\n"


def section_juge(lignes: list[str], mesure: phase3_mesure.Mesure) -> None:
    """Le juge du protocole : gain moyen, borne basse de l'IC 99 %, part fractionnee a cote."""
    verdict = mesure.verdict
    basse, haute = verdict.gain.intervalle
    lignes.append(_titre("1. Le juge -- gain moyen contre deux greedys"))
    lignes += [
        f"**Composition : {mesure.intitule}.** {mesure.nb_donnes} donnes x "
        f"{phase3.CONFIG.joueurs} sieges = **{mesure.nb_parties} parties**. Bootstrap **par "
        f"donne**, {phase3.RECHANTILLONS} rechantillons.",
        "",
        "**Le niveau nul du gain moyen est exactement 0,0000**, et il n'est pas estime : sous "
        "l'hypothese nulle, l'esperance du gain mesure vaut 0 par la somme nulle du paragraphe "
        "5.2 et par la permutation systematique des sieges. Voir le paragraphe 1 de la "
        "pre-inscription.",
        "",
        "| Grandeur | Valeur | Niveau nul |",
        "|---|---:|---:|",
        f"| **Gain moyen** | **{verdict.gain.moyenne:+.4f}** | **0,0000** (exact) |",
        f"| IC 99 % bootstrap par donne | [{basse:+.4f} ; {haute:+.4f}] | |",
        f"| Part de victoire fractionnee | {_pct(verdict.part_fractionnee.moyenne)} | "
        f"{_pct(verdict.part_neutre)} (exact) |",
        f"| Part de victoire stricte | {_pct(verdict.part_stricte)} | "
        f"**inconnu d'avance -- jamais un seuil** |",
        "",
        f"**Seuil du protocole : la borne basse de l'IC 99 % est-elle strictement positive ?** "
        f"Elle vaut **{basse:+.4f}**. "
        + (
            "**OUI -- l'agent bat le greedy.**"
            if verdict.bat_le_greedy
            else (
                "**NON.** "
                + (
                    "L'IC contient 0 : **non conclu a ce budget**. Ce n'est pas « l'agent ne "
                    "bat pas le greedy »."
                    if haute > 0
                    else "La borne haute est negative : **l'agent est battu par le greedy**."
                )
            )
        ),
        "",
        "### Le gain par siege -- a cote de la moyenne, jamais a sa place",
        "",
        "**L'avantage de siege est massif dans cette composition** : contraste apparie entre "
        "sieges extremes **+0,5735**, IC 99 % [+0,5218 ; +0,6240], mesure sur la population de "
        "l'hypothese nulle. Un chiffre d'un seul siege ne se compare **jamais** a un chiffre "
        "agrege sur trois.",
        "",
        "| Siege occupe | Gain moyen de l'agent |",
        "|---|---:|",
    ]
    for siege, gain in sorted(verdict.gains_par_siege.items()):
        lignes.append(f"| siege {siege} | {gain:+.4f} |")
    somme = sum(verdict.gains_par_siege.values())
    lignes += [
        "",
        f"Somme des trois : **{somme:+.4f}**, soit **trois fois le gain moyen** "
        f"({verdict.gain.moyenne:+.4f} x 3 = {verdict.gain.moyenne * 3:+.4f}).",
        "",
        "> **Ce n'est PAS un controle de nullite, et une premiere redaction de ce rapport le "
        "presentait comme tel.** Elle ecrivait « elle n'est nulle qu'a la precision "
        "d'echantillonnage », ce qui n'est vrai que **sous l'hypothese nulle**. Chaque siege "
        "portant le meme nombre de parties, la somme des trois moyennes vaut `3 x moyenne` "
        "**par identite arithmetique**, quel que soit l'agent : elle ne vaut zero que si le "
        "gain moyen vaut zero. Ce qui est nul par construction, c'est la somme des gains des "
        "**trois sieges d'une meme partie** -- invariant I5 --, et c'est verifie au "
        "paragraphe 6, partie par partie.",
    ]


def section_dimensionnement(lignes: list[str], mesure: phase3_mesure.Mesure) -> None:
    """`sigma` et `rho` **remesures** sur la composition reelle, contre ceux du nul."""
    dim = mesure.dimensionnement
    basse, haute = mesure.verdict.gain.intervalle
    demi_largeur = (haute - basse) / 2
    detectable = dim.ecart_detectable(dim.nb_parties)
    rho = "-" if dim.rho is None else f"**{dim.rho:+.4f}**"
    effet = "-" if dim.effet_de_plan is None else f"**{dim.effet_de_plan:.4f}**"

    lignes.append(_titre("2. Le dimensionnement, remesure sur la composition reelle"))
    lignes += [
        "La pre-inscription mesure `sigma` et `rho` **sous l'hypothese nulle** -- le greedy mis "
        "a la place de l'agent. Un agent different a une distribution de gain differente : "
        "l'ecart entre le **SUPPOSE** de la pre-inscription et le **MESURE** ci-dessous est un "
        "chiffre, et non un oubli.",
        "",
        "| Grandeur | Pre-inscription (hypothese nulle) | Mesure ici |",
        "|---|---:|---:|",
        f"| `sigma(gain)` | 0,6494 | **{dim.sigma_gain:.4f}** |",
        f"| `rho` intra-donne | −0,1400 | {rho} |",
        f"| effet de plan (analyse de variance) | 0,7200 | {effet} |",
        f"| effet de plan (bootstrap) | 0,7223 | **{dim.gain.effet:.4f}** |",
        "",
        f"**Ecart de gain detectable a ce budget** : **{detectable:+.4f}** sur "
        f"{dim.nb_parties} parties, 99 % bilateral et 80 % de puissance. La pre-inscription "
        f"annoncait **+0,0243**.",
        "",
        f"**Demi-largeur de l'IC 99 % du gain** : **{demi_largeur:.4f}** sur "
        f"{dim.nb_parties} parties.",
        "",
        "> **LA REGLE PRE-INSCRITE PORTE SUR LA DEMI-LARGEUR, PAS SUR `sigma`, ET ELLE "
        "N'EST PAS FRANCHIE.** Le paragraphe 3 de la pre-inscription ecrit : « la "
        "**demi-largeur** reelle sera remesuree sur la campagne finale et publiee a cote de "
        "celle-ci ; si **elle** en differe de plus de 10 %, c'est que `sigma` a bouge et il "
        "faudra le dire ». Le declencheur est donc la demi-largeur.",
        ">",
        f"> Mesuree : **{demi_largeur:.4f}** contre **0,0183** pre-inscrits, au **meme budget "
        f"de 6 000 parties** -- soit **{(demi_largeur / 0.0183 - 1) * 100:+.1f} %**. "
        + (
            "**Elle sort de la marge de 10 %.**"
            if abs(demi_largeur / 0.0183 - 1) > 0.10
            else "**Elle reste dans la marge de 10 %, donc le declencheur pre-inscrit n'est "
            "pas franchi.**"
        ),
        ">",
        f"> **Et `sigma` a pourtant bouge de "
        f"{(dim.sigma_gain / 0.6494 - 1) * 100:+.1f} %** -- {dim.sigma_gain:.4f} contre "
        f"0,6494. Une premiere redaction de ce rapport declarait sur cette base « `sigma` a "
        f"bouge de plus de 10 % », en attribuant a la marge une grandeur qu'elle ne "
        f"surveillait pas ; l'audit l'a relevee, et le pilote avait propage l'erreur sans la "
        f"voir. Le fait reste vrai, c'est la regle citee qui etait la mauvaise.",
        ">",
        f"> **La regle etait aveugle au mouvement qu'elle pretendait detecter, et c'est le "
        f"resultat interessant.** Une demi-largeur ne depend pas de `sigma` seul mais de "
        f"`sigma x sqrt(effet de plan / n)`. Ici `sigma` a "
        + ("**chute**" if dim.sigma_gain < 0.6494 else "**monte**")
        + f" de {abs(dim.sigma_gain / 0.6494 - 1) * 100:.1f} % pendant que l'effet de plan "
        + ("**montait**" if dim.effet_de_plan > 0.7200 else "**baissait**")
        + f" de 0,7200 a {dim.effet_de_plan:.4f} : "
        f"`0,6494 x sqrt(0,7200)` = {0.6494 * 0.72 ** 0.5:.4f} contre "
        f"`{dim.sigma_gain:.4f} x sqrt({dim.effet_de_plan:.4f})` = "
        f"{dim.sigma_gain * dim.effet_de_plan ** 0.5:.4f}, soit "
        f"{(dim.sigma_gain * dim.effet_de_plan ** 0.5) / (0.6494 * 0.72 ** 0.5) * 100 - 100:+.1f} "
        f"%. **Les deux mouvements se compensent dans la demi-largeur.** Une regle de "
        f"surveillance posee sur un produit ne detecte pas le mouvement d'un seul de ses "
        f"facteurs : c'est `sigma` qu'il fallait surveiller, et la pre-inscription surveillait "
        f"le produit.",
        ">",
        f"> Les deux grandeurs sont donc publiees separement, et c'est la lecon : "
        f"`sigma` = **{dim.sigma_gain:.4f}** (pre-inscrit 0,6494), effet de plan = "
        f"**{dim.effet_de_plan:.4f}** (pre-inscrit 0,7200), demi-largeur = "
        f"**{demi_largeur:.4f}** (pre-inscrite 0,0183).",
    ]


def section_pool(lignes: list[str], mesures: Sequence[phase3_mesure.Mesure]) -> None:
    """Chaque membre du pool, **avec sa composition nommee**."""
    lignes.append(_titre("3. Le pool -- chaque composition, nommee"))
    lignes += [
        "**Aucune de ces lignes n'est le juge.** Le juge est le gain moyen contre deux greedys, "
        "et lui seul. Les autres compositions repondent a d'autres questions.",
        "",
        "| Composition | Parties | Gain moyen | IC 99 % | Part fractionnee | Neutre |",
        "|---|---:|---:|---|---:|---:|",
    ]
    for mesure in mesures:
        basse, haute = mesure.verdict.gain.intervalle
        lignes.append(
            f"| {mesure.intitule} | {mesure.nb_parties} | "
            f"{mesure.verdict.gain.moyenne:+.4f} | [{basse:+.4f} ; {haute:+.4f}] | "
            f"{_pct(mesure.verdict.part_fractionnee.moyenne)} | "
            f"{_pct(mesure.verdict.part_neutre)} |"
        )
    contre_checkpoints = [m for m in mesures if "copies de" in m.intitule]
    lignes += ["", "### Ce que ces lignes disent, et ce qu'elles ne disent pas", ""]
    if contre_checkpoints:
        premier = contre_checkpoints[0]
        dernier = contre_checkpoints[-1]
        basse_d, haute_d = dernier.verdict.gain.intervalle
        lignes += [
            "La pre-inscription annonce, au paragraphe 6, que **« un agent qui ecrase ses "
            "propres checkpoints mais ne bat pas le greedy est le symptome exact de "
            "l'effondrement de convention en self-play »**. C'est la contrepartie assumee "
            "d'avoir sorti le greedy du pool d'entrainement.",
            "",
            "**Confrontee aux chiffres, cette phrase ne s'applique qu'a moitie, et il faut le "
            "dire plutot que de la laisser conclure a notre place.**",
            "",
            f"- l'agent bat son **premier** checkpoint de **{premier.verdict.gain.moyenne:+.4f}** "
            f"-- un ecart reel, mais sur un adversaire vieux de quinze minutes ;",
            f"- il bat son **dernier** de **{dernier.verdict.gain.moyenne:+.4f}**, IC 99 % "
            f"[{basse_d:+.4f} ; {haute_d:+.4f}]"
            + (
                ", **qui contient zero** : sur les quinze dernieres minutes, l'amelioration "
                "contre lui-meme n'est **pas etablie** a ce budget."
                if basse_d <= 0.0 <= haute_d
                else " : l'amelioration contre lui-meme est etablie."
            ),
            "",
            "**« Ecraser » ne decrit donc pas ce qui est mesure.** La marge sur un checkpoint "
            "decroit a mesure que le checkpoint se rapproche de l'agent final, ce qui est "
            "attendu et ne prouve rien a soi seul : un checkpoint recent est un adversaire "
            "plus fort. Ce que ces lignes etablissent est plus etroit -- **l'agent a progresse "
            "contre lui-meme sur la duree du run**, et cette progression n'a pas suffi a "
            "atteindre le greedy.",
            "",
            "**Ce qu'elles n'etablissent PAS** : qu'une convention de self-play soit la cause. "
            "Une convention stable et un apprentissage inacheve produisent tous deux un agent "
            "qui bat ses anciennes versions sans battre un adversaire exterieur. **Rien ici ne "
            "separe les deux hypotheses**, et il faudrait pour cela une population que cette "
            "phase n'a pas mesuree -- par exemple un second agent entraine depuis une autre "
            "graine, qui n'aurait aucune raison de partager la convention du premier.",
        ]
    reference = next((m for m in mesures if "2 greedys, sieges permutes" in m.intitule), None)
    deterministe = next((m for m in mesures if "DETERMINISTE" in m.intitule), None)
    lignes += [
        "",
        "### La variante deterministe -- rapportee a cote, jamais a la place",
        "",
    ]
    if reference is not None and deterministe is not None:
        gain_reference = reference.verdict.gain.moyenne
        gain_deterministe = deterministe.verdict.gain.moyenne
        ecart = gain_deterministe - gain_reference
        basse, haute = reference.verdict.gain.intervalle
        demi = (haute - basse) / 2
        lignes += [
            "**Une mesure de consequence, et elle ne se lit qu'en juxtaposant les deux "
            "nombres** -- c'est la meme forme qu'en phase 2 pour le departage du greedy, et la "
            "meme raison : un renvoi vers une autre section ne se lit pas.",
            "",
            "| | |",
            "|---|---:|",
            f"| gain moyen, agent echantillonne (reference) | **{gain_reference:+.4f}** |",
            f"| gain moyen, agent deterministe | **{gain_deterministe:+.4f}** |",
            f"| ecart | **{ecart:+.4f}** |",
            f"| demi-largeur de l'IC 99 % de la reference | {demi:.4f} |",
            f"| l'ecart, en demi-largeurs | **{abs(ecart) / demi:.2f}** |",
            "",
            "**Autrement dit : prendre l'action la plus probable plutot que d'echantillonner "
            + (
                "ne deplace pas le gain de l'agent a ce budget.** L'entropie de sa politique "
                "est basse -- 0,34 au dernier checkpoint --, donc les deux departages tirent "
                "le plus souvent la meme action, et ce chiffre le confirme plutot que de le "
                "supposer."
                if abs(ecart) < demi
                else "deplace le gain de l'agent d'un ecart superieur a la demi-largeur de "
                "l'IC : les deux departages ne jouent pas la meme politique, et la reference "
                "reste celle qui est echantillonnee."
            ),
            "",
            "**Ce que ce chiffre n'etablit pas** : que la variante deterministe soit une bonne "
            "politique. Elle est **biaisee** -- l'indice d'une action de pose encode "
            "l'assignation, la position au banquet et l'adversaire vise --, et son seul usage "
            "est d'etre rapportee ici.",
        ]


def section_garde_fou(lignes: list[str], jalons: Sequence[dict]) -> None:
    """La courbe du garde-fou, **et l'intervalle de ses ECARTS**.

    **La section que l'audit a fait tomber.** Elle publiait huit intervalles sur huit niveaux
    et aucun sur les sept ecarts, puis concluait « croissance monotone sans exception, et
    l'agent progressait encore au dernier ». Les deux moities de cette phrase etaient des
    proprietes du tirage, pas de l'agent : aucun des sept pas n'atteint l'ecart detectable de
    2,75 points que la pre-inscription fixe elle-meme a ce budget, et une remesure sur les
    MEMES donnes avec un autre aleatoire porte deux inversions et un dernier pas negatif.

    Le paragraphe 0.2 du protocole en a tire une regle : *une courbe d'apprentissage se publie
    avec l'intervalle de ses ECARTS, pas seulement de ses niveaux.*
    """
    from agents import campagne as campagne_module
    from mesure import phase3_courbe

    risque = 0.01 / campagne_module.CHECKPOINTS_ATTENDUS
    lignes.append(_titre("4. Le garde-fou -- un agent contre deux aleatoires"))
    lignes += [
        "**Ce n'est pas un juge.** Depasser 86,52 % ne dit rien sur le fait de battre le "
        "greedy : le greedy y est deja. C'est un detecteur d'agent qui n'apprend pas.",
        "",
        "Le **86,52 %** est une **moyenne sur les trois sieges**, agregee sur les 10 002 "
        "parties de la campagne B de la phase 2, et il ne se compare qu'a une mesure agregee "
        "de la meme facon. La colonne ci-dessous l'est.",
        "",
        f"Composition : **{campagne_module.intitule_du_garde_fou()}**. "
        f"Chaque checkpoint : {phase3_mesure_donnes_garde_fou()} donnes x "
        f"{phase3.CONFIG.joueurs} sieges, **les memes donnes a chaque fois**. IC corrige de "
        f"**Bonferroni pour {campagne_module.CHECKPOINTS_ATTENDUS} regards**.",
        "",
        "### Les niveaux -- et ils ne decident de rien",
        "",
        "| # | s | Parties d'entrainement | Entropie | Part fractionnee | IC (Bonferroni) | "
        "Gain moyen |",
        "|---:|---:|---:|---:|---:|---|---:|",
    ]
    for jalon in jalons:
        lignes.append(
            f"| {jalon['numero']} | {jalon['secondes']:.0f} | {jalon['parties']} | "
            f"{jalon['entropie']:.4f} | {_pct(jalon['part_fractionnee'])} | "
            f"[{_pct(jalon['borne_basse'])} ; {_pct(jalon['borne_haute'])}] | "
            f"{jalon['gain_moyen']:+.4f} |"
        )
    if not jalons:
        return

    consecutifs = phase3_courbe.ecarts(jalons, 1, risque)
    portee = campagne_module.PORTEE_DU_GARDE_FOU
    de_portee = phase3_courbe.ecarts(jalons, portee, risque)
    extremes = phase3_courbe.ecart_des_extremes(jalons, risque)
    dernier, premier = jalons[-1], jalons[0]
    franchi = dernier["part_fractionnee"] > 0.8652
    recouvrements = sum(
        1
        for a, b in zip(jalons, jalons[1:], strict=False)
        if a["borne_haute"] >= b["borne_basse"] and b["borne_haute"] >= a["borne_basse"]
    )

    lignes += [
        "",
        "> **Huit intervalles de NIVEAU ne disent pas si l'agent progresse, et une premiere "
        "redaction de ce rapport a conclu comme s'ils le disaient.** Elle ecrivait « croissance "
        "monotone sans exception » et « il progressait encore au dernier ». **Les deux sont "
        "retirees.** La monotonie de cette colonne est une propriete de ce tirage : une "
        "remesure sur les **memes donnes** avec un autre aleatoire de politique porte deux "
        "inversions, dont le dernier pas. Ce qui decide est en dessous.",
        "",
        "### Les ecarts -- et ce sont eux qui decident",
        "",
        "**Bootstrap apparie par donne, memes donnes des deux cotes, meme correction de "
        "Bonferroni.** Un ecart apparie ne coute pas une partie de plus : les donnes du "
        "garde-fou sont les memes a chaque checkpoint, la pre-inscription l'avait prevu, il "
        "ne manquait que de garder la serie.",
        "",
        f"**Un ecart ne se lit pas au recouvrement de deux intervalles de niveau.** Ici "
        f"{recouvrements} des {len(jalons) - 1} couples consecutifs se recouvrent, alors que "
        f"l'ecart des extremes est etabli : le recouvrement ignore la correlation que "
        f"l'appariement rend forte.",
        "",
        "| Ecart apparie | Valeur | IC (Bonferroni) | Etabli ? |",
        "|---|---:|---|---|",
    ]
    for ecart in consecutifs:
        lignes.append(
            f"| ckpt {ecart.depuis} -> {ecart.vers} (portee 1) | {_pt(ecart.moyenne)} | "
            f"[{_pt(ecart.intervalle[0])} ; {_pt(ecart.intervalle[1])}] | "
            + ("**etabli**" if ecart.etabli else "non -- dans le bruit") + " |"
        )
    for ecart in de_portee:
        lignes.append(
            f"| ckpt {ecart.depuis} -> {ecart.vers} (portee {portee}) | {_pt(ecart.moyenne)} | "
            f"[{_pt(ecart.intervalle[0])} ; {_pt(ecart.intervalle[1])}] | "
            + ("**etabli**" if ecart.etabli else "non -- dans le bruit") + " |"
        )
    lignes.append(
        f"| **ckpt {extremes.depuis} -> {extremes.vers} (portee {extremes.portee})** | "
        f"**{_pt(extremes.moyenne)}** | "
        f"[{_pt(extremes.intervalle[0])} ; {_pt(extremes.intervalle[1])}] | "
        + ("**ETABLI**" if extremes.etabli else "non -- dans le bruit") + " |"
    )

    etablis = [e for e in consecutifs if e.etabli]
    # **Le declencheur du garde-fou, recalcule avec la regle courante.** `progres_etabli`, pas
    # `etabli` : un effondrement etabli n'est pas un progres, et la v5 les confondait.
    sans_progres = [e for e in de_portee if not e.progres_etabli]
    lignes += [
        "",
        f"**Ce qui est etabli : l'agent apprend.** Du premier au dernier checkpoint, "
        f"**{_pt(extremes.moyenne)}**, IC "
        f"[{_pt(extremes.intervalle[0])} ; {_pt(extremes.intervalle[1])}], qui **exclut 0**. "
        f"C'est la seule lecture de cette section qui tienne, et elle tient franchement.",
        "",
        f"**Ce qui n'est PAS etabli : qu'il progressait ENCORE a la fin.** "
        + ("Aucun des " if not etablis else f"{len(etablis)} des ")
        + f"{len(consecutifs)} pas consecutifs n'est etabli"
        + (f" ({', '.join(f'ckpt {e.depuis}->{e.vers}' for e in etablis)})" if etablis else "")
        + f", et le dernier -- ckpt {consecutifs[-1].depuis} -> {consecutifs[-1].vers} -- vaut "
        f"{_pt(consecutifs[-1].moyenne)}, IC "
        f"[{_pt(consecutifs[-1].intervalle[0])} ; {_pt(consecutifs[-1].intervalle[1])}], qui "
        f"**contient 0**. Un quart d'heure de progres vaut environ "
        f"{_pt((extremes.moyenne) / (len(jalons) - 1))}, quand la demi-largeur des IC apparies "
        f"ci-dessus va de "
        f"{_pt(min((e.intervalle[1] - e.intervalle[0]) / 2 for e in consecutifs))} a "
        f"{_pt(max((e.intervalle[1] - e.intervalle[0]) / 2 for e in consecutifs))} : "
        f"**ce budget ne peut pas trancher un pas isole**, et aucune redaction ne le lui fera "
        f"dire.",
        "",
        "> **La barre qui juge un ecart est la demi-largeur de SON PROPRE intervalle apparie, "
        "pas le 2,75 pt de la pre-inscription.** Ce 2,75 est un ecart detectable **iid sur un "
        "NIVEAU** a 1 800 parties ; les ecarts ci-dessus sont **apparies**, et leur precision "
        "reelle est celle que le bootstrap rend. Les deux mènent ici a la meme conclusion, mais "
        "les confondre serait comparer deux grandeurs qui ne portent pas sur la meme chose -- "
        "et une premiere redaction de ce paragraphe le faisait.",
        "",
        f"**Critere terminal du protocole** : au dernier checkpoint, la part fractionnee vaut "
        f"**{_pct(dernier['part_fractionnee'])}** contre **86,52 %**. "
        + ("**Franchi.**" if franchi else "**NON franchi.**"),
        "",
        f"**Declencheur du garde-fou** -- l'ecart apparie de portee {portee}, a partir du "
        f"checkpoint {campagne_module.PREMIER_CHECKPOINT_QUI_DECLENCHE} : "
        + (
            f"**declenche** -- {len(sans_progres)} ecart(s) de portee {portee} ne sont pas un "
            f"progres etabli : "
            + ", ".join(f"ckpt {e.depuis}->{e.vers}" for e in sans_progres)
            + "."
            if sans_progres
            else f"**non declenche** -- les {len(de_portee)} ecarts de portee {portee} sont "
            f"tous des progres etablis, intervalle entierement au-dessus de 0."
        ),
        "",
        "> **Ce verdict est RECALCULE ici, il n'est pas relu dans le journal.** Le champ "
        "`declenche` du `journal.jsonl` de ce run a ete ecrit **pendant** le run, donc par la "
        "regle en vigueur ce jour-la, qui a depuis ete retiree deux fois. Le tour 2 le relisait "
        "tel quel pendant que la phrase au-dessus decrivait la regle courante : les deux "
        "concordent sur ce run, et rien ne le garantissait. Un verdict se recalcule avec la "
        "regle qu'on publie, ou il ne se publie pas.",
        "",
        "> **Le critere terminal n'est pas franchi, et la raison que le protocole lui pretait "
        "etait fausse -- mais pas pour la raison que ce rapport donnait au premier tour.**",
        ">",
        "> Le protocole ecrivait : « si apres 2 h l'agent n'a pas depasse 86,52 %, on arrete : "
        "**l'agent n'apprend pas**, et rallonger ne dira rien de plus ». La premisse est "
        f"verifiable, et l'ecart des extremes la contredit : {_pt(extremes.moyenne)}, IC "
        f"[{_pt(extremes.intervalle[0])} ; {_pt(extremes.intervalle[1])}]. **L'agent apprend.**",
        ">",
        "> **Ce qui ne suit pas, et que la premiere redaction en tirait :** « il n'a pas fini "
        "d'apprendre », donc « rallonger le budget ». Cette conclusion demandait que la courbe "
        "montre encore une pente a la fin, et **aucun ecart mesure ici ne le montre**. Ce que "
        "cette section etablit s'arrete a : l'agent a appris entre le premier et le dernier "
        "checkpoint. Ce qu'il ferait d'un quart d'heure de plus n'est pas mesure.",
        ">",
        f"> Le garde-fou lui-meme a ete corrige une **quatrieme** fois sur cette section. Sa "
        f"version du 21/08/2026 se declenchait sur trois checkpoints consecutifs a intervalles "
        f"recouvrants -- or {recouvrements} des {len(jalons) - 1} couples se recouvrent ici, "
        f"donc elle aurait arrete ce run au **checkpoint 3, a 45 minutes sur 120**. La regle "
        f"generale qui manquait aux quatre versions : **un garde-fou ne peut chercher qu'un "
        f"progres plus grand que l'ecart detectable a son propre budget.** D'ou la portee "
        f"{portee}, et `agents.campagne.portee_minimale` qui la calcule.",
    ]


def phase3_mesure_donnes_garde_fou() -> int:
    """Le nombre de donnes du garde-fou, **demande au module qui le fixe**, jamais recopie."""
    from agents import campagne

    return campagne.DONNES_GARDE_FOU


def section_comportements(
    lignes: list[str],
    comparaisons: Sequence[phase3_mesure.Comparaison],
    nb_parties: int,
) -> None:
    """B1 a B7, compares a la ligne de base regeneree **au meme grain**."""
    lignes.append(_titre("5. Les comportements B1 a B7"))
    lignes += [
        "**La ligne de base est REGENEREE**, et ce n'est pas une commodite : ma composition est "
        "un agent contre deux greedys, un seul siege mesure. Sa ligne de base est donc **trois "
        "greedys, UN seul siege compte**, et elle n'existe pas dans le depot. Meme composition, "
        "meme decalage de graine `6000000`, memes seeds **que la phase 2** : seuls les sieges "
        "**comptes** changent.",
        "",
        "> **« Memes seeds » designe la phase 2, PAS la campagne de l'agent**, et une premiere "
        "redaction laissait croire le contraire. La ligne de base joue les donnes **0 a 1999** "
        "-- celles de `phase2.campagne_b`, `DEPART_B = 0` --, l'agent les donnes **60000 a "
        "61999**. **Les deux echantillons ne partagent aucune donne, et la comparaison n'est "
        "donc PAS appariee** : c'est une comparaison entre deux echantillons independants, et "
        "l'ecart detectable ci-dessous en tient compte des deux cotes. Regenerer la ligne de "
        "base sur les donnes de l'agent aurait change la population de reference pour une "
        "seconde raison, et elle n'aurait plus ete celle de la phase 2.",
        "",
        "`comportements.ecart_de_taux` **leve** si les grains different. Elle est appelee "
        "plutot que contournee : une ligne dont le grain differe fait tomber la mesure au lieu "
        "de produire un nombre qu'il faudrait relire.",
        "",
        f"**Le detectable est calcule sur les DEUX effectifs**, chacun avec son taux et son "
        f"denominateur -- `phase3_mesure.ecart_detectable_deux_echantillons`. La formule de la "
        f"phase 2 suppose deux echantillons de meme taille ; les denominateurs d'action n'y "
        f"obeissent pas, et l'ecart pouvait atteindre 67 % sur `B4-strict`. **Aucune ligne ne "
        f"change de statut**, mais le chiffre publie au premier tour etait faux.",
        "",
        f"**Les exclusions sont recalculees au budget de {nb_parties} parties**, jamais "
        f"recopiees : ce sont des proprietes du couple `(ligne, budget)`. Voir "
        f"`mesure/phase3_budget_des_comportements.py`.",
        "",
        "> **La regle « hors budget » de la pre-inscription ne s'applique pas ici, et il faut "
        "le dire plutot que de la laisser croire appliquee.** Le paragraphe 9.2 annoncait que "
        "les huit lignes hors budget a 6 000 parties ne seraient pas comparees, et les "
        "nommait ; ces huit noms sont calcules sur l'ecart **greedy contre hasard** de la "
        "phase 2, qui n'est pas l'ecart de cette phase. La branche qui les excluait etait par "
        "ailleurs **inatteignable** -- `ecart=None` rendait `hors_budget` toujours faux --, "
        "donc elle n'a jamais rien exclu : elle est retiree. Le critere qui s'exerce est "
        "`|ecart| > detectable`, **le meme critere** exprime sur l'ecart effectivement mesure, "
        "et la colonne « Separable ? » publie desormais le nombre de parties que chaque ligne "
        "non separable demanderait.",
        "",
    ]
    exactes = [c for c in comparaisons if c.regle == phase3_mesure.REGLE_BORNES_EXACTES]
    if exactes:
        lignes += [
            "",
            f"**{len(exactes)} ligne(s) sont tranchees par une AUTRE regle, et le tableau la "
            f"nomme.** "
            + ", ".join(f"`{c.nom}`" for c in exactes)
            + " porte(nt) un **zero absolu** d'un cote. Sur un zero, la variance binomiale est "
            "nulle : la formule normale rendrait « tout est detectable », ce qui est exactement "
            "faux, donc `ecart_detectable_deux_echantillons` rend `None`. **Ce `None` etait "
            "imprime « non separable a ce budget » au tour 2** -- une conclusion que rien "
            "n'avait calculee, et fausse. Un zero se traite par sa **borne exacte**, celle de "
            "Clopper-Pearson, qui ne suppose aucune normalite : "
            + " ; ".join(
                f"`{c.base.succes}/{c.base.total}` a pour borne haute exacte "
                f"{LATERALITE_EXACTE} **{_borne(c.borne_exacte)}** quand l'agent vaut "
                f"**{_pct(c.agent.taux())}**"
                for c in exactes
            )
            + ". Le rendu **leve** desormais sur toute ligne qu'aucune regle n'a tranchee, "
            "plutot que de lui donner un verdict par defaut.",
            "",
            "> **Le tour 2 se contredisait dans ce document meme** : ce tableau declarait "
            f"`{exactes[0].nom}` non separable, et le paragraphe 6 argumentait une demi-page "
            f"sur ce que son ecart de {_pt(exactes[0].ecart)} etablit. C'est le tableau qui "
            f"avait tort.",
        ]
    if any(c.nom.endswith("-par-partie") for c in comparaisons):
        lignes += [
            "",
            "> **Les lignes `-par-partie` portent ici les MEMES nombres que leur ligne au grain "
            "du couple, et ce n'est pas un defaut.** Un seul siege est mesure par partie, donc "
            "« au moins un des 1 sieges » et « le siege mesure » comptent exactement la meme "
            "chose. C'est deja le cas de la colonne a un siege de la phase 2. Les deux sont "
            "gardees pour que le grain reste lisible dans le libelle, et parce que "
            "`ecart_de_taux` leve si on les compare a une population qui en agrege trois.",
        ]
    # Le blockquote passe AVANT l'en-tete, et l'en-tete est colle a ses lignes. Une ligne vide
    # ou un blockquote entre l'en-tete et le corps **termine le tableau** en Markdown : au
    # premier tour, les 34 lignes de cette section sortaient dans un `<p>`, pas dans un
    # `<table>`. C'etait le tableau central du rapport.
    lignes += [
        "",
        "| Compteur | Agent | Ligne de base | Ecart | Detectable | Separable ? |",
        "|---|---|---|---:|---:|---|",
    ]
    for comparaison in comparaisons:
        agent, base = comparaison.agent, comparaison.base
        # **La garde qui LEVE.** Une ligne dont aucune regle n'a tranche ne s'imprime pas :
        # « non separable a ce budget » est une CONCLUSION, et le tour 2 la publiait sur deux
        # lignes qu'il n'avait pas calculees -- les deux zeros de la ligne de base, que la
        # formule normale rend `None`. Le rapport les declarait non separables dans son
        # tableau pendant que son texte argumentait une demi-page sur ce qu'elles etablissent.
        # Rien ne se publie qu'une regle nommee n'ait tranche.
        if comparaison.separable is None and comparaison.exclu is None:
            raise ValueError(
                f"{comparaison.nom} : aucune regle n'a tranche cette ligne "
                f"({comparaison.regle}), et un tableau ne publie pas un verdict qu'il n'a pas "
                f"calcule. Ecart {comparaison.ecart}, detectable {comparaison.detectable}, "
                f"agent {agent.succes}/{agent.total}, base {base.succes}/{base.total}."
            )
        if comparaison.exclu is not None:
            verdict = f"**non compare** : {comparaison.exclu}"
        elif comparaison.regle == phase3_mesure.REGLE_BORNES_EXACTES:
            verdict = _phrase_de_borne_exacte(comparaison)
        elif comparaison.separable:
            verdict = "**separable**"
        elif comparaison.parties_requises is not None:
            verdict = (
                f"non separable a ce budget -- il en faudrait "
                f"{comparaison.parties_requises} de chaque cote"
            )
        else:
            verdict = "non separable a ce budget"
        lignes.append(
            f"| `{comparaison.nom}` | {_pct(agent.taux())} ({agent.succes}/{agent.total}) | "
            f"{_pct(base.taux())} ({base.succes}/{base.total}) | {_pt(comparaison.ecart)} | "
            f"{_pct(comparaison.detectable)} | {verdict} |"
        )


def section_lecture_de_b4(
    lignes: list[str], comparaisons: Sequence[phase3_mesure.Comparaison], bat_le_greedy: bool
) -> None:
    """Les quatre compteurs de B4 juges par l'evaluation MYOPE du greedy, et leur piege.

    La phase 2 pre-inscrit une lecture flatteuse : « pour un agent de la phase 3, ce meme zero
    cesse d'etre tautologique [...] un refus par anticipation d'un retournement y comptera, ce
    qui se lit comme un signe de planification et non comme un defaut ». Cette section existe
    pour **confronter cette lecture aux chiffres** au lieu de la recopier.
    """
    par_nom = {c.nom: c for c in comparaisons}
    interessants = [
        n
        for n in ("B4-contre-nature", "B4-meurtre-couteux", "B4-brut", "B4-strict")
        if n in par_nom
    ]
    if not interessants:
        return
    lignes.append(
        _titre("6. B4 -- le piege de lecture, et pourquoi je refuse la lecture flatteuse")
    )
    lignes += [
        "**Quatre compteurs de B4 sont definis par rapport a `greedy.evaluer_actions`**, "
        "c'est-a-dire par l'evaluation **myope** du greedy lui-meme -- `B4-strict`, "
        "`B4-departage`, `B4-contre-nature` et `B4-meurtre-couteux`. Chez le greedy leur valeur "
        "est **tautologique** : `choisir` prend un argmax, donc il ne peut pas se contredire. "
        "Les deux zeros absolus de la phase 2 sont dans ce lot.",
        "",
        "**Chez un agent dont l'argmax n'est pas celui de l'etalon, ces compteurs cessent "
        "d'etre tautologiques.** Ils mesurent alors une chose et une seule : **a quelle "
        "frequence l'agent contredit l'evaluation myope du greedy.**",
        "",
        "| Compteur | Agent | Ligne de base (3 greedys) | Ce que l'ecart mesure |",
        "|---|---|---|---|",
    ]
    for nom in interessants:
        c = par_nom[nom]
        lignes.append(
            f"| `{nom}` | {_pct(c.agent.taux())} ({c.agent.succes}/{c.agent.total}) | "
            f"{_pct(c.base.taux())} ({c.base.succes}/{c.base.total}) | "
            f"desaccord avec l'evaluation myope |"
        )
    contre_nature = par_nom.get("B4-contre-nature")
    taux = contre_nature.agent.taux() if contre_nature else None
    lignes += [
        "",
        "### La lecture que la phase 2 propose, et pourquoi elle ne tient pas ici",
        "",
        "Le rapport de la phase 2 ecrit : « pour un agent de la phase 3, ce meme zero cesse "
        "d'etre tautologique : son argmax n'est pas celui de l'etalon, donc `B4-contre-nature` "
        "devient un vrai diagnostic -- et **un refus par anticipation d'un retournement y "
        "comptera, ce qui se lit comme un signe de planification** et non comme un defaut ».",
        "",
        "**Je refuse cette lecture pour cet agent, et le motif est dans le paragraphe 1.** "
        "`B4-contre-nature` vaut "
        + (f"**{_pct(taux)}**" if taux is not None else "un taux non nul")
        + " chez lui contre **"
        + (_pct(contre_nature.base.taux()) if contre_nature is not None else "0,00 %")
        + "** chez le greedy -- un ecart "
        + (
            "**separable**, et le paragraphe 5 dit par quelle regle : la borne haute exacte "
            f"{LATERALITE_EXACTE} de ce zero vaut {_borne(contre_nature.borne_exacte)}"
            if contre_nature is not None
            and contre_nature.borne_exacte is not None
            and contre_nature.separable
            else "dont le paragraphe 5 donne le statut"
        )
        + ". Deux hypotheses expliquent le meme chiffre :",
        "",
        "1. **l'agent voit quelque chose que l'evaluation myope ne voit pas** -- il refuse un "
        "meurtre localement gagnant parce qu'il anticipe un retournement. C'est la lecture "
        "flatteuse ;",
        "2. **l'agent joue moins bien** -- il refuse des meurtres qu'il aurait fallu commettre.",
        "",
        "**Les deux produisent exactement le meme compteur.** Ce qui les separe n'est pas dans "
        "B4, il est dans le juge : "
        + (
            "l'agent **bat** le greedy, ce qui rend la premiere hypothese defendable sans "
            "l'etablir."
            if bat_le_greedy
            else "**l'agent est battu par le greedy**, gain moyen negatif borne haute "
            "comprise. Un agent qui contredit massivement l'evaluation d'un adversaire qui le "
            "bat n'a pas etabli qu'il voit plus loin ; il a etabli qu'il decide autrement. La "
            "seconde hypothese est la plus economique, et rien ici ne la refute."
        ),
        "",
        "**Ce que ce compteur etablit, mot pour mot** : l'agent contredit l'evaluation myope du "
        "greedy a cette frequence. **Il n'etablit ni planification, ni erreur** -- il faudrait "
        "pour trancher une evaluation de reference qui ne soit ni myope ni celle de l'agent, et "
        "cette phase n'en a pas.",
        "",
        "La meme reserve vaut pour `B4-meurtre-couteux`, `B4-strict` et `B4-departage`, dont "
        "les denominateurs sortent du meme argmax.",
    ]


def section_ce_qui_n_est_pas_etabli(lignes: list[str]) -> None:
    """Pre-inscrite au paragraphe 10, recopiee ici pour que le rapport soit autoportant."""
    lignes.append(_titre("8. Ce que ces chiffres n'etablissent PAS"))
    lignes += [
        "**Ecrit avant la mesure.** Les points 1 a 6 sont le paragraphe 10 de la "
        "pre-inscription, mot pour mot ; le point 7 vient de son paragraphe 9.2, et le point 8 "
        "du paragraphe 2.2. Une premiere redaction attribuait les sept au seul paragraphe 10, "
        "dont elle omettait par ailleurs un point -- celui sur `sigma`, ici rendu au 8.",
        "",
        "1. **B1 et B3 mesurent la frequence a laquelle un MOTIF apparait, jamais une "
        "planification.** Ecrire « l'agent planifie des retournements dans X % des parties » "
        "serait faux quel que soit X. Le chiffre s'intitule *frequence du motif*, jamais "
        "*frequence de planification*.",
        "2. **B1 est plafonne par les 7,40 % de parties portant une perte d'acquis qu'aucun "
        "siege ne pouvait voir**, mesures en phase 1. Ces retournements sont **invulnerables a "
        "toute planification, par n'importe quel agent** : c'est un plafond du mesurable, pas "
        "un defaut d'agent.",
        "3. **Battre le greedy ne dit pas que l'agent est fort.** Le greedy a un horizon d'un "
        "tour, et son gain publie est un **plancher** de lui-meme -- son ciblage est plus myope "
        "que sa specification. Aucun chiffre ici ne borne la distance entre l'agent et un bon "
        "joueur.",
        "4. **Rien ici ne se transporte a `complet-3j`** -- 6 familles, 90 cartes, 10 tours.",
        "5. **Le controle de collision de tenseurs est un echantillon, pas une preuve "
        "d'injectivite.**",
        "6. **Aucun resultat de cette phase ne valide le moteur.** Elle le suppose conforme ; "
        "c'est la phase 0 qui l'etablit, et elle est close.",
        "7. **B7 devient separable par le bas a ce budget, il ne devient pas informatif.** "
        "`B7-occasions` vaut 1,22 % des poses au banquet : l'occasion de se manifester est "
        "rare, et un taux bas se lit sur ce fond-la. *(Paragraphe 9.2.)*",
        "8. **`sigma` est mesure sous l'hypothese nulle et SUPPOSE valoir sous l'agent.** Il "
        "est remesure au paragraphe 2, et il a bouge. *(Paragraphe 2.2.)*",
        "",
        "**Trois limites de plus, que le premier tour n'ecrivait pas et que l'audit a "
        "etablies.**",
        "",
        "9. **La courbe du garde-fou n'etablit pas que l'agent progressait ENCORE a la fin.** "
        "Elle etablit qu'il a progresse du premier au dernier checkpoint. Aucun pas consecutif "
        "n'atteint l'ecart detectable de ce budget -- voir le paragraphe 4.",
        "10. **Les 20 mutations de `outillage/mutation.py` ne couvrent AUCUN fichier de cette "
        "phase.** Elles ciblent toutes `courtisans/`, ce que le paragraphe 0.3 du protocole "
        "impose -- `agents/greedy.py` est la ligne de base de toutes les phases et ne porte "
        "aucune mutation. « 20 mutations, toutes detectees » ne dit donc **rien** de "
        "`agents/reseau.py`, `agents/entrainement.py`, `agents/campagne.py` ni de "
        "`mesure/phase3*.py` : ce que ces fichiers ont, ce sont leurs tests, pas une preuve "
        "que ces tests mordent. **Etendre le perimetre des mutations est un arbitrage de "
        "perimetre, remonte au pilote et non decide ici.**",
        "11. **Les comportements comparent deux echantillons de donnes DISJOINTES** -- 0 a "
        "1999 pour la ligne de base, 60000 a 61999 pour l'agent. La comparaison n'est pas "
        "appariee, et sa puissance est celle de deux echantillons independants.",
        "",
        "**Deux limites de plus, etablies par l'audit croise du tour 2 -- qui a REJETE les "
        "corrections du tour 1 sur des defauts qu'elles avaient elles-memes introduits.**",
        "",
        "12. **Les deux lignes a zero absolu ne sont pas separees par la regle du reste du "
        "tableau.** Elles le sont par des bornes exactes, un critere de non-recouvrement, plus "
        "conservateur et de puissance differente -- voir le paragraphe 5. Deux verdicts "
        "« separable » du meme tableau ne viennent donc pas tous du meme raisonnement, et la "
        "colonne le dit ligne par ligne. **Ce que le tour 1 en publiait etait faux**, et ce "
        "que le tour 2 en publiait -- « non separable a ce budget » -- etait une conclusion "
        "qu'aucun calcul n'avait rendue.",
        "13. **Le garde-fou n'a jamais ete eprouve en conditions reelles sur un effondrement.** "
        "Sa version 5 laissait passer une chute etablie -- **17,80 points sur le support de "
        "l'auditeur du tour 2**, qui n'est pas un checkpoint de ce run -- parce qu'elle "
        "demandait « l'ecart est-il etabli ? » au lieu de « est-ce un progres etabli ? ». "
        "Le defaut est "
        "corrige et un cas hostile le tient, mais **il a ete trouve par un auditeur, pas par "
        "le run** : ce run n'a pas eu d'effondrement, donc rien n'a exerce cette branche en "
        "vrai. **Cinquieme defaut du meme garde-fou, et le cinquieme est ne dans la correction "
        "du quatrieme.**",
    ]


def section_audit(lignes: list[str], controles: Sequence) -> None:
    """L'auto-audit, **ecrit avant le resultat** et joue sur lui.

    Un controle ecrit apres avoir vu un chiffre est un controle que le chiffre a passe par
    construction. Ceux-ci sont dans `mesure/phase3_audit.py`, commite avant l'entrainement.
    """
    lignes.append(_titre("7. L'audit de ce resultat, par ses propres controles"))
    lignes += [
        "**Les zeros absolus de la ligne de base -- ceux que R4 nomme ci-dessous, avec leurs "
        "comptes -- sont confrontes a un cas construit a la main**, comme "
        "le paragraphe 0.2 l'exige, par quatre cas de `tests/mesure/test_comportements.py` : "
        "deux qui fabriquent le nœud et exigent que le compteur le classe, un qui retrouve les "
        "zeros sur de vraies parties, et **un contre-cas** ou une politique uniforme en produit "
        "-- sans lui, un compteur mort rendrait le meme zero. Le controle R4 les **liste** "
        "desormais : au premier tour il ne regardait que l'agent, et imprimait « aucune » "
        "pendant que le rapport en publiait deux.",
        "",
        "**Ces controles sont ecrits et commites AVANT que l'agent ne soit mesure** -- "
        "`mesure/phase3_audit.py`. Un controle ecrit apres avoir vu un chiffre est un controle "
        "que le chiffre a passe par construction.",
        "",
        "Ils portent sur des **unites**, des **denominateurs** et des **populations**, jamais "
        "sur des valeurs : reproduire un nombre ne le valide pas, et un facteur trois indu a "
        "survecu a deux verifications reussies en phase 2 pour cette raison.",
        "",
        "| Question | Controle | Verdict | Preuve |",
        "|---|---|---|---|",
    ]
    for controle in controles:
        etat = {
            "concluant": "concluant",
            "en echec": "**ECHOUE**",
            "releve": "*releve* -- il liste, il ne juge pas",
        }[controle.statut]
        lignes.append(
            f"| {controle.code} | {controle.intitule} | {etat} | {controle.preuve} |"
        )
    echoues = [c for c in controles if c.statut == "en echec"]
    eprouves = [c for c in controles if c.eprouve]
    releves = [c for c in controles if not c.eprouve]
    lignes += [
        "",
        (
            f"**{len(echoues)} controle(s) en echec : "
            + ", ".join(c.intitule for c in echoues)
            + ". Aucun chiffre de ce rapport ne vaut tant qu'ils ne sont pas expliques.**"
            if echoues
            else f"**{len(eprouves)} controles eprouves, aucun en echec"
            + (
                f" ; {len(releves)} releves, qui ne s'y comptent pas -- "
                + ", ".join(c.code for c in releves)
                + ".**"
                if releves
                else ".**"
            )
        ),
        "",
        "> **Un controle qui ne peut pas echouer ne se compte pas parmi les concluants**, et "
        "c'est desormais une regle du paragraphe 0.2 du protocole. Une premiere redaction de "
        "ce rapport annoncait « dix controles, aucun en echec » alors que **deux** d'entre eux "
        "passaient un `True` **litteral** : ils listaient les zeros et les ecarts d'unite sans "
        "jamais pouvoir tomber. Le compte rendu affirmait par-dessus que **chacun** des dix "
        "etait verifie capable d'echouer, alors que le fichier de tests n'en cassait que six.",
        ">",
        "> Les deux constructeurs sont donc distincts -- `_epreuve` et `_releve` --, "
        "`tests/mesure/test_phase3_audit.py` **lit l'AST de `mesure/phase3_audit.py`** pour "
        "refuser qu'un booleen litteral soit passe a `_epreuve`, et les quatre controles qui "
        "n'etaient pas casses le sont, chacun par reinjection de la faute qu'il pretend "
        "attraper.",
    ]


def rapport(
    contre_greedys: phase3_mesure.Mesure,
    pool: Sequence[phase3_mesure.Mesure],
    comparaisons: Sequence[phase3_mesure.Comparaison],
    jalons: Sequence[dict],
    controles: Sequence,
) -> str:
    """Assemble le rapport complet en Markdown."""
    lignes: list[str] = [
        "# Phase 3 -- le premier agent entraine",
        "",
        "Genere par `uv run python -m mesure.phase3_mesure`. Aucune interpretation : chaque "
        "chiffre porte sa decomposition, sa composition et son denominateur. Les seuils "
        "rappeles sont ceux de `mesure/phase3_hypothese_et_instrument.md`, commite **avant** "
        "l'entrainement.",
        "",
        f"Instance : `familles={phase3.CONFIG.familles}`, {len(phase3.CONFIG.roles)} roles, "
        f"`exemplaires={phase3.CONFIG.exemplaires}`, `joueurs={phase3.CONFIG.joueurs}` -- "
        f"{phase3.CONFIG.nb_cartes} cartes, {phase3.CONFIG.tours} tours par joueur.",
        "",
        "Algorithme : **PPO a masque d'actions**, reseau unique partage par les trois sieges, "
        "tete de valeur, `gamma = 1`, `lambda = 1`. Pool d'entrainement : 60 % copie courante, "
        "40 % checkpoint fige. **Ni le greedy ni l'aleatoire n'entrent dans le pool.**",
    ]
    section_juge(lignes, contre_greedys)
    section_dimensionnement(lignes, contre_greedys)
    section_pool(lignes, pool)
    section_garde_fou(lignes, jalons)
    section_comportements(lignes, comparaisons, contre_greedys.nb_parties)
    section_lecture_de_b4(
        lignes, comparaisons, contre_greedys.verdict.bat_le_greedy
    )
    section_audit(lignes, controles)
    section_ce_qui_n_est_pas_etabli(lignes)
    return "\n".join(lignes) + "\n"


def section_durees(passes: Sequence[dict]) -> str:
    """Les durees machine, sur **toutes** les passes enregistrees, avec leur etendue.

    Le paragraphe 0.2 est net : « Aucune duree ne se cite sur un seul chronometrage. Sur la
    machine du projet, cinq passes du meme code donnent un rapport max/min de 2,93 a 3,00 par
    campagne, **de facon non monotone**. Le temps mural mesure l'etat de la machine, pas le
    cout du code. Toute duree se cite sur au moins **trois passes, avec son etendue**. »

    Cette fonction ne recopie aucun chiffre : elle lit le journal des durees, qu'une ligne
    alimente a chaque lancement de la mesure. Elle **dit** combien de passes elle a, et refuse
    de presenter moins de trois comme une mesure.
    """
    if not passes:
        return ""
    etapes = list(passes[0])
    lignes = [
        "",
        f"## 9. Duree machine -- {len(passes)} passe(s)",
        "",
    ]
    if len(passes) < 3:
        lignes += [
            f"> **{len(passes)} passe(s) seulement.** Le paragraphe 0.2 exige au moins trois "
            f"passes avec leur etendue : ces valeurs sont donnees pour reproduire l'ordre de "
            f"grandeur du cout, et **aucune conclusion n'en est tiree**. Relancer la commande "
            f"du paragraphe 9.5 de la pre-inscription ajoute une passe.",
            "",
        ]
    else:
        lignes += [
            f"**{len(passes)} passes**, etendue publiee. Le temps mural mesure l'etat de la "
            f"machine, pas le cout du code : le rapport max/min ci-dessous est a lire comme "
            f"tel, et non comme une variation du programme.",
            "",
        ]
    lignes += [
        "| Etape | Minimum | Maximum | Rapport max/min |",
        "|---|---:|---:|---:|",
    ]
    for etape in etapes:
        valeurs = [passe[etape] for passe in passes if etape in passe]
        if not valeurs:
            continue
        mini, maxi = min(valeurs), max(valeurs)
        rapport_mm = maxi / mini if mini > 0 else float("nan")
        lignes.append(f"| {etape} | {mini:.1f} s | {maxi:.1f} s | {rapport_mm:.2f} |")
    totaux = [sum(passe.values()) for passe in passes]
    lignes += [
        "",
        "Total par passe : "
        + ", ".join(f"{total:.1f} s" for total in totaux)
        + f" -- etendue {min(totaux):.1f}-{max(totaux):.1f} s, rapport "
        f"{max(totaux) / min(totaux):.2f}.",
        "",
    ]
    return "\n".join(lignes)


def ecrire(texte: str, chemin: pathlib.Path) -> None:
    """Ecrit le rapport **en UTF-8**, depuis Python. Voir la docstring du module."""
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(texte, encoding="utf-8", newline="\n")



__all__ = ["ecrire", "rapport", "section_durees"]
