"""L'auto-audit : chaque controle doit pouvoir ECHOUER -- ou dire qu'il ne le peut pas.

Un controle qui ne peut pas echouer ne prouve rien. C'est la lecon que le greedy a laissee --
chacune de ses trois preuves est assortie d'un cas qui verifie que le piege mord -- et elle
vaut mot pour mot ici : `mesure/phase3_audit.py` est ecrit avant le resultat, donc personne ne
peut savoir qu'il mord tant qu'on ne le lui a pas fait faire.

**Ce fichier ne tenait pas cette promesse, et l'audit du tour 1 l'a montre.** Il cassait six
controles sur dix. Des quatre autres : deux passaient un `True` **litteral** -- aucune entree
ne pouvait les faire tomber --, un eprouvait `bootstrap_par_donne` sur des donnees fabriquees
sans jamais toucher le controle, et le dernier verifiait la **forme** de la preuve. Le compte
rendu affirmait pourtant que **chacun** des dix etait verifie capable d'echouer.

Trois choses ici, donc :

  - les **huit** controles eprouvables sont casses, chacun par reinjection de la faute qu'il
    pretend attraper ;
  - les **deux** releves sont verifies **relevés** -- ils listent, et le disent ;
  - `test_aucun_controle_eprouve_ne_passe_un_booleen_litteral` **lit l'AST du module** : c'est
    la parade qui empeche le defaut de revenir, la ou une docstring ne l'empechait pas.
"""

from __future__ import annotations

import dataclasses
import random
from pathlib import Path

from mesure import phase2, phase3, phase3_mesure
from mesure import phase3_audit as audit


def _mesure(donnes: int = 8) -> phase3_mesure.Mesure:
    """Une mesure minuscule : c'est la STRUCTURE des controles qu'on teste, pas leur valeur."""
    return phase3_mesure.mesurer(
        agent=phase3.greedy_de_reference,
        adversaire=phase3.greedy_de_reference,
        donnes=donnes,
        intitule="1 greedy contre 2 greedys (support de test)",
        depart=phase3_mesure.DEPART_CAMPAGNE_FINALE,
    )


def test_le_controle_de_somme_nulle_mord_sur_un_gain_falsifie():
    """Si I5 tombait, le niveau nul du seuil n'aurait plus de valeur connue."""
    mesure = _mesure()
    assert audit.controle_somme_nulle(mesure, mesure.campagne).passe

    trace = mesure.campagne.traces[0][0]
    faussee = dataclasses.replace(trace, gains=(1.0, 1.0, 1.0))
    campagne_faussee = dataclasses.replace(
        mesure.campagne,
        traces=((faussee,) + mesure.campagne.traces[0][1:],) + mesure.campagne.traces[1:],
    )
    controle = audit.controle_somme_nulle(mesure, campagne_faussee)
    assert not controle.passe
    assert "3.000e+00" in controle.preuve, controle.preuve


def test_le_controle_de_plan_equilibre_mord_sur_un_siege_double():
    """Le desequilibre deplacerait le niveau nul d'un ecart entre sieges -- +0,5735 mesure."""
    mesure = _mesure()
    assert audit.controle_plan_equilibre(mesure.campagne).passe

    desequilibre = dataclasses.replace(
        mesure.campagne,
        sieges_mesures=((0, 0, 1),) + mesure.campagne.sieges_mesures[1:],
    )
    controle = audit.controle_plan_equilibre(desequilibre)
    assert not controle.passe
    assert "1 desequilibrees" in controle.preuve, controle.preuve


def test_le_controle_de_denominateur_mord_sur_un_compte_falsifie():
    """`parties = donnes x sieges`, reconstruit et non recopie."""
    mesure = _mesure()
    assert audit.controle_denominateur(mesure).passe
    faussee = dataclasses.replace(mesure, nb_parties=mesure.nb_parties + 1)
    assert not audit.controle_denominateur(faussee).passe


def test_le_controle_des_populations_mord_sur_un_doublon_et_sur_un_nom_muet():
    """Deux compositions de meme nom se liraient comme une seule dans le rapport."""
    mesure = _mesure()
    autre = dataclasses.replace(mesure, intitule="1 agent contre 2 aleatoires")
    assert audit.controle_populations_nommees([mesure, autre]).passe

    doublon = audit.controle_populations_nommees([mesure, mesure])
    assert not doublon.passe
    assert "doublons" in doublon.preuve

    muet = dataclasses.replace(mesure, intitule="la campagne")
    resultat = audit.controle_populations_nommees([muet, autre])
    assert not resultat.passe
    assert "sans composition" in resultat.preuve


