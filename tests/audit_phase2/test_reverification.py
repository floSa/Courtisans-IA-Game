"""Re-verification du tour 2 : les sept points listes, et rien au-dela.

Chaque cas ci-dessous tient **une** affirmation du constructeur. Aucun ne cherche un front
nouveau : le protocole d'audit croise l'interdit a l'etape 6 du cycle.
"""

from __future__ import annotations

import pathlib
import random
from math import ceil

import pytest

from audit.phase2.stats import _phi_inverse, clopper_pearson
from courtisans.cards import Role
from mesure import comportements as comp
from mesure import phase2
from mesure.instance import ENTRAINEMENT_3J as CONFIG

PARTIES_CAMPAGNE = 10_002


def _compte(nom: str, succes: int, total: int, grain: str) -> comp.Compte:
    """Un `Compte` fabrique, pour eprouver une garde sans jouer de partie."""
    return comp.Compte(nom, succes, total, grain, comp.VUE_DECIDEUR)


# ---------------------------------------------------------------------------------
# Point 1 -- la parade de grain, ses deux branches, et la levee reellement couverte
# ---------------------------------------------------------------------------------


def test_p1_le_grain_distingue_un_siege_de_trois():
    """Les deux libelles etaient **identiques** avant : une parade textuelle n'aurait rien vu.

    C'est le point qui rend la correction reelle plutot que cosmetique : la garde ne peut
    fonctionner que si le grain porte le nombre de sieges agreges.
    """
    un = _compte("B1-motif-par-partie", 1, 2, "parties (au moins un des 1 sieges mesures)")
    trois = _compte(
        "B1-motif-par-partie", 1, 2, "parties (au moins un des 3 sieges mesures)"
    )
    assert un.grain != trois.grain


@pytest.mark.parametrize("garde", [comp.ecart_de_taux, comp.cumuler])
def test_p1_les_deux_gardes_levent_sur_des_grains_differents(garde):
    """`ecart_de_taux` **et** `cumuler` : les deux endroits ou deux grains se rencontrent."""
    un = _compte("X-par-partie", 5, 10, "parties (au moins un des 1 sieges mesures)")
    trois = _compte("X-par-partie", 7, 10, "parties (au moins un des 3 sieges mesures)")
    with pytest.raises(comp.GrainsIncomparables):
        garde(un, trois)


@pytest.mark.parametrize("garde", [comp.ecart_de_taux, comp.cumuler])
def test_p1_les_deux_gardes_passent_sur_le_meme_grain(garde):
    """L'autre branche. Une garde qui leve toujours interdirait la table entiere."""
    a = _compte("X", 5, 10, "parties")
    b = _compte("X", 7, 10, "parties")
    assert garde(a, b) is not None


def test_p1_un_denominateur_vide_ne_se_confond_pas_avec_un_grain_incomparable():
    """Les deux cas sont distincts et le restent : `None` d'un cote, une levee de l'autre.

    Les confondre ferait lire « pas comparable » la ou il faut lire « l'occasion ne s'est pas
    presentee », et reciproquement -- deux phrases qui ne decrivent pas le meme calcul.
    """
    vide = _compte("X", 0, 0, "parties")
    plein = _compte("X", 3, 10, "parties")
    assert comp.ecart_de_taux(vide, plein) is None
    assert comp.ecart_de_taux(plein, vide) is None


def test_p1_le_rapport_ne_porte_plus_les_cinq_ecarts_fabriques():
    """Les cinq lignes `-par-partie` du paragraphe 6 ne portent plus ni ecart ni budget."""
    texte = _rapport()
    debut = texte.index("## 6.")
    section = texte[debut : texte.index("###", debut)]
    lignes = [x for x in section.splitlines()
              if x.startswith("| `") and "-par-partie" in x]
    assert len(lignes) == 5
    for ligne in lignes:
        cellules = [c.strip() for c in ligne.strip("|").split("|")]
        assert cellules[4].startswith("non comparable"), ligne
        assert cellules[5].startswith("non comparable"), ligne
    assert "-23.97" not in section, "l'ecart de signe inverse est toujours publie"
    assert "grain" in section.lower(), "le paragraphe 6 doit nommer ce qui n'est pas comparable"


#: Le rapport livre. Nomme une fois : les cas ci-dessous et celui de l'encodage doivent
#: parler du meme fichier, sinon l'un pourrait garantir l'encodage d'un autre.
RAPPORT_LIVRE = pathlib.Path("mesure/resultats/phase2.md")


