"""L'outil de mutation, eprouve. **Il n'avait aucun cas, et c'est lui qui juge la suite.**

Ce qui a rendu ce module necessaire, le 23/08/2026 : le releve d'etape 0 de la phase 4 a ete
commite avec un document qu'un cas de la suite exigeait de nommer. La suite est passee au
rouge, et `outillage/mutation.py` n'a **aucun moyen de le savoir** -- il ecrivait `detectee`
des que `rouges` etait non nul, sans jamais mesurer le rouge preexistant.

Une campagne rejouee sur ce depot aurait rendu **56 detectees, 0 survivante, 1 expiree** : un
feu vert integral et faux, sur l'instrument meme qui venait de publier onze survivantes.

Les cas ci-dessous ne rejouent aucune suite -- ils couteraient 169 s chacun. Ils exercent les
**invariants** de l'outil, ceux dont la violation rend un releve faux sans rien lever.
"""

from __future__ import annotations

import ast
import subprocess
from collections import Counter

import pytest

from outillage.mutation import (
    FICHIERS_EXEMPTS,
    MUTATIONS,
    RACINE,
    refus_de_la_passe_de_base,
    refus_si_head_a_bouge,
    tombes_sous_TOUTES_les_mutations,
)


def _source_commitee(fichier: str) -> str:
    """Le contenu du fichier **tel que HEAD le porte**, jamais celui du disque.

    **Ce detour corrige un defaut que ces cas ont porte le 23/08/2026, et il vaut d'etre
    raconte parce qu'il est ne dans une correction.**

    Les deux cas ci-dessous verifient des invariants du CATALOGUE : « ce motif apparait
    exactement une fois dans sa source », « cette version mutee reste du Python valide ».
    Ecrits contre le disque, ils tombent des qu'une mutation est appliquee -- `_appliquer`
    REMPLACE `avant` par `apres`, donc le fichier ne contient plus le motif cherche.

    Or `outillage/mutation.py` joue la suite ENTIERE avec la mutation en place. Ces deux cas
    tombaient donc **sur les 56 mutations a la fois**, et la campagne rejouee a rendu
    **56 detectees, 0 survivante** : exactement `+2 rouges` sur chaque ligne, sans exception,
    et les onze survivantes reelles effacees.

    **C'est le mode de defaillance que la passe de base venait de fermer, refait par la
    correction elle-meme.** La passe de base ne pouvait pas le voir : elle mesure le zero
    AVANT la premiere mutation, et ces deux cas sont verts tant qu'aucune n'est en place.

    La source commitee est la bonne population : `principal` refuse de tourner sur un depot
    sale et restaure par `git checkout`, donc **HEAD est l'etat pristine par construction**.
    L'invariant porte sur le catalogue contre le depot, pas contre un fichier momentanement
    mute.
    """
    return subprocess.run(
        ["git", "show", f"HEAD:{fichier}"],
        cwd=RACINE,
        capture_output=True,
        text=True,
        check=True,
    ).stdout

# ---------------------------------------------------------------------------------
# La passe de base -- la regle qui refuse de lire un ecart contre un zero inconnu
# ---------------------------------------------------------------------------------


def test_une_passe_de_base_VERTE_laisse_la_campagne_commencer():
    """Etablit : sur `(1172 verts, 0 rouge)`, l'outil ne refuse pas. Population : la passe
    de base d'un depot sain."""
    assert refus_de_la_passe_de_base(1172, 0, len(MUTATIONS)) is None