def test_le_controle_de_grain_mord_sur_deux_grains_differents():
    """La faute bloquante du tour 1 de la phase 2, avec inversion de signe sur B1."""
    from mesure import comportements as comp

    compte = comp.Compte(nom="B1-motif", succes=5, total=10, grain="couples", vue="decideur")
    autre_grain = comp.Compte(
        nom="B1-motif", succes=5, total=10, grain="parties", vue="decideur"
    )
    bonne = phase3_mesure.Comparaison(
        nom="B1-motif", agent=compte, base=compte, ecart=0.0,
        detectable=0.1, separable=False, regle=phase3_mesure.REGLE_DETECTABLE,
        borne_exacte=None, parties_requises=None, exclu=None,
    )
    assert audit.controle_grains([bonne]).passe

    mauvaise = dataclasses.replace(bonne, base=autre_grain)
    controle = audit.controle_grains([mauvaise])
    assert not controle.passe
    assert "B1-motif" in controle.preuve


def test_le_controle_de_grain_ignore_les_lignes_EXCLUES():
    """Une ligne non comparee n'a pas a coincider : l'exiger ferait echouer a tort."""
    from mesure import comportements as comp

    compte = comp.Compte(nom="B4-tout-dos", succes=1, total=10, grain="a", vue="decideur")
    autre = comp.Compte(nom="B4-tout-dos", succes=1, total=10, grain="b", vue="decideur")
    exclue = phase3_mesure.Comparaison(
        nom="B4-tout-dos", agent=compte, base=autre, ecart=None,
        detectable=None, separable=None, regle=phase3_mesure.REGLE_EXCLUE,
        borne_exacte=None, parties_requises=None,
        exclu="texte de la definition",
    )
    assert audit.controle_grains([exclue]).passe


def test_le_controle_des_seeds_mord_sur_le_defaut_QU_IL_A_TROUVE():
    """Le defaut reel, rejoue : les compositions du pool tombaient dans l'entrainement.

    La premiere version de `phase3_mesure` partait a 30 000 et decalait le pool de +100 000 et
    +200 000. L'entrainement part a 100 000 et consomme une donne par partie : a 229 parties
    par seconde pendant 7 200 secondes, il monte a environ 1 749 000. Le cas verifie que le
    controle **voit** ce chevauchement.
    """
    bon = audit.controle_seeds_disjoints(
        donnes_verdict=2_000, donnes_pool=500, nb_checkpoints=8,
        parties_entrainement=1_800_000,
    )
    assert bon.passe, bon.preuve

    # Le defaut d'origine : on remet le depart et les decalages fautifs.
    original = (
        phase3_mesure.DEPART_CAMPAGNE_FINALE,
        phase3_mesure.DECALAGE_POOL_ALEATOIRE,
        phase3_mesure.DECALAGE_POOL_CHECKPOINTS,
    )
    try:
        phase3_mesure.DEPART_CAMPAGNE_FINALE = 30_000
        phase3_mesure.DECALAGE_POOL_ALEATOIRE = 100_000
        phase3_mesure.DECALAGE_POOL_CHECKPOINTS = 200_000
        casse = audit.controle_seeds_disjoints(
            donnes_verdict=2_000, donnes_pool=500, nb_checkpoints=8,
            parties_entrainement=1_800_000,
        )
    finally:
        (
            phase3_mesure.DEPART_CAMPAGNE_FINALE,
            phase3_mesure.DECALAGE_POOL_ALEATOIRE,
            phase3_mesure.DECALAGE_POOL_CHECKPOINTS,
        ) = original
    assert not casse.passe
    assert "entrainement" in casse.preuve and "CHEVAUCHEMENTS" in casse.preuve


def test_le_controle_de_bootstrap_distingue_un_tirage_par_donne_d_un_tirage_par_partie():
    """Un bootstrap qui tirerait des parties rendrait un effet de plan de 1,0 par construction.

    Le cas construit des donnes **fortement correlees** -- toutes les parties d'une donne ont
    le meme gain -- et exige que les deux routes vers l'effet de plan le voient. Sur des
    donnes ainsi construites, l'effet doit etre tres au-dessus de 1.
    """
    import random as alea_module

    from mesure import bootstrap as boot

    correlees = [[1.0, 1.0, 1.0] if i % 2 else [-1.0, -1.0, -1.0] for i in range(40)]
    effet = boot.bootstrap_par_donne(
        correlees, 2_000, alea_module.Random(0)
    ).effet
    rho = boot.correlation_intra_donne(correlees)
    assert rho is not None and rho > 0.9, rho
    assert effet > 2.0, (
        f"effet de plan {effet:.4f} sur des donnes parfaitement correlees : le bootstrap ne "
        f"tire pas des donnes, ou l'effet de plan n'est pas calcule sur la bonne unite."
    )