def _rapport() -> str:
    """Le rapport livre, decode en UTF-8 -- et **seulement** en UTF-8.

    Ce lecteur tolerait les deux encodages : il essayait UTF-8 puis retombait sur cp1252.
    C'etait un contournement du defaut mineur 2, pas une parade, et il avait un effet que
    personne n'avait voulu -- **il rendait la derive muette**. Un rapport regenere depuis une
    console cp1252 se serait relu sans bruit, et les 75 controles de l'audit auraient passe
    au vert sur un fichier qui n'etait pas dans l'encodage des quatre autres.

    La tolerance est retiree le 20/08/2026, en meme temps que le fichier est converti et que
    le generateur cesse de laisser la console decider (`mesure.phase2.main`, `--sortie`).
    """
    return RAPPORT_LIVRE.read_text(encoding="utf-8")


def test_le_rapport_livre_est_en_utf8_comme_les_quatre_autres_documents():
    """Defaut mineur 2 de la phase 2. Le cas qui **dit** la derive au lieu de la subir.

    Il ne se contente pas de decoder : decoder reussirait sur un rapport **purement
    ASCII**, qui n'etablirait rien -- cp1252 et UTF-8 coincident sur l'ASCII. Il exige donc
    qu'au moins un caractere non-ASCII soit present et se decode, ce qui distingue
    reellement les deux encodages. Les caracteres en cause sont MESURES : 36 `«`, 36 `»`,
    16 `œ` et 3 `è`.
    """
    octets = RAPPORT_LIVRE.read_bytes()
    texte = octets.decode("utf-8")  # leve si le rapport a rederive en cp1252

    non_ascii = [c for c in texte if ord(c) > 127]
    assert non_ascii, (
        "le rapport est purement ASCII : ce cas ne separe plus UTF-8 de cp1252, parce que "
        "les deux encodages coincident sur l'ASCII. Il faut le relire avant de le croire."
    )
    assert "«" in texte and "œ" in texte, (
        f"les caracteres attendus ont disparu du rapport : {sorted(set(non_ascii))}"
    )


#: Les documents de `mesure/`, **nommes**. Le releve du defaut mineur 2 disait « les quatre
#: autres documents » : il y en a **CINQ** en plus du rapport, et ce mecompte a ete trouve
#: par ce cas meme, en tombant a l'ecriture. C'est la faute que la phase 2 a commise cinq
#: fois -- un compte a la place d'une liste de noms -- et le releve du defaut la reproduisait.
DOCUMENTS_DE_MESURE: tuple[str, ...] = (
    "mesure/hypothese_et_instrument.md",
    "mesure/phase2_corrections_audit.md",
    "mesure/phase2_definitions_et_concurrentes.md",
    "mesure/phase2_entree_de_journal.md",
    "mesure/phase2_hypothese_et_instrument.md",
    # Ajoutes les 20 et 21/08/2026 : les trois documents de la phase 3. Ils sont inscrits ici
    # par leur NOM au moment ou ils sont ecrits, ce qui est precisement ce que la liste sert a
    # forcer -- le releve du defaut mineur 2 disait « les quatre autres documents » quand il y
    # en avait cinq, et c'est ce cas qui l'a trouve, en tombant a l'ecriture.
    "mesure/phase3_entree_de_journal.md",
    "mesure/phase3_hypothese_et_instrument.md",
    "mesure/resultats/phase2.md",
    "mesure/resultats/phase3.md",
    # Ajoute le 23/08/2026, etape 0 de la phase 4 : le releve du test de mutation.
    #
    # **Il a ete commite sans etre inscrit ici, et ce cas est tombe.** C'est exactement ce
    # pour quoi il existe -- et l'incident vaut mieux que la correction : le document non
    # inscrit etait le rapport qui publiait « 1 172 tests, 45 detections », produit par un
    # outil qui ne verifiait pas que la suite etait verte avant de commencer. Un seul rouge
    # preexistant aurait fait rapporter « 56 detectees, 0 survivante » a la campagne suivante.
    # Voir `outillage/mutation.py`, `_passe_de_base`.
    "mesure/resultats/phase4_mutations.md",
    # Ajoute le 24/08/2026 : le mode d'emploi des journaux bruts de la phase 4.
    #
    # **Il a fait tomber ce cas a son tour, et c'est la seconde fois en deux jours.** Un
    # document depose dans `mesure/` sans etre inscrit ici est un document que personne ne
    # nomme -- et celui-la porte les deux commandes qui permettent de recompter la
    # reproduction des 57 verdicts sans rejouer la campagne. Le cas ne demande pas qu'un
    # document soit important : il demande qu'il soit NOMME.
    "mesure/resultats/phase4_journaux/README.md",
    # Ajoute le 24/08/2026 : le releve de l'etape 0 ter, les neuf trous combles.
    "mesure/resultats/phase4_etape0ter.md",
    # Ajoute le 24/08/2026 : le releve de l'etape 0 bis, les trois reserves de la phase 3.
    "mesure/resultats/phase4_etape0bis.md",
    # Ajoute le 24/08/2026, etape 2 de l'iteration 1 : ou est le plafond du critique. Ecrit
    # AVANT tout entrainement, et avant la pre-inscription qui le suit.
    "mesure/resultats/phase4_le_plafond_du_critique.md",
)