def test_une_passe_de_base_ROUGE_ARRETE_la_campagne():
    """Etablit : sur `(1171 verts, 1 rouge)` -- l'etat exact du depot le 23/08/2026 --,
    l'outil refuse et nomme la consequence. Population : la passe de base d'un depot casse.

    **C'est le cas qui empeche le defaut de se refaire.** Sans lui, la regle vit dans le corps
    de `principal`, qui joue 57 passes de 169 s : personne ne peut l'exercer.
    """
    refus = refus_de_la_passe_de_base(1171, 1, len(MUTATIONS))
    assert refus is not None, (
        "un seul rouge preexistant suffit a faire sortir les 57 mutations `detectee` : "
        "l'outil doit refuser de commencer, pas rapporter une suite parfaite"
    )
    assert "ROUGE" in refus and str(len(MUTATIONS)) in refus, refus


def test_une_cible_qui_ne_collecte_RIEN_arrete_aussi_la_campagne():
    """Etablit : `(0 vert, 0 rouge)` est refuse. Population : une cible pytest vide.

    Un zero-zero passe le test « pas de rouge » et ne mesure rien du tout : les mutations
    seraient toutes lues contre une suite vide, et sortiraient toutes survivantes. C'est le
    symetrique du cas precedent -- l'autre facon dont un instrument ment sans lever.
    """
    assert refus_de_la_passe_de_base(0, 0, len(MUTATIONS)) is not None


# ---------------------------------------------------------------------------------
# Les invariants du catalogue -- ce qui rend un releve lisible
# ---------------------------------------------------------------------------------


def test_chaque_motif_apparait_EXACTEMENT_une_fois_dans_son_fichier():
    """Etablit : les 57 `avant` sont uniques dans leur fichier. Population : le catalogue.

    `_appliquer` leve deja sur ce cas, mais **en pleine campagne**, apres avoir joue les
    mutations precedentes. Le verifier ici le fait tomber en une seconde au lieu d'une heure.
    """
    comptes = {m.nom: _source_commitee(m.fichier).count(m.avant) for m in MUTATIONS}
    fautifs = {nom: c for nom, c in comptes.items() if c != 1}
    assert not fautifs, (
        f"un motif qui n'apparait pas exactement une fois ne designe pas la ligne qu'il "
        f"croit muter : {fautifs}"
    )


def test_chaque_version_mutee_reste_du_PYTHON_VALIDE():
    """Etablit : les 57 textes mutes se parsent. Population : le catalogue.

    **Sans ce cas, une « detection » peut n'etre qu'une `SyntaxError`** : la suite entiere
    tombe a la collecte, l'outil compte des rouges, et le releve porte `detectee` sur une
    mutation qui n'a jamais rien exerce. Le chiffre serait juste et la conclusion fausse.
    """
    fautifs = []
    for mutation in MUTATIONS:
        source = _source_commitee(mutation.fichier)
        mute = source.replace(mutation.avant, mutation.apres)
        assert mute != source, f"{mutation.nom} ne change rien"
        try:
            ast.parse(mute)
        except SyntaxError as erreur:
            fautifs.append(f"{mutation.nom} : {erreur}")
    assert not fautifs, "versions mutees invalides :\n  " + "\n  ".join(fautifs)


def test_les_noms_de_mutation_sont_deux_a_deux_distincts():
    """Etablit : aucun doublon parmi les 57 noms. Population : le catalogue.

    `--nom` et `--noms` selectionnent par le nom, et le releve s'y indexe : deux mutations
    homonymes rendraient deux verdicts sous une seule ligne.
    """
    doublons = {n: c for n, c in Counter(m.nom for m in MUTATIONS).items() if c > 1}
    assert not doublons, doublons


def test_aucune_mutation_ne_vise_l_ETALON():
    """Etablit : `agents/greedy.py` porte 0 mutation. Population : le catalogue.

    C'est le §0.3 du protocole, et le seul invariant que la regle du perimetre protegeait :
    un agent de reference se documente au lieu de se corriger, et le muter deplacerait la
    ligne de base a laquelle toutes les phases se comparent.
    """
    vises = [m.nom for m in MUTATIONS if m.fichier in FICHIERS_EXEMPTS]
    assert not vises, (
        f"ces mutations visent un fichier exempt ({sorted(FICHIERS_EXEMPTS)}) : {vises}"
    )