def test_le_controle_du_niveau_nul_tourne_sur_les_seeds_DU_VERDICT():
    """Un niveau nul verifie ailleurs ne dit rien ici : c'est un autre echantillon."""
    controle = audit.controle_niveau_nul(
        donnes=20, depart=phase3_mesure.DEPART_CAMPAGNE_FINALE
    )
    assert str(phase3_mesure.DEPART_CAMPAGNE_FINALE) in controle.preuve
    assert "IC 99 %" in controle.preuve


def test_l_audit_complet_rend_un_controle_par_question_et_aucune_preuve_vide():
    """Une preuve qui dirait « OK » ne serait pas une preuve. Chacune porte un chiffre."""
    mesure = _mesure()
    base = phase3_mesure.ligne_de_base_trois_greedys_un_siege(donnes=8)
    comparaisons = phase3_mesure.comparer(
        mesure.comportements, base, mesure.nb_parties, 24, budget=24
    )
    controles = audit.auditer(
        mesure=mesure,
        campagne=mesure.campagne,
        pool=[mesure],
        comparaisons=comparaisons,
        base=base,
        nb_parties_base=24,
        donnes_calibration=8,
        donnes_pool=500,
        nb_checkpoints=8,
        parties_entrainement=1_800_000,
    )
    assert len(controles) == 10
    assert {c.code for c in controles} == {"Q1", "Q2", "Q3", "R1", "R2", "R3", "R4", "R5"}
    for controle in controles:
        assert controle.preuve.strip(), controle.intitule
        assert controle.preuve.strip().upper() not in {"OK", "PASSE", "VRAI"}
        assert any(caractere.isdigit() for caractere in controle.preuve), (
            f"« {controle.intitule} » : sa preuve ne porte aucun chiffre"
        )


def test_le_budget_de_la_phase_2_n_est_pas_deplace_par_la_phase_3():
    """La phase 3 passe son budget en argument ; elle ne deplace pas l'etalon d'un livrable."""
    assert phase2.BUDGET_PHASE_3 == 1_000


# ---------------------------------------------------------------------------------------
# Les quatre controles que l'audit du tour 1 a trouves NON casses
# ---------------------------------------------------------------------------------------


def _predicats_litteraux(source: str) -> tuple[list[str], int]:
    """Les `_epreuve(...)` dont le predicat est un booleen en dur, et le nombre d'appels vus.

    **Positionnel ET par mot-cle.** Le tour 2 ne regardait que `args[2]`, si bien qu'un
    `_epreuve(code=..., passe=True, ...)` la traversait sans la faire tomber -- meme famille
    que la reserve laissee sur la parade des intitules : une garde qui ne couvre qu'une des
    formes syntaxiques d'une meme ecriture.

    Le compte d'appels est rendu **pour que l'appelant l'exige non nul**. Sans lui, renommer
    `_epreuve` viderait la boucle et le cas resterait vert sans avoir rien inspecte : c'est
    l'autre facon dont une parade cesse silencieusement de garder.
    """
    import ast

    fautifs: list[str] = []
    vus = 0
    for noeud in ast.walk(ast.parse(source)):
        if not isinstance(noeud, ast.Call) or getattr(noeud.func, "id", None) != "_epreuve":
            continue
        vus += 1
        # `_epreuve(code, intitule, passe, preuve)` : le predicat est le troisieme argument,
        # qu'il soit passe par position ou sous son nom.
        predicat = noeud.args[2] if len(noeud.args) >= 3 else None
        for motcle in noeud.keywords:
            if motcle.arg == "passe":
                predicat = motcle.value
        if isinstance(predicat, ast.Constant) and isinstance(predicat.value, bool):
            fautifs.append(f"ligne {noeud.lineno} : passe={predicat.value!r}")
    return fautifs, vus


def test_aucun_controle_eprouve_ne_passe_un_booleen_litteral():
    """**La parade.** Un `True` en dur dans un `_epreuve` fait un controle qui ne peut pas
    echouer, et c'est exactement ce que R4 et R5 faisaient. Une docstring ne l'empeche pas ;
    l'AST, si.
    """
    import pathlib

    source = pathlib.Path(audit.__file__).read_text(encoding="utf-8")
    fautifs, vus = _predicats_litteraux(source)
    assert vus >= 8, (
        f"la parade n'a trouve que {vus} appel(s) a `_epreuve` dans {audit.__file__} : elle "
        f"n'inspecte plus ce qu'elle croit inspecter, et resterait verte quoi qu'on ecrive"
    )
    assert not fautifs, (
        "un controle eprouve porte un booleen litteral, donc il ne peut pas echouer : "
        + " ; ".join(fautifs)
        + ". Utiliser `_releve` si le controle liste sans juger."
    )