def test_les_documents_de_mesure_sont_nommes_et_dans_le_meme_encodage():
    """« Les quatre autres sont en UTF-8 » est un compte : ce cas ecrit les NOMS.

    Deux assertions, et elles ne disent pas la meme chose. La premiere : **tout** document
    Markdown de `mesure/` se decode en UTF-8, y compris un document ajoute demain -- c'est
    la garantie. La seconde : la liste nommee ci-dessus est **exhaustive** -- c'est ce qui
    oblige celui qui ajoute un document a l'y inscrire, au lieu de laisser un compte se
    perimer en silence, comme le « quatre » du releve.

    **Ce cas s'appelait `test_les_neuf_documents_...`, et son propre nom portait un compte.**
    Il y en a dix depuis le 23/08/2026. Un cas ecrit pour imposer une liste de noms contre un
    compte s'etait donne un compte en guise de nom, et ce compte s'est perime comme tous les
    autres. Le nom ne dit plus combien il y en a : c'est la liste qui le dit, et elle est la
    seule a avoir le droit de le dire.
    """
    trouves = sorted(
        str(chemin)
        for chemin in list(pathlib.Path("mesure").rglob("*.md"))
    )

    fautifs = []
    for document in trouves:
        try:
            pathlib.Path(document).read_bytes().decode("utf-8")
        except UnicodeDecodeError as erreur:
            fautifs.append(f"{document} : {erreur}")
    assert not fautifs, "documents qui ne sont pas en UTF-8 :\n  " + "\n  ".join(fautifs)

    assert trouves == sorted(DOCUMENTS_DE_MESURE), (
        f"la liste nommee de `mesure/` n'est plus exhaustive.\n"
        f"  sur le disque : {trouves}\n"
        f"  dans la liste : {sorted(DOCUMENTS_DE_MESURE)}\n"
        f"Inscris le document manquant par son NOM. Un compte se perime, une liste non."
    )


# ---------------------------------------------------------------------------------
# Point 3 -- le plancher vaut pour M3 et pas pour M4, et il doit etre ecrit des TROIS
# ---------------------------------------------------------------------------------


def test_p3_les_compteurs_juges_par_l_evaluation_myope_sont_QUATRE_et_nommes():
    """La reserve du paragraphe 4 bis doit couvrir tous les compteurs qu'elle concerne.

    Le greedy est un plancher pour M3 -- un agent plus myope que sa specification est plus
    faible, donc le gain publie minore ce qu'un G-combine complet obtiendrait. Il ne l'est
    pas pour les compteurs B4 juges **par cette meme evaluation myope** : corriger
    l'incoherence deplacerait leur etalon, pas seulement leur valeur.

    **Le compte est faux.** Le paragraphe 4 bis ecrit « Trois compteurs de B4 sont juges par
    cette meme evaluation myope ». Le code en montre **quatre** : `b4` lit `decision.valeurs`
    -- produit par `evaluer_actions` -- pour `B4-strict`, `B4-departage`, `B4-contre-nature`
    **et** `B4-meurtre-couteux`. Les deux exclus, `B4-brut` et `B4-tout-dos`, ne lisent aucune
    valeur. Le quatrieme omis est justement l'un des deux zeros absolus du rapport.

    Et aucun des quatre n'est nomme : le lecteur est renvoye a la section 5. Un compte sans
    noms est ce que ce projet a appris a ne plus accepter.
    """
    concernes = ("B4-strict", "B4-departage", "B4-contre-nature", "B4-meurtre-couteux")
    source = pathlib.Path("mesure/comportements.py").read_text(encoding="utf-8")
    debut = source.index("def b4(")
    corps = source[debut : source.index("\ndef ", debut + 10)]
    # Les quatre se decident sur une comparaison de `decision.valeurs`, les deux autres non.
    assert corps.count("decision.valeurs") >= 1
    for exclu in ("B4-brut", "B4-tout-dos"):
        assert exclu not in concernes

    texte = _rapport()
    debut = texte.index("4 bis")
    section = texte[debut : texte.index("## 5", debut)]
    manquants = [c for c in concernes if c not in section]
    assert not manquants, (
        f"le paragraphe 4 bis annonce « Trois compteurs de B4 » et n'en nomme aucun ; "
        f"le code en concerne quatre, absents de la section : {manquants}"
    )