def test_chaque_mutation_vise_un_fichier_QUI_EXISTE():
    """Etablit : les 57 chemins existent. Population : le catalogue.

    Un fichier renomme laisse une mutation qui ne s'applique plus ; `_appliquer` leverait,
    mais seulement quand la campagne y arrive.

    **Celui-ci lit le disque, et c'est correct** : une mutation en place ne fait pas
    disparaitre son fichier, donc il est insensible a l'etat mute. Voir `_source_commitee`
    pour ce que cette distinction a coute.
    """
    absents = [m.nom for m in MUTATIONS if not (RACINE / m.fichier).is_file()]
    assert not absents, absents


@pytest.mark.parametrize("mutation", MUTATIONS, ids=lambda m: m.nom)
def test_chaque_mutation_dit_ce_qu_elle_vise(mutation):
    """Etablit : chaque mutation porte un `vise` non vide. Population : le catalogue.

    Une mutation sans `vise` qui survit nomme un trou que personne ne peut lire.
    """
    assert mutation.vise.strip(), f"{mutation.nom} ne dit pas ce qu'elle casse"


# ---------------------------------------------------------------------------------
# Le detecteur de miroir -- ce qui aurait vu le defaut du 23/08/2026
# ---------------------------------------------------------------------------------


def test_un_test_qui_tombe_sous_TOUTES_les_mutations_est_signale():
    """Etablit : l'intersection des tests tombes est rendue. Population : trois passes dont
    un test commun.

    **C'est le cas du defaut reel.** Le 23/08/2026, deux cas de ce fichier meme lisaient le
    disque pour verifier les invariants du catalogue ; sous mutation le motif n'y est plus,
    les deux tombaient, et la campagne a rendu 56 detectees / 0 survivante au lieu de
    45 / 11. Un test qui tombe sous toutes les mutations ne reagit a aucune d'elles.
    """
    miroirs = tombes_sous_TOUTES_les_mutations(
        [
            frozenset({"t::miroir", "t::vrai_a"}),
            frozenset({"t::miroir", "t::vrai_b"}),
            frozenset({"t::miroir"}),
        ]
    )
    assert miroirs == frozenset({"t::miroir"}), miroirs


def test_des_detections_LEGITIMES_ne_sont_pas_signalees():
    """Etablit : sans test commun, rien n'est signale. Population : deux passes disjointes.

    **Le controle doit pouvoir NE PAS se declencher.** Un detecteur qui signale toujours ne
    signale rien -- c'est la meme faute que le garde-fou de portee 1 de la phase 3.
    """
    assert not tombes_sous_TOUTES_les_mutations(
        [frozenset({"t::a"}), frozenset({"t::b"})]
    )


def test_le_detecteur_de_miroir_ne_leve_pas_sur_ZERO_passe():
    """Etablit : sur aucune passe, l'ensemble vide. Population : le cas degenere.

    L'intersection de rien n'est pas definie ; rendre l'ensemble vide est la seule reponse
    qui ne fabrique pas un signalement a partir d'une absence de mesure.
    """
    assert tombes_sous_TOUTES_les_mutations([]) == frozenset()


# ---------------------------------------------------------------------------------
# La parade STATIQUE : quels tests lisent la source d'un fichier mute
# ---------------------------------------------------------------------------------