def test_la_parade_du_booleen_litteral_MORD_sur_LES_DEUX_ecritures():
    """Une parade qu'on n'a jamais vue tomber ne garde rien -- et celle-ci ne voyait qu'une
    des deux facons d'ecrire la meme faute."""
    positionnel = '_epreuve("R4", "les zeros", True, "aucune")'
    par_motcle = '_epreuve(code="R4", intitule="les zeros", passe=True, preuve="aucune")'
    calcule = '_epreuve("R4", "les zeros", len(extremes) == 0, "aucune")'

    for source in (positionnel, par_motcle):
        fautifs, vus = _predicats_litteraux(source)
        assert vus == 1 and fautifs, f"la parade laisse passer : {source}"

    fautifs, vus = _predicats_litteraux(calcule)
    assert vus == 1 and not fautifs, "la parade accuse un predicat calcule"


def test_le_controle_du_niveau_nul_MORD_sur_un_instrument_decalibre():
    """La faute que ce controle pretend attraper : un niveau nul qui n'est pas a zero.

    On met a la place du greedy une politique qui n'est PAS l'egale de ses deux adversaires --
    l'uniforme. L'esperance du gain mesure n'est alors plus nulle, et le controle doit le voir.
    Au tour 1, ce controle n'etait eprouve que sur la **forme** de sa preuve.
    """
    bon = audit.controle_niveau_nul(donnes=20, depart=phase3_mesure.DEPART_CAMPAGNE_FINALE)
    assert bon.passe, bon.preuve
    assert bon.statut == "concluant"

    casse = audit.controle_niveau_nul(
        donnes=20,
        depart=phase3_mesure.DEPART_CAMPAGNE_FINALE,
        agent=phase3.uniforme,
    )
    assert not casse.passe, casse.preuve
    assert casse.statut == "en echec"


def test_le_controle_de_bootstrap_MORD_si_le_bootstrap_tirait_des_PARTIES(monkeypatch):
    """La faute exacte : un bootstrap qui tirerait des parties rend un effet de plan de 1,0.

    Au tour 1, le cas eprouvait `boot.bootstrap_par_donne` sur des donnees fabriquees -- utile,
    mais il ne faisait jamais tomber le controle lui-meme.

    Le support est construit a la main et porte la structure de la composition reelle : les
    trois sieges d'une donne se partagent une somme nulle, donc `rho` y est **negatif** et
    l'effet de plan franchement sous 1. C'est cette structure que le controle doit voir
    disparaitre si le bootstrap se met a tirer des parties.
    """
    from mesure import bootstrap as boot

    class SupportConstruitALaMain:
        """Ce que `controle_bootstrap_par_donne` regarde, et rien de plus."""

        replicats_par_donne = 3

        def gains_par_donne(self):
            # Somme nulle dans chaque donne -- `rho` negatif --, plus une derive lente entre
            # donnes pour que l'effet de plan ne soit pas EXACTEMENT nul : la composition
            # reelle est a 0,887, pas a 0.
            alea = random.Random(4)
            groupes = []
            for _ in range(200):
                a = alea.uniform(-1.0, 1.0)
                b = alea.uniform(-1.0, 1.0)
                groupes.append([a, b, -(a + b)])
            return groupes

    support = SupportConstruitALaMain()
    bon = audit.controle_bootstrap_par_donne(support)
    assert bon.passe, bon.preuve

    vrai = boot.bootstrap_par_donne

    def tire_des_parties(observations, repetitions, alea, risque=0.01):
        """La faute reinjectee : chaque partie devient sa propre donne."""
        plates = [[valeur] for groupe in observations for valeur in groupe]
        return vrai(plates, repetitions, alea, risque)

    monkeypatch.setattr(audit.boot, "bootstrap_par_donne", tire_des_parties)
    casse = audit.controle_bootstrap_par_donne(support)
    assert not casse.passe, casse.preuve
    assert casse.statut == "en echec"


def test_R4_est_un_RELEVE_et_regarde_les_DEUX_cotes():
    """Il ne peut pas echouer -- il liste --, et il doit le dire. Et il ne voyait que l'agent :
    les deux zeros absolus que le rapport publie sont du cote de la ligne de base."""

    def compte(nom, succes, total):
        from mesure import comportements as comp

        return comp.Compte(nom, succes, total, "refus", "publique")

    def comparaison(nom, a, b):
        return phase3_mesure.Comparaison(
            nom=nom, agent=a, base=b, ecart=0.0, detectable=1.0,
            separable=False, regle=phase3_mesure.REGLE_DETECTABLE,
            borne_exacte=None, parties_requises=None, exclu=None,
        )

    lignes = [
        comparaison("B4-contre-nature", compte("a", 1368, 3814), compte("b", 0, 1967)),
        comparaison("B4-meurtre-couteux", compte("a", 298, 8131), compte("b", 0, 10382)),
    ]
    controle = audit.controle_zeros(lignes)
    assert controle.statut == "releve"
    assert not controle.eprouve
    assert "2 valeur(s) extreme(s)" in controle.preuve, controle.preuve
    assert "B4-contre-nature [ligne de base]" in controle.preuve, controle.preuve
    assert "B4-meurtre-couteux [ligne de base]" in controle.preuve, controle.preuve