def test_p3_la_pre_inscription_n_est_pas_amendee():
    """Une pre-inscription qu'on reecrit apres la mesure ne pre-inscrit plus rien."""
    import subprocess

    diff = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "02ae24b",
            "72630a1",
            "--",
            "mesure/phase2_hypothese_et_instrument.md",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert diff.strip() == "", f"la pre-inscription a bouge : {diff!r}"


# ---------------------------------------------------------------------------------
# Point 4 -- « aveugle par le bas » est un calcul, et il porte sur les bonnes lignes
# ---------------------------------------------------------------------------------


def test_p4_le_critere_d_aveuglement_est_calcule_et_non_ecrit():
    """`Budget.aveugle_par_le_bas` doit valoir `detectable > taux`, calcule, pas redige."""
    aveugle = phase2.budget_d_un_compteur(
        _compte("B7-gaspillage", 61, 40_008, "poses au banquet"),
        PARTIES_CAMPAGNE,
        ecart=-0.0002,
    )
    assert aveugle.aveugle_par_le_bas is True
    assert aveugle.detectable is not None and aveugle.detectable > 61 / 40_008

    voyant = phase2.budget_d_un_compteur(
        _compte("B7-lumiere", 4_723, 40_008, "poses au banquet"),
        PARTIES_CAMPAGNE,
        ecart=-0.0164,
    )
    assert voyant.aveugle_par_le_bas is False


def test_p4_exactement_deux_lignes_du_paragraphe_6_sont_aveugles_par_le_bas():
    """Je recalcule le critere sur les 34 lignes avec MA formule, et j'en attends deux.

    Un critere calcule doit tomber sur les memes lignes qu'un calcul independant, sinon il
    est calcule mais pas juste.
    """
    texte = _rapport()
    debut = texte.index("## 6.")
    section = texte[debut : texte.index("###", debut)]
    lignes = [x for x in section.splitlines() if x.startswith("| `")]
    assert len(lignes) == 34

    marquees = {
        x.strip("|").split("|")[0].strip().strip("`")
        for x in lignes
        if "aveugle par le bas" in x
    }
    # Mon propre calcul : delta = (z_a + z_b) sqrt(2 p q / (budget x par_partie)).
    z = _phi_inverse(1 - 0.01 / 2) + _phi_inverse(0.80)
    miennes = set()
    for ligne in lignes:
        cellules = [c.strip() for c in ligne.strip("|").split("|")]
        nom = cellules[0].strip("`")
        if "**" in cellules[1]:
            continue  # taux nul : pas de detectable, une borne exacte a la place
        taux = float(cellules[1].rstrip(" %")) / 100
        par_partie = float(cellules[2])
        detectable = z * (2 * taux * (1 - taux) / (1000 * par_partie)) ** 0.5
        if detectable > taux:
            miennes.add(nom)
    assert miennes == marquees, f"mien {sorted(miennes)} contre marque {sorted(marquees)}"
    assert len(marquees) == 2


# ---------------------------------------------------------------------------------
# Point 5 -- la garde de campagne, scindee : composition ici, symetrie la
# ---------------------------------------------------------------------------------


def test_p5_la_composition_est_gardee_dans_la_campagne():
    """Une composition impossible se refuse a la construction de la campagne."""
    with pytest.raises(ValueError):
        phase2.campagne_b(donnes=1, nb_greedys=0)
    with pytest.raises(ValueError):
        phase2.campagne_b(donnes=1, nb_greedys=CONFIG.joueurs + 1)


def test_p5_trois_greedys_est_accepte_par_la_campagne_et_refuse_par_m3():
    """La garde confondait une mesure avec une phase : vrai de M3, faux de M4.

    Trois greedys n'ont pas de winrate relatif -- la symetrie donne un tiers -- mais leurs
    comportements se mesurent parfaitement. Refuser la composition entiere interdisait M4.
    """
    groupes = phase2.campagne_b(donnes=2, nb_greedys=CONFIG.joueurs)
    assert groupes, "la campagne doit accepter trois greedys, M4 en a besoin"
    with pytest.raises(ValueError):
        phase2.mesurer_m3(
            groupes, "trois greedys", random.Random(0), nb_greedys=CONFIG.joueurs
        )