#: Les sites de lecture de source connus, **nommes**, avec ce qui les rend inoffensifs.
#:
#: **Pourquoi une liste et pas un compte.** Un test qui lit la source d'un fichier mute peut
#: tomber parce que le fichier a ete EDITE, et non parce que son comportement a change. Un tel
#: test se deguise en detection et efface des survivantes du releve -- c'est ce qui est arrive
#: le 23/08/2026. Ni la passe de base ni `tombes_sous_TOUTES_les_mutations` ne le voient : la
#: premiere mesure avant toute mutation, le second ne voit que ce qui tombe sous les 57, et un
#: test sensible a UN fichier ne tombe que sous les mutations de ce fichier.
#:
#: Les temoins de `outillage.mutation` couvrent la population des 20 fichiers mutes. Cette
#: liste-ci couvre autre chose et ne coute aucune passe : elle oblige **celui qui ajoute un
#: site de lecture** a dire pourquoi il est inoffensif, au moment ou il l'ajoute. C'est la
#: seule des deux qui attrape un couple **avant** qu'une campagne de deux heures ne le
#: rencontre.
#:
#: Chaque entree : `(fichier de test, ce qu'il lit, pourquoi il ne reagit pas a l'edition)`.
SITES_DE_LECTURE_DE_SOURCE: tuple[tuple[str, str, str], ...] = (
    (
        "tests/agents/test_aveuglement_reseau.py",
        "agents/reseau.py",
        "cherche des NOMS interdits dans la source -- `vue_privilegiee`, `State` -- pour "
        "etablir l'aveuglement. Un commentaire ajoute n'en introduit aucun ; et une mutation "
        "qui en introduirait un DOIT le faire tomber, c'est le but de ce cas.",
    ),
    (
        "tests/audit_phase2/test_reverification.py",
        "mesure/comportements.py",
        "cherche la presence d'un motif de definition dans la source ; l'ajout d'une ligne "
        "ne retire aucun motif, donc il est insensible a l'edition.",
    ),
    (
        "tests/mesure/test_phase3_audit.py",
        "agents/*.py (glob)",
        "parse l'AST et ne lit que les mots-cles `intitule=` ; un commentaire est invisible "
        "a `ast.parse`. **Site le plus large du depot avec le suivant : 14 des 20 fichiers "
        "mutes, 37 des 57 mutations.**",
    ),
    (
        "tests/mesure/test_phase3_audit.py",
        "mesure/*.py (glob)",
        "meme site, second repertoire : AST et mots-cles `intitule=` seulement, donc "
        "insensible aux commentaires et aux numeros de ligne.",
    ),
    (
        "tests/mesure/test_phase3_audit.py",
        "agents/campagne.py",
        "le chemin sert a RESOUDRE un module pour en appeler une fonction "
        "(`_cle_d_un_intitule`), pas a lire la source : c'est l'import qui porte le "
        "comportement, et un commentaire ajoute n'en change aucun.",
    ),
    (
        "tests/outillage/test_mutation.py",
        "git show HEAD: -- les 20 fichiers mutes",
        "lit la source COMMITEE et non le disque, donc l'etat mute lui est invisible **par "
        "construction** -- c'est la correction du defaut du 23/08/2026, ou deux cas lisant "
        "le disque tombaient sous les 56 mutations et effacaient onze survivantes.",
    ),
)