def test_R5_est_un_RELEVE_et_le_dit():
    """Un facteur dix sur l'unite le laissait « concluant » au tour 1. Il liste, et il le dit."""
    from mesure import comportements as comp

    class FausseMesure:
        comportements = {"X": comp.Compte("X", 5, 1000, "poses", "publique")}
        nb_parties = 100

    controle = audit.controle_unite_avant_valeur(
        FausseMesure(), {"X": comp.Compte("X", 5, 100, "poses", "publique")}, 100
    )
    assert controle.statut == "releve"
    assert "10.000 vs 1.000" in controle.preuve, controle.preuve


def test_R2_voit_le_doublon_de_nom_QUI_A_ECHAPPE_au_tour_1():
    """La composition du garde-fou portait le meme nom qu'une ligne du pool, et R2 ne voyait
    rien parce qu'il ne s'appliquait qu'au pool."""
    from agents import campagne as campagne_module

    mesure = _mesure()
    homonyme = dataclasses.replace(mesure, intitule=campagne_module.intitule_du_garde_fou())
    assert audit.controle_populations_nommees([mesure], []).passe
    casse = audit.controle_populations_nommees(
        [homonyme], [campagne_module.intitule_du_garde_fou()]
    )
    assert not casse.passe, casse.preuve
    assert "doublons" in casse.preuve, casse.preuve


#: Les formes d'expression qui **fabriquent** un intitule, et que la parade sait donc lire.
#: `ast.Name` et `ast.Attribute` -- `intitule=intitule`, `intitule=campagne.intitule` -- ne
#: fabriquent rien : elles transmettent un nom fabrique ailleurs, ou ce cas l'attrape deja.
#: Les compter ferait deux faux doublons sur `campagne.intitule` et masquerait les vrais.
FORMES_QUI_FABRIQUENT_UN_INTITULE = ("Constant", "Call", "JoinedStr")


def _cle_d_un_intitule(valeur, chemin) -> str | None:
    """La chaine qu'une expression `intitule=` fixe, ou `None` si elle n'en fixe aucune.

    **Un appel est EVALUE, pas seulement transcrit.** C'est la reserve que l'audit du tour 2 a
    laissee : la parade ne lisait que `ast.Constant`, si bien que redonner au pool le nom du
    garde-fou **via `intitule_du_garde_fou()`** la traversait sans la faire tomber. Or c'est
    la forme la plus probable du retour du defaut, maintenant que le site unique existe : on
    ne recopie plus une chaine, on rappelle la fonction.

    L'appel est donc resolu et execute avec ses arguments par defaut, et sa valeur de retour
    devient la cle -- ce qui rapproche un litteral et un appel qui rendent la meme chaine.
    S'il n'est pas resoluble ou s'il leve, on retombe sur son texte source : deux appels
    ecrits pareil restent un doublon.

    **Un appel QUALIFIE est resolu comme un appel nu, et c'est la reserve 3 de la phase 3.**
    La version du tour 3 cherchait le nom de la fonction dans le module ou l'APPEL est ecrit :
    pour `campagne_module.intitule_du_garde_fou()`, elle cherchait `intitule_du_garde_fou`
    dans `mesure/phase3_mesure.py`, ou il n'existe pas -- seul `campagne_module` y existe. La
    resolution echouait, la cle retombait sur le texte source, et le doublon passait.

    **Ce n'est pas un cas de bord : c'est la seule forme que le depot ecrit.**
    `mesure/phase3_mesure.py:887` -- le seul appel hors des tests -- traversait deja la parade.
    Une garde qui ne couvre pas le style de son propre depot ne garde rien, et c'est la seconde
    fois que cette parade est prise sur une forme syntaxique qu'elle ne voyait pas : le tour 2
    ne lisait que les litteraux, le tour 3 ne lisait que les appels nus.

    Le chemin qualifie est donc suivi **maillon par maillon** -- `a.b.c()` resout `a`, puis
    `b`, puis `c` -- au lieu de ne garder que le dernier nom.
    """
    import ast
    import importlib

    if type(valeur).__name__ not in FORMES_QUI_FABRIQUENT_UN_INTITULE:
        return None
    if isinstance(valeur, ast.Constant):
        return valeur.value if isinstance(valeur.value, str) else None
    if isinstance(valeur, ast.Call):
        fonction = _resoudre_l_appel(_chemin_pointe(valeur.func), chemin)
        if callable(fonction):
            try:
                rendu = fonction()
            except TypeError:  # des arguments sans defaut : on garde le texte source
                rendu = None
            if isinstance(rendu, str):
                return rendu
    return ast.unparse(valeur)