def test_p5_le_parametre_de_symetrie_de_m3_est_obligatoire():
    """Un defaut le rendrait facultatif, et l'oublier ferait retomber dans la faute."""
    import inspect

    signature = inspect.signature(phase2.mesurer_m3)
    parametre = signature.parameters["nb_greedys"]
    assert parametre.default is inspect.Parameter.empty


# ---------------------------------------------------------------------------------
# Point 7 -- les six budgets, reconstruits avec MON denominateur par partie
# ---------------------------------------------------------------------------------

#: Les six lignes de la troisieme population : nom, (k, n) a trois greedys, (k, n) au hasard,
#: et le budget publie. Les comptes sont recopies du rapport, jamais recalcules par son code.
SIX_BUDGETS = (
    ("B1-collectif", 21_538, 30_006, 20_157, 30_006, 745),
    ("B1-collectif-par-partie", 9_327, 10_002, 8_990, 10_002, 1_295),
    ("B1-motif-par-partie", 8_254, 10_002, 7_191, 10_002, 299),
    ("B1-tentative-par-partie", 9_412, 10_002, 8_674, 10_002, 239),
    ("B1-strict-par-partie", 5_917, 10_002, 5_684, 10_002, 10_400),
    ("B1-savoir-commun-par-partie", 8_289, 10_002, 7_199, 10_002, 280),
)


@pytest.mark.parametrize("nom,k3,n3,kh,nh,publie", SIX_BUDGETS)
def test_p7_les_six_budgets_se_reconstruisent(nom, k3, n3, kh, nh, publie):
    """Le budget publie, refait avec mon quantile et **mon** denominateur par partie.

    L'unite est reconstruite **avant** la valeur : un compteur `-par-partie` rend un seul
    booleen par partie, quel que soit le nombre de sieges agreges, parce que l'agregation est
    dans son numerateur ; un compteur au grain du couple `(partie, siege)` en rend autant que
    de sieges mesures. Ce n'est qu'ensuite que je verifie que ce nombre egale `n / parties`.
    """
    par_partie = 1.0 if nom.endswith("-par-partie") else float(CONFIG.joueurs)
    assert par_partie == n3 / PARTIES_CAMPAGNE

    z = _phi_inverse(1 - 0.01 / 2) + _phi_inverse(0.80)
    taux = k3 / n3
    ecart = abs(k3 / n3 - kh / nh)
    effectif = (z / ecart) ** 2 * 2 * taux * (1 - taux)
    assert ceil(effectif / par_partie) == publie


def test_p7_l_invariant_rend_le_facteur_trois_impossible():
    """Un compteur `-par-partie` dont le denominateur n'est pas le nombre de parties leve."""
    with pytest.raises(ValueError, match="par-partie"):
        phase2.observations_par_partie(
            _compte("B1-motif-par-partie", 100, 30_006, "parties"), PARTIES_CAMPAGNE
        )
    # L'autre branche : le meme compteur au bon denominateur passe, et rend exactement 1.
    assert (
        phase2.observations_par_partie(
            _compte("B1-motif-par-partie", 100, 10_002, "parties"), PARTIES_CAMPAGNE
        )
        == 1.0
    )


def test_p7_un_nombre_de_parties_nul_est_refuse():
    """Un budget sans le nombre de parties qui l'a produit n'a pas de sens."""
    with pytest.raises(ValueError):
        phase2.observations_par_partie(_compte("X", 5, 10, "parties"), 0)


def test_p7_un_seul_site_calcule_un_budget():
    """Trois tables passent par `budget_d_un_compteur` ; aucune ne recalcule a cote.

    C'est la cause racine du defaut : trois sites deduisaient chacun leur denominateur.
    """
    import pathlib
    import re

    rapport = pathlib.Path("mesure/rapport_phase2.py").read_text(encoding="utf-8")
    for interdit in ("parties_pour_separer_un_taux", "ecart_de_taux_detectable"):
        assert not re.search(rf"\b{interdit}\(", rapport), (
            f"{interdit} est appele hors de budget_d_un_compteur"
        )
    assert rapport.count("budget_d_un_compteur(") >= 3


# ---------------------------------------------------------------------------------
# Point 6 -- la troisieme population, lue comme une premiere livraison
# ---------------------------------------------------------------------------------


