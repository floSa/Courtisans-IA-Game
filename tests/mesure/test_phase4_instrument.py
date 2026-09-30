"""L'instrument de l'iteration 1, teste AVANT d'entrainer quoi que ce soit.

Trois familles, et chacune tient une chose que rien ne tenait :

1. **L'empreinte de l'adversaire.** Le seuil qui tranche l'iteration se mesure contre
   `models/phase3/final.pt`, un fichier non suivi et non sauvegarde. Sans ce cas, un jour, le
   juge tournerait contre un autre adversaire que celui qu'il nomme.
2. **L'EGALITE D'ECHELLE**, exigee par l'arbitrage avant toute modification de la cible du
   critique : si le critique predit une cible rescalee, elle doit etre remise a l'echelle de
   `R` avant d'entrer dans l'avantage. Un avantage entre un `R` brut et un `V` normalise n'est
   pas un avantage.
3. **Le R2 et son ecart apparie.** Un rapport d'agregats ne s'apparie pas nœud a nœud, et un
   bootstrap qui tirerait des nœuds rendrait un intervalle bien trop etroit.
"""

from __future__ import annotations

import math
import random
import statistics
from pathlib import Path

import pytest
import torch

from mesure import phase4

APPAREIL = torch.device("cpu")


# ---------------------------------------------------------------------------------
# 1. L'adversaire du seuil decisif est celui que le rapport nomme
# ---------------------------------------------------------------------------------


def test_l_agent_de_la_phase3_present_porte_l_empreinte_pre_inscrite():
    """ETABLIT : le fichier sur le disque est bien l'agent contre lequel l'iteration se juge.

    POPULATION : `models/phase3/final.pt` tel qu'il est au moment ou le cas s'execute.

    Le fichier n'est **pas dans le depot** -- `models/` est ignore, et 500 Ko de binaire n'ont
    rien a y faire. C'est donc son identite qui est inscrite, et ce cas la confronte. Un gain
    publie contre un autre adversaire serait un chiffre exact sur une population que sa phrase
    ne nomme pas : la faute de signature du projet, appliquee au juge lui-meme.
    """
    fichier = Path(phase4.CHEMIN_AGENT_PHASE3)
    if not fichier.exists():
        pytest.fail(
            f"{phase4.CHEMIN_AGENT_PHASE3} est absent. Ce n'est pas un cas a desactiver : "
            f"c'est l'adversaire du seuil decisif. Recette : {phase4.RECETTE_AGENT_PHASE3}"
        )
    assert fichier.stat().st_size == phase4.OCTETS_AGENT_PHASE3
    assert phase4.verifier_l_agent_de_la_phase3() == phase4.EMPREINTE_AGENT_PHASE3


def test_la_verification_de_l_empreinte_LEVE_sur_un_autre_fichier(tmp_path: Path):
    """ETABLIT : la garde mord -- un fichier different fait lever, avec les deux empreintes.

    POPULATION : un fichier fabrique dont le contenu n'est pas celui de l'agent.

    Une garde qu'on n'a jamais vue tomber ne protege rien. Le message doit porter **les deux**
    empreintes : celle qu'on attendait et celle qu'on a trouvee, sinon il ne dit pas quoi faire.
    """
    faux = tmp_path / "final.pt"
    faux.write_bytes(b"ceci n'est pas un reseau")
    with pytest.raises(ValueError, match="n'est pas l'agent de la phase 3"):
        phase4.verifier_l_agent_de_la_phase3(str(faux))


def test_la_verification_de_l_empreinte_LEVE_sur_un_fichier_absent(tmp_path: Path):
    """ETABLIT : un adversaire absent leve avec sa RECETTE, et ne rend pas silencieusement None.

    POPULATION : un chemin qui n'existe pas.

    Une empreinte prouve l'identite ; elle ne dit pas comment refaire le fichier. Les deux sont
    inscrits, et le message porte la recette parce que c'est le moment ou on en a besoin.
    """
    with pytest.raises(FileNotFoundError, match="Recette"):
        phase4.verifier_l_agent_de_la_phase3(str(tmp_path / "absent.pt"))