def _chemin_pointe(fonction) -> list[str] | None:
    """`a.b.c` -> `['a', 'b', 'c']` ; `c` -> `['c']` ; toute autre forme -> `None`.

    Rend le chemin **entier**, pas seulement son dernier maillon : c'est ce qui permet de
    resoudre un appel qualifie depuis le module ou il est ecrit, et c'est la reserve 3.
    """
    import ast

    maillons: list[str] = []
    courant = fonction
    while isinstance(courant, ast.Attribute):
        maillons.append(courant.attr)
        courant = courant.value
    if isinstance(courant, ast.Name):
        maillons.append(courant.id)
        return list(reversed(maillons))
    return None


def _alias_declares(chemin) -> dict[str, str]:
    """Les alias d'import d'un fichier : `alias -> chemin pointe complet`.

    **Lus dans l'AST du fichier, et non dans les globales du module importe**, et c'est ce qui
    fait la difference : `mesure/phase3_mesure.py` ecrit `from agents import campagne as
    campagne_module` **a l'interieur d'une fonction**. L'alias n'est donc pas un attribut du
    module, et une resolution par `getattr(module, alias)` echoue -- sans rien dire, en
    retombant sur le texte source.

    C'est la forme reelle du seul appel qualifie du depot. Une parade syntaxique qui ne lirait
    que les imports de premier niveau raterait exactement celui qu'elle doit garder.
    """
    import ast

    alias: dict[str, str] = {}
    arbre = ast.parse(chemin.read_text(encoding="utf-8"))
    for noeud in ast.walk(arbre):
        if isinstance(noeud, ast.Import):
            for nom in noeud.names:
                alias[nom.asname or nom.name.split(".")[0]] = nom.name
        elif isinstance(noeud, ast.ImportFrom) and noeud.module and noeud.level == 0:
            for nom in noeud.names:
                alias[nom.asname or nom.name] = f"{noeud.module}.{nom.name}"
    return alias


def _resoudre_l_appel(chemin_pointe, chemin):
    """L'objet appelable designe par `a.b.c`, ou `None` s'il ne se resout pas.

    Deux routes, dans cet ordre, parce qu'aucune des deux ne couvre l'autre :

    1. **les alias d'import declares dans le fichier** -- la seule qui voie un import local a
       une fonction, donc la seule qui voie l'appel qualifie que le depot ecrit ;
    2. **les attributs du module importe** -- la route du tour 3, qui voit un appel nu produit
       par un `from ... import` de premier niveau.

    Aucune ne leve : une expression qui ne se resout pas retombe sur son texte source, et deux
    appels ecrits pareil restent un doublon.
    """
    import importlib

    if not chemin_pointe:
        return None

    def _descendre(objet, maillons):
        for maillon in maillons:
            objet = getattr(objet, maillon, None)
            if objet is None:
                return None
        return objet

    alias = _alias_declares(chemin)
    if chemin_pointe[0] in alias:
        pointe = alias[chemin_pointe[0]].split(".")
        for coupe in range(len(pointe), 0, -1):
            try:
                module = importlib.import_module(".".join(pointe[:coupe]))
            except ImportError:
                continue
            objet = _descendre(module, [*pointe[coupe:], *chemin_pointe[1:]])
            if objet is not None:
                return objet

    try:
        module = importlib.import_module(
            str(chemin.with_suffix("")).replace("/", ".").replace("\\", ".")
        )
    except ImportError:  # pragma: no cover -- le fichier vient du depot
        return None
    return _descendre(module, chemin_pointe)