def test_p6_le_perimetre_se_decide_sur_le_texte_de_la_definition():
    """« La definition nomme-t-elle un autre joueur ? » -- verifiable sur les docstrings.

    `B1-collectif` doit nommer un autre joueur ; `B4-tout-dos` et `B5-renfort`, non. Si l'un
    des deux exclus nommait un adversaire, le critere textuel designerait un perimetre plus
    large que celui qui a ete livre.
    """
    collectif = comp.motif_b1.__doc__ or ""
    assert "differents" in collectif or "n'importe quel" in collectif.lower()
    for exclu in (comp.b4, comp.b5):
        texte = (exclu.__doc__ or "").lower()
        assert "joueurs differents" not in texte
        assert "n'importe quel siege" not in texte


def test_p6_l_inclusion_de_b1_collectif_tient_a_trois_greedys():
    """`B1-collectif` majore `B1-motif` par construction. L'inclusion doit tenir ici aussi.

    Elle est deja tombee une fois -- `B1-collectif` valait exactement `B1-motif` quand un seul
    siege etait mesure. La troisieme population est precisement celle ou elle doit se voir.
    """
    texte = _rapport()
    debut = texte.index("5 bis")
    section = texte[debut : texte.index("## 6.", debut)]
    assert "21538/30006" in section
    # B1-motif au grain du couple, trois greedys : la ligne n'est pas dans 5 bis, mais
    # l'inclusion se lit sur les deux nombres publies au meme grain.
    assert "71.78" in section


def test_p6_m3_est_explicitement_declare_sans_objet_pour_cette_population():
    """« M3 n'a pas d'objet ici » doit etre ecrit **et** tenu par le code (point 5)."""
    texte = _rapport()
    debut = texte.index("5 bis")
    section = texte[debut : texte.index("## 6.", debut)]
    assert "M3 n'a pas d'objet" in section


def test_p6_les_deux_compteurs_exclus_sont_nommes_avec_leur_raison():
    """Un perimetre qui exclut sans nommer est un perimetre qu'on elargira sans le dire."""
    texte = _rapport()
    debut = texte.index("5 bis")
    section = texte[debut : texte.index("## 6.", debut)]
    assert "B4-tout-dos" in section
    assert "B5-renfort" in section


# ---------------------------------------------------------------------------------
# Point 2 -- le zero exact de B1, et la premisse assertee
# ---------------------------------------------------------------------------------


def test_p2_la_partie_construite_finit_exactement_indifferente():
    """La premisse du test du constructeur doit etre assertee, pas supposee.

    Un cas « exactement Indifferente » qui finirait en Obscurite passerait sous les deux
    lectures et ne separerait rien. Je verifie que son propre test asserte la premisse.
    """
    import pathlib

    source = pathlib.Path("tests/mesure/test_comportements.py").read_text(encoding="utf-8")
    debut = source.index("def test_b1_compte_une_famille_qui_finit_EXACTEMENT_indifferente")
    corps = source[debut : debut + 3000]
    assert "INDIFFERENTE" in corps.upper()
    assert "B1-motif" in corps and "B1-strict" in corps


def test_p2_le_role_assassin_existe_bien_dans_l_instance():
    """Garde-fou de mes propres cas : l'instance de la phase 2 porte les cinq roles."""
    assert Role.ASSASSIN in CONFIG.roles
    assert len(CONFIG.roles) == 5


# ---------------------------------------------------------------------------------
# Un chiffre que je dois, et qui ferme le seul point reste ouvert
# ---------------------------------------------------------------------------------


def test_mon_7_33_pourcent_et_le_sien_mesurent_deux_populations():
    """Les deux intervalles se recouvrent des que la population est nommee.

    MESURE par `audit.phase2.coherence_horizon` sur 3 400 donnes : trois greedys 287/4145
    = 6,92 %, IC99 [5,95 ; 8,00] ; un greedy contre deux uniformes 204/4145 = 4,92 %,
    IC99 [4,10 ; 5,85]. Son chiffre, 4,23 % sur 4 063 nœuds, tombe dans le second intervalle
    et pas dans le premier. Le denominateur est le meme, la population ne l'etait pas -- et
    c'est mon chiffre qui etait mal etiquete.
    """
    trois = clopper_pearson(287, 4145, 0.01)
    un = clopper_pearson(204, 4145, 0.01)
    assert trois[0] <= 0.0733 <= trois[1], "mon 7,33 % doit tomber dans la population a trois"
    assert un[0] <= 0.0492 <= un[1]
    assert not (un[0] <= 0.0733 <= un[1]), "les deux populations doivent bien differer"
    sien = clopper_pearson(172, 4063, 0.01)  # 4,23 % de 4 063, arrondi au plus proche
    assert sien[0] <= un[1] and un[0] <= sien[1], "les deux intervalles doivent se recouvrir"