# ---------------------------------------------------------------------------------
# 2. L'EGALITE D'ECHELLE -- avant toute modification de la cible du critique
# ---------------------------------------------------------------------------------


def _reseau(graine: int = 0):
    from agents import entrainement

    torch.manual_seed(graine)
    return entrainement.construire(APPAREIL)


def test_l_avantage_compare_deux_grandeurs_de_MEME_echelle():
    """ETABLIT : `R - V(s)` est invariant si l'on rescale la cible ET qu'on la remet a l'echelle.

    POPULATION : une vague reelle de 24 parties d'entrainement, dont l'avantage est calcule
    deux fois -- une fois sur `V` brut, une fois sur un `V` normalise puis **remis a
    l'echelle de `R`**.

    **C'est la condition sans exception de l'arbitrage.** Un critique a le droit de predire une
    cible rescalee ; il n'a pas le droit d'entrer rescale dans l'avantage. Un avantage calcule
    entre un `R` brut et un `V` normalise n'est pas un avantage : c'est une difference entre
    deux grandeurs qui ne se comparent pas, et **rien ne leverait** -- exactement la forme de
    `valeur-non-aplatie`.

    Le cas etablit les deux moities : la remise a l'echelle rend l'avantage identique, et
    l'oubli de la remise a l'echelle le rend different. Sans la seconde, le cas passerait sur
    une transformation qui ne fait rien.
    """
    from agents import entrainement

    modele = _reseau(graine=5)
    trajectoires, _ = entrainement.jouer_une_vague(modele, [], 24, 910_000, APPAREIL)
    retours = torch.tensor(trajectoires.gains, dtype=torch.float32)
    valeurs = torch.tensor(trajectoires.valeurs, dtype=torch.float32)

    avantage_de_reference = retours - valeurs

    # Une cible rescalee, de la forme la plus banale : centrer-reduire.
    moyenne = float(valeurs.mean())
    ecart_type = float(valeurs.std())
    assert ecart_type > 1e-6, "les valeurs predites sont constantes : le cas ne teste rien"
    normalisees = (valeurs - moyenne) / ecart_type

    # AVEC la remise a l'echelle : l'avantage ne bouge pas.
    remises = normalisees * ecart_type + moyenne
    avantage_remis = retours - remises
    assert torch.allclose(avantage_remis, avantage_de_reference, atol=1e-5), (
        "une cible rescalee PUIS remise a l'echelle de R doit rendre le meme avantage ; "
        f"ecart max {float((avantage_remis - avantage_de_reference).abs().max()):.3e}"
    )

    # SANS la remise a l'echelle : l'avantage est faux, et rien ne leve.
    avantage_faux = retours - normalisees
    ecart = float((avantage_faux - avantage_de_reference).abs().max())
    assert ecart > 1e-3, (
        "sur cette vague, oublier la remise a l'echelle ne change rien : le cas ne separe "
        "pas les deux lectures et ne prouverait rien"
    )


def test_un_avantage_melangeant_deux_echelles_change_le_signe_de_certains_noeuds():
    """ETABLIT : l'oubli de la remise a l'echelle **inverse le signe** d'une part des avantages.

    POPULATION : les nœuds de la meme vague de 24 parties.

    Le cas precedent montre que les nombres different. Celui-ci montre ce que ca coute : PPO
    ne lit pas la valeur de l'avantage, il lit **son signe** -- renforcer ou decourager
    l'action. Un avantage qui change de signe fait apprendre l'inverse de ce qu'on croit, et
    la perte descend quand meme.
    """
    from agents import entrainement

    modele = _reseau(graine=5)
    trajectoires, _ = entrainement.jouer_une_vague(modele, [], 24, 910_000, APPAREIL)
    retours = torch.tensor(trajectoires.gains, dtype=torch.float32)
    valeurs = torch.tensor(trajectoires.valeurs, dtype=torch.float32)
    normalisees = (valeurs - valeurs.mean()) / valeurs.std()

    reference = retours - valeurs
    faux = retours - normalisees
    inversions = int(((reference > 0) != (faux > 0)).sum())
    assert inversions > 0, (
        "aucun signe ne s'inverse sur cette vague : le cas ne montre pas la consequence "
        "qu'il annonce"
    )