def test_les_intitules_du_depot_sont_deux_a_deux_DISTINCTS():
    """**La parade du defaut 5.** Deux campagnes differentes ne peuvent plus porter le meme nom
    sans que ce cas ne tombe -- il lit les intitules de tout le code de mesure, pas seulement
    ceux qu'un appelant a pense passer a R2.

    **Il lit les APPELS autant que les litteraux**, et c'est la reserve levee du tour 2 : voir
    `_cle_d_un_intitule`. R2 reste le second filet ; ce cas est le premier, et il en fallait
    deux, parce que R2 ne voit que ce qu'on lui passe.
    """
    import ast
    import pathlib

    vus: dict[str, list[str]] = {}
    for chemin in sorted(
        list(pathlib.Path("mesure").glob("*.py")) + list(pathlib.Path("agents").glob("*.py"))
    ):
        arbre = ast.parse(chemin.read_text(encoding="utf-8"))
        for noeud in ast.walk(arbre):
            if not isinstance(noeud, ast.Call):
                continue
            for motcle in noeud.keywords:
                if motcle.arg != "intitule":
                    continue
                cle = _cle_d_un_intitule(motcle.value, chemin)
                if cle is not None:
                    vus.setdefault(cle, []).append(f"{chemin}:{motcle.value.lineno}")
    # **Elle doit avoir trouve des intitules, sinon elle ne garde rien.** Un `glob` qui ne
    # ramene plus rien, un mot-cle renomme, et cette parade reste verte en n'inspectant plus
    # aucun fichier -- c'est la seconde facon dont une garde cesse silencieusement de garder,
    # apres celle de ne couvrir qu'une forme syntaxique.
    assert len(vus) >= 5, (
        f"la parade n'a trouve que {len(vus)} intitule(s) dans tout `mesure/` et `agents/` : "
        f"elle n'inspecte plus ce qu'elle croit inspecter"
    )
    doublons = {nom: ou for nom, ou in vus.items() if len(ou) > 1}
    assert not doublons, (
        "deux campagnes portent le meme intitule, donc deux populations differentes se "
        f"liraient comme une seule : {doublons}"
    )


def test_la_parade_des_intitules_ATTRAPE_le_contournement_par_APPEL(tmp_path):
    """**Elle mord, et sur le contournement precis que l'auditeur a construit.**

    Une parade qui n'a jamais ete vue tomber ne protege rien. Ce cas lui donne les deux formes
    du meme nom -- le litteral et l'appel qui le produit -- et exige qu'elle les rapproche.
    Sans l'evaluation de l'appel, les deux cles differeraient et le doublon passerait : c'est
    exactement ce que faisait la version du tour 2.
    """
    import ast

    from agents import campagne as campagne_module

    source = (
        "from agents.campagne import intitule_du_garde_fou\n"
        "a = Campagne(intitule=intitule_du_garde_fou())\n"
        f"b = Campagne(intitule={campagne_module.intitule_du_garde_fou()!r})\n"
    )
    arbre = ast.parse(source)
    cles = [
        _cle_d_un_intitule(motcle.value, Path("agents/campagne.py"))
        for noeud in ast.walk(arbre)
        if isinstance(noeud, ast.Call)
        for motcle in noeud.keywords
        if motcle.arg == "intitule"
    ]
    assert len(cles) == 2, cles
    assert cles[0] == cles[1], (
        f"l'appel rend {cles[0]!r} et le litteral {cles[1]!r} : la parade ne les rapproche "
        f"pas, et redonner le nom du garde-fou par appel la traverserait"
    )


def test_la_parade_des_intitules_ATTRAPE_AUSSI_l_appel_QUALIFIE(tmp_path):
    """**Reserve 3 de la phase 3, levee avec sa parade et non avec son seul rendu.**

    ETABLIT : un appel qualifie `module.fonction()` et le litteral qu'il produit rendent la
    MEME cle, donc un doublon entre les deux fait tomber la parade.

    POPULATION : les trois formes du meme nom -- le litteral, l'appel nu, l'appel qualifie --
    lues dans une source construite pour ce cas.

    Le cas frere juste au-dessus tient l'appel **nu**, celui qu'un `from ... import` produit.
    Il ne dit rien de l'appel **qualifie**, et c'est celui-la que le depot ecrit :
    `mesure/phase3_mesure.py:887` est le seul appel a `intitule_du_garde_fou` hors des tests,
    et il est ecrit `campagne_module.intitule_du_garde_fou()`. **La parade laissait donc passer
    la seule forme qu'elle avait a garder.**

    C'est la deuxieme fois que cette parade est prise sur une forme syntaxique qu'elle ne
    voyait pas -- le tour 2 ne lisait que les litteraux. La lecon n'est pas « il fallait penser
    a celle-la » : c'est qu'une parade syntaxique doit etre eprouvee sur **le style reel du
    depot**, pas sur la forme que son auteur avait en tete.
    """
    import ast

    from agents import campagne as campagne_module

    attendu = campagne_module.intitule_du_garde_fou()
    source = (
        "from agents import campagne as campagne_module\n"
        "from agents.campagne import intitule_du_garde_fou\n"
        "a = Campagne(intitule=campagne_module.intitule_du_garde_fou())\n"
        "b = Campagne(intitule=intitule_du_garde_fou())\n"
        f"c = Campagne(intitule={attendu!r})\n"
    )
    # La source est ECRITE sur le disque et c'est ce fichier-la qui est passe a la parade :
    # les alias se lisent dans les imports du fichier ou l'appel est ecrit, donc la source et
    # le chemin doivent etre le meme objet -- comme ils le sont lors du balayage du depot.
    faux = tmp_path / "faux_module_de_mesure.py"
    faux.write_text(source, encoding="utf-8")

    arbre = ast.parse(source)
    # Indexe par la VARIABLE affectee : `ast.walk` est un parcours en largeur et ne rend pas
    # les appels dans l'ordre de la source.
    cles: dict[str, str | None] = {}
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, ast.Assign):
            continue
        for motcle in noeud.value.keywords:
            if motcle.arg == "intitule":
                cles[noeud.targets[0].id] = _cle_d_un_intitule(motcle.value, faux)

    assert set(cles) == {"a", "b", "c"}, cles
    assert cles["a"] == attendu, (
        f"l'appel QUALIFIE rend {cles['a']!r} au lieu de {attendu!r} : redonner le nom du "
        f"garde-fou sous cette forme traverse la parade -- et c'est la forme que le depot ecrit"
    )
    assert cles["a"] == cles["b"] == cles["c"], (
        f"les trois formes du meme nom ne se rapprochent pas : {cles}"
    )


