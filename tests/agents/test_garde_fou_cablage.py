"""Le garde-fou au SITE D'APPEL : ce qui declenche l'arret, avec quel risque, et ce que le pool garde.

`agents/campagne.py` porte cinq versions successives d'un meme garde-fou, dont quatre etaient
fausses. La cinquieme faute est nee **dans la correction de la quatrieme**, et le module la
raconte. Sa parade a ete de deplacer le predicat dans `bootstrap.EcartApparie.progres_etabli`,
a un seul site, et de lui passer un cas.

**Le predicat a donc sa parade. Son CABLAGE n'en avait aucune.** La campagne de mutation de
l'etape 0 l'a mesure : trois trous, tous dans `entrainer` et dans `evaluer_le_garde_fou`,
c'est-a-dire dans les lignes qui decident si un run continue, avec quel intervalle, et contre
quoi l'agent s'entraine. Un cinquieme defaut peut revenir par le cablage sans qu'un seul cas
bouge -- et il tuerait un run en cours de route, ou le laisserait tourner sur un effondrement.

Ce fichier ne mesure aucun agent. Il tient trois cablages, sur un run reel dont **l'horloge est
fournie par le cas** : le budget de la vraie campagne est de deux heures, et un cas ne les paie
pas. Ce qui est joue est reel -- vraies parties, vrai reseau, vrais checkpoints ; seul le temps
est simule, et il l'est pour que le nombre de checkpoints soit un nombre choisi et non un aleas
de machine.
"""

from __future__ import annotations

import random
from pathlib import Path

import pytest
import torch

from agents import campagne
from agents import entrainement
from mesure import bootstrap as boot

APPAREIL = torch.device("cpu")

#: Le run miniature des cas ci-dessous : assez de checkpoints pour depasser le plafond du pool
#: **et** pour atteindre le premier checkpoint qui peut declencher.
CHECKPOINTS_DU_CAS = entrainement.POOL_MAXIMUM + 2


class _HorlogeDeCas:
    """Une horloge qui avance d'une seconde par lecture. Deux lectures par tour de boucle.

    `entrainer` lit `perf_counter` deux fois par iteration : une avant la vague, une apres.
    Avec un pas d'une seconde et un checkpoint attendu toutes les deux secondes, **chaque
    vague est un checkpoint** et leur nombre est exactement calculable. Aucune constante du
    garde-fou n'est modifiee : c'est le budget qui est reduit, pas la regle.
    """

    def __init__(self) -> None:
        self.lectures = 0

    def __call__(self) -> float:
        valeur = float(self.lectures)
        self.lectures += 1
        return valeur


def _lancer_un_run_miniature(
    monkeypatch: pytest.MonkeyPatch, dossier: Path, checkpoints: int
) -> list[campagne.Jalon]:
    """Un run reel de `checkpoints` checkpoints, sur une horloge de cas."""
    monkeypatch.setattr(campagne.time, "perf_counter", _HorlogeDeCas())
    return campagne.entrainer(
        dossier=dossier,
        plafond_secondes=2.0 * checkpoints + 1.0,
        secondes_entre_checkpoints=2.0,
        parties_par_vague=8,
        appareil=APPAREIL,
        donnes_garde_fou=4,
    )


def _ecart(moyenne: float, bas: float, haut: float) -> boot.EcartApparie:
    """Un `EcartApparie` d'intervalle choisi. Le predicat reste celui du module, jamais recopie."""
    return boot.EcartApparie(
        moyenne=moyenne,
        nb_donnes=4,
        intervalle=(bas, haut),
    )


# ---------------------------------------------------------------------------------
# 1. Ce qui declenche : un progres qui n'est pas ETABLI, pas un ecart qui l'est
# ---------------------------------------------------------------------------------