# ---------------------------------------------------------------------------------
# 3. Le R2 et son ecart apparie
# ---------------------------------------------------------------------------------


def test_le_r2_est_bien_un_moins_MSE_sur_variance():
    """ETABLIT : `r2` rend la valeur de la methode de la phase 3, recalculee a la main.

    POPULATION : dix retours et dix predictions choisis, plus le cas du predicteur constant.

    Le predicteur qui rend la moyenne des retours fait, par construction, **exactement 0**.
    C'est l'etalon du chiffre : un R2 positif dit « mieux que la moyenne », et c'est tout ce
    qu'il dit. Le critique de la phase 3 vaut +0,10 -- il n'explique presque rien de plus.
    """
    retours = [1.0, -1.0, 0.5, 0.0, -0.5, 1.0, -1.0, 0.25, -0.25, 0.0]
    predites = [0.8, -0.9, 0.4, 0.1, -0.6, 0.7, -0.8, 0.3, -0.2, 0.05]

    mse = statistics.fmean((r - v) ** 2 for r, v in zip(retours, predites))
    variance = statistics.pvariance(retours)
    assert math.isclose(phase4.r2(retours, predites), 1.0 - mse / variance, rel_tol=1e-12)

    constant = [statistics.fmean(retours)] * len(retours)
    assert math.isclose(phase4.r2(retours, constant), 0.0, abs_tol=1e-12), (
        "le predicteur constant doit faire exactement 0 : c'est l'etalon du R2"
    )


def test_le_r2_LEVE_sur_une_variance_nulle_au_lieu_de_rendre_un():
    """ETABLIT : une variance de retours nulle fait lever, et ne rend pas `1.0`.

    POPULATION : dix retours tous egaux.

    Un R2 sur une variance nulle n'est pas « parfait » : il n'est **pas defini**. Le rendre
    `1.0` publierait une conclusion que rien n'a calculee -- c'est exactement la faute du
    tour 2 de la phase 3, ou un `None` etait imprime « non separable a ce budget ».
    """
    with pytest.raises(ValueError, match="variance des retours est nulle"):
        phase4.r2([0.5] * 10, [0.1] * 10)


def test_le_r2_LEVE_si_les_deux_suites_n_ont_pas_la_meme_longueur():
    """ETABLIT : comparer 10 retours a 9 predictions leve au lieu de tronquer en silence.

    POPULATION : deux suites de longueurs differentes.

    `zip` tronque sans rien dire. Un R2 calcule sur une troncature muette serait un chiffre
    exact sur une population que sa phrase ne nomme pas.
    """
    with pytest.raises(ValueError, match="comparerait"):
        phase4.r2([1.0] * 10, [0.0] * 9)


def test_l_ecart_apparie_de_r2_est_NUL_quand_les_deux_critiques_sont_le_meme():
    """ETABLIT : compare a lui-meme, l'ecart vaut 0 et son intervalle contient 0.

    POPULATION : un echantillon fabrique de 40 donnes x 5 nœuds, un seul jeu de predictions
    passe deux fois.

    C'est le controle de niveau nul de l'instrument, et il est **exact**, pas statistique :
    chaque rechantillon donne le meme R2 des deux cotes, donc l'ecart y est exactement zero.
    Un instrument qui rendrait autre chose ici fabriquerait du signal a partir de rien.
    """
    alea = random.Random(11)
    donnes, retours, predites = [], [], []
    for donne in range(40):
        gain = alea.choice([-1.0, 0.0, 1.0])
        for _ in range(5):
            donnes.append(donne)
            retours.append(gain)
            predites.append(gain * 0.3 + alea.gauss(0, 0.2))
    echantillon = phase4.EchantillonHorsPlage(
        observations=tuple(() for _ in retours),
        retours=tuple(retours),
        donnes=tuple(donnes),
        depart=0,
        nb_parties=40,
    )

    ecart = phase4.ecart_apparie_de_r2(
        echantillon, predites, predites, repetitions=200, alea=random.Random(3)
    )
    assert ecart.moyenne == 0.0
    assert ecart.intervalle == (0.0, 0.0)
    assert not ecart.progres_etabli, (
        "un critique compare a lui-meme ne progresse pas : l'instrument fabriquerait du signal"
    )