def test_la_main_d_un_siege_ne_depend_pas_de_la_politique():
    """Ce qui autorise mes deux populations a partager un denominateur.

    Chaque joueur joue ses **trois** cartes a chaque tour (paragraphe 3.2) et recomplete sa
    main depuis une pioche fixee par la donne (paragraphe 3.3). La main d'un siege a un tour
    donne est donc determinee par la seule donne. Avec elle, le nombre d'Assassins qu'il pose,
    donc le nombre de nœuds de ciblage a Assassin en attente.

    **C'est pourquoi `287/4145` et `204/4145` portent le meme denominateur** : ce n'est pas une
    coincidence ni une erreur de report, c'est une propriete des regles. Si elle tombait, mes
    deux taux ne se compareraient plus a nombre de nœuds egal, et il faudrait publier deux
    denominateurs.
    """
    from agents.greedy import choisir
    from agents.perception import percevoir
    from audit.phase2.greedy import Aleatoire
    from courtisans.cards import Role
    from courtisans.engine import Engine, Phase

    class Greedy:
        """Sa politique, graine fixee."""

        def __init__(self, graine: int) -> None:
            self.alea = random.Random(graine)

        def action(self, etat) -> int:
            """L'action de son greedy."""
            return choisir(percevoir(etat, etat.current_player()), self.alea)

    def assassins_par_tour(seed: int, table) -> list[int]:
        """Les Assassins en main de chaque siege, tour par tour, dans l'ordre de jeu."""
        etat = Engine(CONFIG).reset(seed)
        comptes = []
        while not etat.is_terminal():
            if etat.phase() is Phase.POSE:
                main = etat.vue_privilegiee().mains[etat.current_player()]
                comptes.append(sum(1 for c in main if c.role is Role.ASSASSIN))
            etat.apply(table[etat.current_player()].action(etat))
        return comptes

    for seed in range(40):
        trois_greedys = assassins_par_tour(seed, [Greedy(1)] * CONFIG.joueurs)
        un_greedy = assassins_par_tour(
            seed,
            [
                Greedy(2) if s == 0 else Aleatoire(random.Random(100 + s))
                for s in range(CONFIG.joueurs)
            ],
        )
        aleatoires = assassins_par_tour(
            seed, [Aleatoire(random.Random(200 + s)) for s in range(CONFIG.joueurs)]
        )
        assert trois_greedys == un_greedy == aleatoires, (
            f"seed {seed} : la main depend de la politique, mes deux populations ne "
            f"partagent alors plus leur denominateur"
        )
        assert len(trois_greedys) == CONFIG.joueurs * CONFIG.tours


def test_mes_deux_populations_comptent_le_meme_nombre_de_sieges_parties():
    """L'unite qui porte le taux est le siege-partie mesure, pas la partie jouee.

    A trois greedys, `donnes` parties et trois sieges mesures chacune ; a un greedy,
    `3 x donnes` parties et un siege mesure chacune. Les **parties jouees** diffèrent d'un
    facteur trois, les **sieges-parties mesures** sont egaux -- et c'est le second qui rend
    les deux taux comparables.
    """
    from audit.phase2.coherence_horizon import mesurer

    donnes = 25
    trois = mesurer("trois-greedys", donnes)
    un = mesurer("un-greedy-deux-hasards", donnes)
    assert trois.iterations == donnes
    assert un.iterations == donnes * CONFIG.joueurs
    assert trois.sieges_parties == un.sieges_parties == donnes * CONFIG.joueurs
    assert trois.tours == un.tours == donnes * CONFIG.joueurs * CONFIG.tours
    assert trois.noeuds_avec_attente == un.noeuds_avec_attente
    for comptage in (trois, un):
        assert "sieges-parties mesures" in comptage.texte()
        assert "parties jouees" in comptage.texte()


# ---------------------------------------------------------------------------------
# Reserve 2 -- l'inclusion levee, ses deux branches, et le grain -par-partie
# ---------------------------------------------------------------------------------


def _paire_inclusion(collectif: int, motif: int, suffixe: str = "") -> dict:
    """Deux comptes d'inclusion fabriques, au grain demande."""
    grain = "parties (au moins un des 3 sieges mesures)" if suffixe else "couples (partie, siege)"
    return {
        f"B1-collectif{suffixe}": _compte(f"B1-collectif{suffixe}", collectif, 100, grain),
        f"B1-motif{suffixe}": _compte(f"B1-motif{suffixe}", motif, 100, grain),
    }