def _sites_de_lecture_trouves() -> set[tuple[str, str]]:
    """Les couples `(test, cible)` reellement presents dans `tests/`, par lecture de l'AST.

    Un module compte comme site s'il lit une source -- `read_text`, `read_bytes`, `ast.parse`,
    `inspect.getsource`, `git show` -- **et** designe un fichier mute.

    **Les chaines de `SITES_DE_LECTURE_DE_SOURCE` elle-meme sont exclues**, et c'est necessaire
    plutot que commode : la liste NOMME les fichiers dont elle parle, donc un scan naif la lit
    comme un site pour chacun d'eux. Ce serait un compteur qui compte sa propre declaration --
    exactement le motif que le §0.2 nomme « un test qui verifie la coherence entre deux sorties
    du meme calcul ne teste rien ». L'exclusion porte sur les NŒUDS de cette affectation, pas
    sur le fichier : le reste de ce module reste inspecte comme les autres.
    """
    import pathlib

    mutes = sorted({m.fichier for m in MUTATIONS})
    dossiers = sorted({f.split("/")[0] for f in mutes})
    verbes = {"read_text", "read_bytes", "getsource"}

    trouves: set[tuple[str, str]] = set()
    for chemin in sorted(pathlib.Path("tests").rglob("*.py")):
        texte = chemin.read_text(encoding="utf-8")
        arbre = ast.parse(texte)
        nom = str(chemin).replace("\\", "/")

        exclus: set[int] = set()
        for noeud in ast.walk(arbre):
            cible_nommee = (
                isinstance(noeud, ast.AnnAssign)
                and isinstance(noeud.target, ast.Name)
                and noeud.target.id == "SITES_DE_LECTURE_DE_SOURCE"
            ) or (
                isinstance(noeud, ast.Assign)
                and any(
                    isinstance(c, ast.Name) and c.id == "SITES_DE_LECTURE_DE_SOURCE"
                    for c in noeud.targets
                )
            )
            if cible_nommee:
                exclus |= {id(sous) for sous in ast.walk(noeud)}

        lit = any(
            isinstance(n, ast.Attribute) and n.attr in verbes for n in ast.walk(arbre)
        ) or "git show" in texte or "ast.parse" in texte
        if not lit:
            continue

        for noeud in ast.walk(arbre):
            if (
                isinstance(noeud, ast.Constant)
                and isinstance(noeud.value, str)
                and noeud.value in mutes
                and id(noeud) not in exclus
            ):
                trouves.add((nom, noeud.value))
            # `Path("agents").glob("*.py")` : un site qui couvre tout un repertoire.
            if (
                isinstance(noeud, ast.Call)
                and isinstance(noeud.func, ast.Attribute)
                and noeud.func.attr in {"glob", "rglob"}
                and noeud.args
                and isinstance(noeud.args[0], ast.Constant)
                and noeud.args[0].value == "*.py"
                and isinstance(noeud.func.value, ast.Call)
                and noeud.func.value.args
                and isinstance(noeud.func.value.args[0], ast.Constant)
                and noeud.func.value.args[0].value in dossiers
            ):
                trouves.add((nom, f"{noeud.func.value.args[0].value}/*.py (glob)"))
        # `git show HEAD:` lit la source COMMITEE de tous les fichiers du catalogue.
        if "git show" in texte:
            trouves.add((nom, "git show HEAD: -- les 20 fichiers mutes"))
    return trouves


def test_tout_site_qui_lit_la_source_d_un_fichier_MUTE_est_inscrit():
    """Etablit : aucun site de lecture de source non inscrit. Population : `tests/**/*.py`.

    **Ce que ce cas empeche.** Ecrire un test qui lit `agents/reseau.py` depuis le disque est
    la pente naturelle quand on veut tenir un invariant de forme -- et c'est exactement ce qui
    a produit, le 23/08/2026, deux cas qui tombaient sous les 56 mutations a la fois et
    effacaient onze survivantes du releve.

    **Ce qu'il n'etablit PAS.** Il ne dit pas qu'un site inscrit est inoffensif : c'est la
    justification ecrite a cote qui l'affirme, et c'est un humain qui la relit. Il dit qu'aucun
    site n'est arrive sans que personne ne se pose la question. « Un compte se perime, une
    liste non. »
    """
    connus = {(test, cible) for test, cible, _ in SITES_DE_LECTURE_DE_SOURCE}
    trouves = _sites_de_lecture_trouves()
    assert trouves, (
        "aucun site de lecture trouve : le detecteur n'inspecte plus ce qu'il croit "
        "inspecter, et cette parade est devenue decorative"
    )
    nouveaux = trouves - connus
    assert not nouveaux, (
        f"des tests lisent la source d'un fichier MUTE sans etre inscrits : {sorted(nouveaux)}\n"
        f"Un tel test peut tomber parce que le fichier a ete EDITE, pas parce que son "
        f"comportement a change -- il se deguiserait alors en detection sur toutes les "
        f"mutations de ce fichier, et effacerait des survivantes du releve.\n"
        f"Inscris-le dans `SITES_DE_LECTURE_DE_SOURCE` avec, en une ligne, POURQUOI il ne "
        f"reagit pas a l'edition. Un compte se perime, une liste non."
    )