def test_l_ecart_apparie_de_r2_ETABLIT_un_progres_reel():
    """ETABLIT : un critique franchement meilleur sort avec un intervalle entierement au-dessus de 0.

    POPULATION : le meme echantillon fabrique, avec un second jeu de predictions **construit**
    pour etre meilleur -- il predit le retour a 20 % de bruit pres, contre un premier jeu qui
    predit presque du bruit.

    Le cas precedent montre que l'instrument ne fabrique pas de signal ; celui-ci montre qu'il
    en voit un quand il y en a. Il en faut deux : un instrument qui ne declare jamais rien
    passerait le premier tout seul.
    """
    alea = random.Random(17)
    donnes, retours, faible, fort = [], [], [], []
    for donne in range(60):
        gain = alea.choice([-1.0, 0.0, 1.0])
        for _ in range(5):
            donnes.append(donne)
            retours.append(gain)
            faible.append(alea.gauss(0, 0.1))
            fort.append(gain + alea.gauss(0, 0.2))
    echantillon = phase4.EchantillonHorsPlage(
        observations=tuple(() for _ in retours),
        retours=tuple(retours),
        donnes=tuple(donnes),
        depart=0,
        nb_parties=60,
    )

    ecart = phase4.ecart_apparie_de_r2(
        echantillon, faible, fort, repetitions=500, alea=random.Random(5)
    )
    assert ecart.moyenne > 0.0
    assert ecart.progres_etabli, (
        f"un critique franchement meilleur n'est pas declare : ecart {ecart.moyenne:+.4f} "
        f"IC {ecart.intervalle}"
    )


def test_l_ecart_apparie_de_r2_rechantillonne_les_DONNES_et_non_les_noeuds():
    """ETABLIT : l'intervalle est plus large que celui d'un bootstrap qui tirerait des nœuds.

    POPULATION : un echantillon fabrique ou les cinq nœuds d'une donne portent **le meme**
    retour -- ce qui est la structure reelle : le gain est terminal et commun a tous les nœuds
    du siege.

    C'est la raison d'etre du bootstrap par donne, et elle se mesure au lieu de s'affirmer.
    Tirer des nœuds traiterait cinq copies du meme retour comme cinq observations
    independantes, et rendrait un intervalle **trop etroit** -- une conclusion plus assuree
    que ce que les donnees permettent.
    """
    alea = random.Random(23)
    donnes, retours, faible, fort = [], [], [], []
    for donne in range(40):
        gain = alea.choice([-1.0, 1.0])
        for _ in range(5):
            donnes.append(donne)
            retours.append(gain)
            faible.append(alea.gauss(0, 0.1))
            fort.append(gain * 0.5 + alea.gauss(0, 0.4))
    echantillon = phase4.EchantillonHorsPlage(
        observations=tuple(() for _ in retours),
        retours=tuple(retours),
        donnes=tuple(donnes),
        depart=0,
        nb_parties=40,
    )
    par_donne = phase4.ecart_apparie_de_r2(
        echantillon, faible, fort, repetitions=400, alea=random.Random(7)
    )

    # Le meme calcul en traitant chaque nœud comme sa propre donne : c'est le bootstrap
    # naif, celui que le projet interdit.
    par_noeud_echantillon = phase4.EchantillonHorsPlage(
        observations=echantillon.observations,
        retours=echantillon.retours,
        donnes=tuple(range(len(retours))),
        depart=0,
        nb_parties=40,
    )
    par_noeud = phase4.ecart_apparie_de_r2(
        par_noeud_echantillon, faible, fort, repetitions=400, alea=random.Random(7)
    )

    largeur_donne = par_donne.intervalle[1] - par_donne.intervalle[0]
    largeur_noeud = par_noeud.intervalle[1] - par_noeud.intervalle[0]
    assert largeur_donne > largeur_noeud, (
        f"le bootstrap par donne ({largeur_donne:.4f}) n'est pas plus large que le bootstrap "
        f"par nœud ({largeur_noeud:.4f}) : la correlation intra-donne n'est pas prise en "
        f"compte, et l'intervalle publie serait trop assure"
    )