def test_le_site_d_appel_arrete_le_run_sur_un_EFFONDREMENT_etabli(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """ETABLIT : un ecart etabli mais NEGATIF arrete le run, au premier checkpoint qui peut declencher.

    POPULATION : un run reel de 10 checkpoints, dont l'ecart apparie est remplace par
    l'effondrement mesure par l'audit du tour 2 -- **-17,80 pt, IC [-18,43 ; -17,08]**, un
    intervalle entierement sous zero.

    C'est la cinquieme faute du garde-fou, celle qui est nee dans la correction de la quatrieme.
    « Un effondrement est un ecart parfaitement etabli : il passait le test, et le garde-fou le
    lisait comme une raison de continuer. » Le predicat a sa parade ; c'est le CABLAGE qui est
    tenu ici. Le cas n'ecrit pas quelle propriete de `EcartApparie` doit etre lue : il fabrique
    un effondrement et exige l'arret.
    """
    effondrement = _ecart(-0.1780, -0.1843, -0.1708)
    assert effondrement.etabli, "le cas doit passer un ecart ETABLI, sinon il ne separe rien"
    assert not effondrement.progres_etabli

    monkeypatch.setattr(
        campagne.boot,
        "bootstrap_apparie_par_donne",
        lambda *args, **kwargs: effondrement,
    )
    jalons = _lancer_un_run_miniature(monkeypatch, tmp_path, CHECKPOINTS_DU_CAS)

    assert jalons[-1].declenche, (
        "le run est alle au bout en encaissant un effondrement etabli a chaque checkpoint : "
        "le garde-fou ne voit pas le mode de defaillance qu'il existe pour voir"
    )
    assert len(jalons) == campagne.PREMIER_CHECKPOINT_QUI_DECLENCHE, (
        f"arret au checkpoint {len(jalons)}, attendu au "
        f"{campagne.PREMIER_CHECKPOINT_QUI_DECLENCHE} -- le premier qui dispose d'un "
        f"checkpoint de reference a portee {campagne.PORTEE_DU_GARDE_FOU}"
    )
    assert not any(jalon.declenche for jalon in jalons[:-1])


def test_le_site_d_appel_laisse_courir_un_run_dont_le_progres_est_etabli(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """ETABLIT : un ecart entierement AU-DESSUS de zero ne declenche a aucun checkpoint.

    POPULATION : le meme run reel de 10 checkpoints, ecart apparie remplace par un progres
    etabli de +5,00 pt, IC [+1,00 ; +9,00].

    Sans ce cas, le precedent serait satisfait par un garde-fou qui arrete **toujours** -- et
    c'est exactement le defaut de la version du 21/08, qui aurait tue le run au checkpoint 3.
    Un declencheur qui declenche sur tout ne detecte rien.
    """
    progres = _ecart(0.0500, 0.0100, 0.0900)
    assert progres.progres_etabli

    monkeypatch.setattr(
        campagne.boot, "bootstrap_apparie_par_donne", lambda *a, **k: progres
    )
    jalons = _lancer_un_run_miniature(monkeypatch, tmp_path, CHECKPOINTS_DU_CAS)

    assert len(jalons) == CHECKPOINTS_DU_CAS
    assert not any(jalon.declenche for jalon in jalons)


def test_le_site_d_appel_arrete_le_run_sur_un_ecart_qui_n_est_pas_etabli(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """ETABLIT : un intervalle qui contient zero -- « on ne sait pas » -- arrete aussi le run.

    POPULATION : le meme run reel, ecart apparie remplace par +0,20 pt, IC [-3,50 ; +3,90].

    C'est le troisieme etat, et il complete les deux autres : le garde-fou ne demande pas
    « l'agent a-t-il recule ? » mais « **le progres est-il etabli ?** ». Un agent dont on ne
    peut pas montrer qu'il progresse est un agent dont on ne sait pas s'il apprend, et le
    garde-fou existe pour cette phrase-la.
    """
    indecis = _ecart(0.0020, -0.0350, 0.0390)
    assert not indecis.etabli
    assert not indecis.progres_etabli

    monkeypatch.setattr(
        campagne.boot, "bootstrap_apparie_par_donne", lambda *a, **k: indecis
    )
    jalons = _lancer_un_run_miniature(monkeypatch, tmp_path, CHECKPOINTS_DU_CAS)

    assert jalons[-1].declenche
    assert len(jalons) == campagne.PREMIER_CHECKPOINT_QUI_DECLENCHE


# ---------------------------------------------------------------------------------
# 2. Avec quel risque : huit regards, et l'intervalle qui va avec
# ---------------------------------------------------------------------------------


def test_le_nombre_de_regards_est_celui_que_le_budget_produit():
    """ETABLIT : `CHECKPOINTS_ATTENDUS` vaut le plafond divise par l'intervalle entre checkpoints.

    POPULATION : les trois constantes de budget du module.

    « Deux heures a un checkpoint tous les quarts d'heure font **huit** evaluations. » Le
    chiffre de Bonferroni n'est pas un reglage : c'est une consequence du budget. S'il etait
    ecrit a la main et que le budget bougeait, la correction porterait sur un nombre de regards
    qui n'est plus celui qu'on prend, et l'IC publie serait faux **dans le sens rassurant**.
    """
    assert campagne.PLAFOND_SECONDES / campagne.SECONDES_ENTRE_CHECKPOINTS == (
        campagne.CHECKPOINTS_ATTENDUS
    ), (
        f"budget {campagne.PLAFOND_SECONDES} s, checkpoint toutes les "
        f"{campagne.SECONDES_ENTRE_CHECKPOINTS} s : cela fait "
        f"{campagne.PLAFOND_SECONDES / campagne.SECONDES_ENTRE_CHECKPOINTS} regards, et la "
        f"correction en applique {campagne.CHECKPOINTS_ATTENDUS}"
    )


def test_l_intervalle_du_garde_fou_est_pris_au_risque_divise_par_le_nombre_de_regards(
    monkeypatch: pytest.MonkeyPatch,
):
    """ETABLIT : l'IC rendu par `evaluer_le_garde_fou` est celui du risque `0,01 / regards`.

    POPULATION : une evaluation reelle de 8 donnes x 3 sieges = 24 parties, dont les
    observations et le risque sont captes au passage, puis rejoues a la main aux deux risques.

    Le module promet : « L'IC est calcule au risque `0,01 / 8` : huit checkpoints sont huit
    regards, et un IC a 99 % applique huit fois se franchit a tort bien plus d'une fois sur
    cent. » Le cas ne lit pas la constante dans le code : il **recalcule les deux intervalles**
    sur les memes observations et exige que celui qui sort soit le corrige, et pas l'autre. Un
    IC non corrige est plus etroit -- il rassure a tort, et c'est le sens dans lequel une faute
    ne se voit pas.
    """
    vrai = boot.bootstrap_par_donne
    captures: list[dict] = []

    def espion(observations, repetitions, alea, risque=0.01):
        etat = alea.getstate()
        resultat = vrai(observations, repetitions, alea, risque=risque)
        captures.append(
            {
                "observations": observations,
                "repetitions": repetitions,
                "etat": etat,
                "risque": risque,
                "intervalle": resultat.intervalle,
            }
        )
        return resultat

    monkeypatch.setattr(campagne.boot, "bootstrap_par_donne", espion)
    modele = entrainement.construire(APPAREIL)
    campagne.evaluer_le_garde_fou(modele, donnes=8)

    assert captures, "aucun intervalle n'a ete calcule : le cas ne teste rien"
    for numero, capture in enumerate(captures):
        alea_corrige = random.Random()
        alea_corrige.setstate(capture["etat"])
        corrige = vrai(
            capture["observations"],
            capture["repetitions"],
            alea_corrige,
            risque=0.01 / campagne.CHECKPOINTS_ATTENDUS,
        )
        alea_nu = random.Random()
        alea_nu.setstate(capture["etat"])
        nu = vrai(
            capture["observations"], capture["repetitions"], alea_nu, risque=0.01
        )

        assert capture["intervalle"] == corrige.intervalle, (
            f"intervalle {numero} : {capture['intervalle']} rendu, "
            f"{corrige.intervalle} attendu au risque 0,01/"
            f"{campagne.CHECKPOINTS_ATTENDUS}"
        )
        largeur = corrige.intervalle[1] - corrige.intervalle[0]
        largeur_nue = nu.intervalle[1] - nu.intervalle[0]
        assert largeur > largeur_nue, (
            f"intervalle {numero} : le corrige ({largeur:.6f}) n'est pas plus large que le "
            f"non corrige ({largeur_nue:.6f}) -- sur cet echantillon les deux risques ne se "
            f"separent pas, et le cas ne prouverait rien"
        )


def test_l_ecart_apparie_du_garde_fou_est_pris_au_meme_risque_corrige(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """ETABLIT : l'ecart apparie qui DECLENCHE est lui aussi calcule au risque `0,01 / regards`.

    POPULATION : les ecarts apparies des checkpoints 4 a 10 d'un run reel de 10 checkpoints.

    L'IC du niveau et l'IC de l'ecart sont deux calculs distincts, a deux sites distincts. Le
    second est **celui qui decide**, et une correction posee sur le premier seulement laisserait
    le declencheur a decouvert.
    """
    vrai = boot.bootstrap_apparie_par_donne
    risques: list[float] = []

    def espion(avant, apres, repetitions, alea, risque=0.01):
        risques.append(risque)
        return vrai(avant, apres, repetitions, alea, risque=risque)

    monkeypatch.setattr(campagne.boot, "bootstrap_apparie_par_donne", espion)
    jalons = _lancer_un_run_miniature(monkeypatch, tmp_path, CHECKPOINTS_DU_CAS)

    declencheurs = [j for j in jalons if j.ecart_de_portee is not None]
    assert declencheurs, "aucun checkpoint n'a calcule d'ecart : le cas ne teste rien"
    assert risques, "aucun ecart apparie n'a ete calcule"
    attendu = 0.01 / campagne.CHECKPOINTS_ATTENDUS
    assert set(risques) == {attendu}, (
        f"les ecarts qui declenchent sont pris aux risques {sorted(set(risques))}, "
        f"attendu {attendu} pour {campagne.CHECKPOINTS_ATTENDUS} regards"
    )


# ---------------------------------------------------------------------------------
# 3. Contre quoi l'agent s'entraine : le pool garde les plus RECENTS
# ---------------------------------------------------------------------------------


def test_le_pool_plein_jette_le_plus_ANCIEN_checkpoint(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """ETABLIT : une fois plein, le pool contient les `POOL_MAXIMUM` checkpoints les plus RECENTS.

    POPULATION : le pool observe a chaque vague d'un run reel de 10 checkpoints, identifie par
    comparaison des poids avec les fichiers `checkpoint_NN.pt` ecrits par le run lui-meme.

    Le commentaire dit ce qui est en jeu, et ce n'est pas de la mesure : « Le plafond garde les
    **plus recents** : un pool rempli de versions tres faibles dilue le signal sans rien
    retenir de l'effondrement de convention. » **Le pool est ce contre quoi l'agent
    s'entraine** : jeter le plus recent au lieu du plus ancien change ce qui est APPRIS, pas
    seulement ce qui est mesure. L'agent s'entrainerait indefiniment contre ses toutes premieres
    versions, la perte descendrait, et le run publierait un progres contre un adversaire fige
    au depart.

    Le cas n'observe pas la liste `pool` par une variable interne : il regarde les poids que
    `jouer_une_vague` recoit reellement, ce qui est la seule chose qui influence l'apprentissage.
    """
    vrai = entrainement.jouer_une_vague
    empreintes_par_vague: list[list[str]] = []

    def empreinte(modele) -> str:
        with torch.no_grad():
            plat = torch.cat(
                [p.reshape(-1) for p in modele.state_dict().values()]
            )
        return f"{float(plat.sum()):.10e}|{float(plat.abs().sum()):.10e}"

    def espion(modele, pool, nb_parties, premiere_donne, appareil):
        empreintes_par_vague.append([empreinte(fige) for fige in pool])
        return vrai(modele, pool, nb_parties, premiere_donne, appareil)

    monkeypatch.setattr(entrainement, "jouer_une_vague", espion)
    monkeypatch.setattr(
        campagne.boot,
        "bootstrap_apparie_par_donne",
        lambda *a, **k: _ecart(0.0500, 0.0100, 0.0900),
    )
    jalons = _lancer_un_run_miniature(monkeypatch, tmp_path, CHECKPOINTS_DU_CAS)
    assert len(jalons) == CHECKPOINTS_DU_CAS

    # Les checkpoints tels que le run les a ecrits sur le disque, dans l'ordre.
    modele_relu = entrainement.construire(APPAREIL)
    empreintes_des_checkpoints: list[str] = []
    for numero in range(1, CHECKPOINTS_DU_CAS + 1):
        chemin = tmp_path / f"checkpoint_{numero:02d}.pt"
        assert chemin.exists(), f"le run n'a pas ecrit {chemin.name}"
        modele_relu.load_state_dict(torch.load(chemin, map_location=APPAREIL))
        empreintes_des_checkpoints.append(empreinte(modele_relu))
    assert len(set(empreintes_des_checkpoints)) == CHECKPOINTS_DU_CAS, (
        "deux checkpoints du run ont les memes poids : le cas ne pourrait pas les distinguer"
    )

    # Le pool est observe AVANT la vague, et un checkpoint y est ajoute APRES : a la vague
    # `k`, le pool est celui d'apres le checkpoint `k - 1`. Le cas verifie TOUTES les vagues,
    # pas seulement la derniere -- un pool qui jetterait le mauvais element ne le ferait qu'a
    # partir de la vague ou il deborde.
    assert len(empreintes_par_vague) == CHECKPOINTS_DU_CAS
    vagues_ou_le_pool_deborde = 0
    for rang_de_vague, pool in enumerate(empreintes_par_vague, start=1):
        deja_faits = rang_de_vague - 1
        attendus = list(
            range(max(1, deja_faits - entrainement.POOL_MAXIMUM + 1), deja_faits + 1)
        )
        if deja_faits > entrainement.POOL_MAXIMUM:
            vagues_ou_le_pool_deborde += 1
        rangs = [empreintes_des_checkpoints.index(e) + 1 for e in pool]
        assert rangs == attendus, (
            f"vague {rang_de_vague} : le pool contient les checkpoints {rangs}, attendu "
            f"{attendus} -- les {entrainement.POOL_MAXIMUM} plus RECENTS parmi les "
            f"{deja_faits} deja figes. L'agent s'entraine contre les mauvais adversaires."
        )

    assert vagues_ou_le_pool_deborde > 0, (
        f"le pool n'a jamais depasse son plafond de {entrainement.POOL_MAXIMUM} sur ce run : "
        f"le cas ne teste pas ce qui est jete"
    )
    assert len(empreintes_par_vague[-1]) == entrainement.POOL_MAXIMUM