def test_la_liste_des_sites_de_lecture_ne_PERIME_pas():
    """Etablit : aucun site inscrit n'a disparu. Population : `SITES_DE_LECTURE_DE_SOURCE`.

    Le symetrique du cas precedent, et il ne fait pas double emploi. Une entree qui ne
    correspond plus a rien -- test supprime, lecture retiree -- laisse croire qu'une
    justification couvre un site qui n'existe plus, et masque le jour ou un site du meme nom
    revient sous une autre forme.
    """
    connus = {(test, cible) for test, cible, _ in SITES_DE_LECTURE_DE_SOURCE}
    disparus = connus - _sites_de_lecture_trouves()
    assert not disparus, (
        f"ces sites sont inscrits mais n'existent plus : {sorted(disparus)}. Retire-les, "
        f"sinon la liste decrit un depot qui n'est plus celui-ci."
    )


@pytest.mark.parametrize(
    "site", SITES_DE_LECTURE_DE_SOURCE, ids=lambda s: f"{s[0]}->{s[1]}"
)
def test_chaque_site_inscrit_DIT_pourquoi_il_est_inoffensif(site):
    """Etablit : chaque entree porte une justification substantielle. Population : la liste.

    Une liste de noms sans motif est un compte deguise : elle laisse passer l'inscription
    reflexe, qui est precisement la facon dont une parade devient decorative.
    """
    _, _, motif = site
    assert len(motif.strip()) > 40, f"justification trop courte pour {site[0]} : {motif!r}"


# ---------------------------------------------------------------------------------
# HEAD qui bouge pendant une campagne -- le defaut du 24/08/2026
# ---------------------------------------------------------------------------------


def test_un_HEAD_qui_a_bouge_ARRETE_la_campagne():
    """Etablit : deux SHA differents produisent un refus. Population : le controle de derive.

    **Le cas du defaut reel.** Le 24/08/2026 a 08:11, un commit est tombe pendant la campagne
    alors que `courtisans/infoset.py` portait la mutation `espions-adverses-visibles`. Le
    commit l'a avalee ; `_restaurer` a fait `git checkout -- <fichier>`, **qui restaure vers
    HEAD**, donc vers la version mutee. La mutation est devenue permanente, l'invariant I7 a
    saute, et les 56 mutations suivantes ont tourne sur un moteur casse -- zero survivante,
    campagne a jeter.
    """
    refus = refus_si_head_a_bouge("a" * 40, "b" * 40)
    assert refus is not None
    assert "HEAD a bouge" in refus, refus


def test_un_HEAD_IMMOBILE_laisse_la_campagne_continuer():
    """Etablit : deux SHA identiques ne produisent aucun refus. Population : le cas nominal.

    Un controle qui refuse toujours ne controle rien.
    """
    assert refus_si_head_a_bouge("a" * 40, "a" * 40) is None


def test_la_restauration_se_fait_depuis_le_SHA_FIGE_et_non_depuis_HEAD():
    """Etablit : `_restaurer` accepte un SHA et le passe a git. Population : sa signature.

    C'est la parade qui **empeche** la contamination, la ou `refus_si_head_a_bouge` ne fait
    que la **detecter**. Il faut les deux : la detection arrive au tour suivant, quand le mal
    est fait.
    """
    import inspect

    from outillage import mutation as module

    parametres = inspect.signature(module._restaurer).parameters
    assert "sha" in parametres, (
        "`_restaurer` ne prend pas de SHA : il restaurerait vers HEAD, et un HEAD qui a avale "
        "une mutation la rendrait permanente"
    )
    source = inspect.getsource(module._restaurer)
    assert '"git", "checkout", sha' in source, source