@pytest.mark.parametrize("suffixe", ["", "-par-partie"])
def test_r2_l_inclusion_leve_quand_elle_tombe(suffixe):
    """La branche qui compte : `B1-collectif < B1-motif` doit **lever**, aux deux grains.

    Une phrase du rapport se re-remplit ; une levee, non. C'est la parade que la correction
    du defaut 1 a introduite, appliquee ici a une inclusion qui n'etait imprimee que sur deux
    populations sur trois.
    """
    with pytest.raises(ValueError, match="inclusion tombee"):
        comp.verifier_inclusion_b1(_paire_inclusion(collectif=10, motif=11, suffixe=suffixe))


@pytest.mark.parametrize("suffixe", ["", "-par-partie"])
def test_r2_l_inclusion_passe_quand_elle_tient(suffixe):
    """L'autre branche. Une garde qui leverait toujours interdirait le rapport entier."""
    assert (
        comp.verifier_inclusion_b1(_paire_inclusion(collectif=11, motif=10, suffixe=suffixe))
        is None
    )
    # L'egalite est licite : `B1-collectif` MAJORE, il n'est pas strictement superieur.
    assert (
        comp.verifier_inclusion_b1(_paire_inclusion(collectif=10, motif=10, suffixe=suffixe))
        is None
    )


def test_r2_un_grain_absent_est_ignore_et_ne_leve_pas():
    """Un compteur manquant n'est pas une inclusion tombee. Les deux cas se distinguent.

    Sans cela, une population qui ne publierait qu'un grain ferait lever la garde et le
    rapport ne s'ecrirait plus du tout -- une garde qui interdit ce qu'elle devait protéger.
    """
    assert comp.verifier_inclusion_b1({}) is None
    partiel = _paire_inclusion(collectif=10, motif=11)
    del partiel["B1-motif"]
    assert comp.verifier_inclusion_b1(partiel) is None


def test_r2_le_rapport_refuse_d_ecrire_si_l_inclusion_tombe_sur_LA_TROISIEME():
    """La garde est appelee **avant** d'ecrire, et sur les trois populations, pas sur deux.

    Verifie en executant plutot qu'en lisant : on passe une troisieme population dont
    l'inclusion est volontairement fausse, et la generation doit lever. Un grep sur le nombre
    d'appels aurait ete la mauvaise forme de controle -- il n'y a qu'**un** site, dans une
    boucle sur les trois populations, ce qui est le meilleur motif et la meme discipline que
    `budget_d_un_compteur`.
    """
    from mesure.rapport_phase2 import section_m4

    def population(collectif: int, motif: int) -> dict:
        """Une population minimale portant la seule paire d'inclusion."""
        grain = "couples (partie, siege)"
        return {
            "B1-collectif": _compte("B1-collectif", collectif, 100, grain),
            "B1-motif": _compte("B1-motif", motif, 100, grain),
        }

    saines = population(11, 10)
    vide: dict = {}
    # La troisieme population viole l'inclusion : la generation doit refuser d'ecrire.
    with pytest.raises(ValueError, match="inclusion tombee"):
        section_m4([], saines, saines, vide, vide, vide, vide, trois=population(9, 10))
    # Et l'absence de troisieme population ne doit pas empecher la verification des deux.
    with pytest.raises(ValueError, match="inclusion tombee"):
        section_m4([], population(9, 10), saines, vide, vide, vide, vide)


def test_r2_les_trois_valeurs_publiees_satisfont_l_inclusion():
    """Les trois couples imprimes, verifies par moi sur le texte du rapport.

    Mon propre `3 916 >= 2 528` du tour 2 portait sur un **sous-echantillon** :
    `campagne_b(donnes=600, depart=6000000, nb_greedys=3)`, soit les 600 premieres donnes de
    la meme plage de graines, 5 400 couples `(partie, siege)`. Le sien porte les 3 334 donnes
    entieres, 30 006 couples. Les deux se comparent en taux : 72,52 % contre 71,78 % pour
    `B1-collectif`, 46,81 % contre 46,13 % pour `B1-motif`.
    """
    texte = _rapport()
    for collectif, motif in ((7008, 4794), (20157, 10836), (21538, 13843)):
        assert str(collectif) in texte, collectif
        assert str(motif) in texte, motif
        assert collectif >= motif
    # Le taux de mon sous-echantillon et celui de sa campagne entiere, au meme grain.
    assert abs(3916 / 5400 - 21538 / 30006) < 0.01
    assert abs(2528 / 5400 - 13843 / 30006) < 0.01