def test_la_parade_des_intitules_voit_le_SEUL_appel_du_depot_hors_des_tests():
    """ETABLIT : l'appel a `intitule_du_garde_fou` ecrit dans `mesure/` est resolu, pas transcrit.

    POPULATION : tous les arguments `intitule=` de `mesure/*.py` et `agents/*.py` qui sont des
    APPELS -- c'est-a-dire, aujourd'hui, `mesure/phase3_mesure.py:887`.

    Le cas precedent travaille sur une source fabriquee ; celui-ci travaille sur le depot. Sans
    lui, la parade pourrait etre elargie a une forme que le depot n'ecrit pas, et personne ne
    le verrait. **Il tombe si le depot se met a ecrire un appel que la parade ne resout pas**,
    ce qui est exactement l'evenement qui a produit la reserve 3.
    """
    import ast
    import pathlib

    appels: list[tuple[str, str | None]] = []
    for chemin in sorted(
        list(pathlib.Path("mesure").glob("*.py")) + list(pathlib.Path("agents").glob("*.py"))
    ):
        arbre = ast.parse(chemin.read_text(encoding="utf-8"))
        for noeud in ast.walk(arbre):
            if not isinstance(noeud, ast.Call):
                continue
            for motcle in noeud.keywords:
                if motcle.arg != "intitule" or not isinstance(motcle.value, ast.Call):
                    continue
                appels.append(
                    (
                        f"{chemin}:{motcle.value.lineno}",
                        _cle_d_un_intitule(motcle.value, chemin),
                        ast.unparse(motcle.value),
                    )
                )

    assert appels, (
        "aucun intitule construit par APPEL dans le depot : ce cas n'inspecte plus rien, et "
        "la parade des appels qualifies n'est plus eprouvee sur du code reel"
    )
    # « Transcrit » se reconnait a l'EGALITE avec le texte source. Un test de forme -- une
    # parenthese finale, par exemple -- se tromperait ici : l'intitule resolu finit lui-meme
    # par « (garde-fou) ».
    non_resolus = [
        (ou, cle) for ou, cle, source in appels if cle is None or cle == source
    ]
    assert not non_resolus, (
        f"{len(non_resolus)} appel(s) `intitule=` du depot ne sont pas RESOLUS mais transcrits "
        f"tels quels : {non_resolus}. Un intitule transcrit ne se rapproche d'aucun litteral, "
        f"donc un doublon avec lui traverse la parade."
    )


def test_l_audit_complet_separe_les_EPROUVES_des_RELEVES():
    """« Dix controles, aucun en echec » comptait deux controles qui ne pouvaient pas tomber."""
    mesure = _mesure()
    base = phase3_mesure.ligne_de_base_trois_greedys_un_siege(donnes=8)
    comparaisons = phase3_mesure.comparer(
        mesure.comportements, base, mesure.nb_parties, 24, budget=24
    )
    controles = audit.auditer(
        mesure=mesure,
        campagne=mesure.campagne,
        pool=[mesure],
        comparaisons=comparaisons,
        base=base,
        nb_parties_base=24,
        donnes_calibration=8,
        donnes_pool=500,
        nb_checkpoints=8,
        parties_entrainement=1_800_000,
    )
    assert len(controles) == 10
    assert {c.statut for c in controles} <= set(audit.STATUTS)
    eprouves = [c for c in controles if c.eprouve]
    releves = [c for c in controles if not c.eprouve]
    assert len(eprouves) == 8, [c.code for c in eprouves]
    assert {c.code for c in releves} == {"R4", "R5"}, [c.code for c in releves]


def test_un_statut_inconnu_est_refuse():
    """Un troisieme degre de reussite invente en passant ne doit pas s'installer."""
    import pytest

    with pytest.raises(ValueError, match="statut"):
        audit.Controle(code="Q1", intitule="x", statut="presque", preuve="1")
