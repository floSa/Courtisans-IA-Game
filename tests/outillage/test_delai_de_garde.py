"""Le minuteur de la suite se prouve, comme le reste : on lui donne un cas qui boucle.

Un delai de garde qu'on installe et qu'on ne declenche jamais est une decoration -- et c'est
exactement le mode de defaut que la phase 4 a mesure sur les onze survivantes : une prose
posee a cote d'une ligne, et rien qui tombe quand on la contredit.

Le cas central de ce fichier lance **une vraie sous-suite dans un vrai processus pytest**, avec
un cas qui ne finit pas, et exige que le releve porte le depassement. C'est la seule forme qui
etablit que le crochet est branche : appeler `pytest_runtest_call` a la main ne prouverait que
la fonction, pas son cablage.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests import conftest as garde

RACINE = Path(__file__).resolve().parents[2]


def test_le_delai_est_le_produit_d_une_mesure_par_un_facteur_ecrit():
    """ETABLIT : le delai est strictement positif et vaut le cas le plus lent mesure fois le facteur.

    POPULATION : les trois constantes de `tests/conftest.py`.

    Un delai nul desarme le minuteur -- le crochet rend la main sans rien poser. Et un delai
    pose a la main, decorrele de la mesure, est **exactement** le chiffre rond que l'arbitrage
    interdit : il se perimerait a la premiere fois qu'un cas devient plus lent, sans que rien
    ne relie les deux nombres. Le cas ne verifie pas que le delai est bon -- il verifie qu'il
    est DERIVE.
    """
    assert garde.DELAI_ORDINAIRE > 0.0, (
        "le delai est nul : le minuteur ne s'arme sur aucun cas"
    )
    assert garde.CAS_LE_PLUS_LENT_MESURE > 0.0
    assert garde.FACTEUR_DU_DELAI > 1.0, (
        f"un facteur de {garde.FACTEUR_DU_DELAI} ne laisse aucune marge au-dessus du cas le "
        f"plus lent mesure : la suite deviendrait rouge sur une machine un peu plus lente"
    )
    assert garde.DELAI_ORDINAIRE == (
        garde.FACTEUR_DU_DELAI * garde.CAS_LE_PLUS_LENT_MESURE
    ), (
        f"le delai ({garde.DELAI_ORDINAIRE} s) n'est pas le produit de la mesure "
        f"({garde.CAS_LE_PLUS_LENT_MESURE} s) par le facteur ({garde.FACTEUR_DU_DELAI})"
    )


def test_aucun_cas_de_la_suite_ne_depasse_le_cas_le_plus_lent_annonce():
    """ETABLIT : la constante annoncee comme « le cas le plus lent » n'est pas perimee.

    POPULATION : ce cas-ci ne peut pas rejouer la suite ; il tient l'autre bout du raisonnement
    -- le delai laisse au moins trois fois la duree du cas le plus lent annonce.

    Le vrai controle du chiffre est la suite elle-meme : si un cas devenait plus lent que
    `DELAI_ORDINAIRE`, il tomberait, et le message d'echec nomme la constante a remesurer. Ce
    cas-ci verifie seulement que la marge annoncee existe, pour qu'un `FACTEUR_DU_DELAI` reduit
    a 1,01 ne passe pas sous couvert d'etre « derive d'une mesure ».
    """
    assert garde.DELAI_ORDINAIRE >= 3.0 * garde.CAS_LE_PLUS_LENT_MESURE


def test_le_delai_choisi_suit_le_marqueur_minuteur_quand_il_est_pose():
    """ETABLIT : `delai_pour` rend le delai du marqueur `minuteur` si et seulement s'il y est.

    POPULATION : deux objets de cas factices, l'un marque `minuteur(secondes=...)`, l'autre non.

    Le marqueur est la porte de sortie pour un cas legitimement long -- l'entrainement de la
    phase 4 en produira. Sans lui, la seule facon de faire passer un tel cas serait de relever
    le delai de **toute** la suite, ce qui desarmerait la garde partout pour un seul cas.
    """

    class _MarqueurFactice:
        kwargs = {"secondes": 123.0}

    class _CasFactice:
        def __init__(self, marque: bool) -> None:
            self._marque = marque

        def get_closest_marker(self, nom: str):
            return _MarqueurFactice() if (self._marque and nom == "minuteur") else None

    assert garde.delai_pour(_CasFactice(marque=True)) == 123.0
    assert garde.delai_pour(_CasFactice(marque=False)) == garde.DELAI_ORDINAIRE


@pytest.mark.skipif(
    not garde.MINUTEUR_DISPONIBLE,
    reason="SIGALRM/setitimer absents : ce fichier ne pretend pas proteger ce qu'il ne protege pas",
)
def test_un_cas_qui_boucle_est_arrete_et_un_cas_lent_de_la_meme_sous_suite_passe(
    tmp_path: Path,
):
    """ETABLIT : une boucle infinie en Python pur fait ECHOUER son cas, et **elle seule**.

    POPULATION : une sous-suite de deux cas, lancee dans un processus pytest separe avec le
    conftest de ce depot et un delai ramene a une seconde -- l'un boucle sans fin, l'autre
    dort moins longtemps que le delai.

    Deux choses sont etablies d'un coup, et elles ne sont pas la meme :

    - **le cas qui boucle tombe**, avec `DelaiDeGardeDepasse` et non une assertion, donc le
      releve peut le distinguer d'une affirmation fausse ;
    - **le cas voisin passe**, donc le minuteur n'emporte pas la campagne avec lui. C'est la
      difference avec le minuteur de `outillage/mutation.py`, qui tue le processus : la, une
      passe perdue coute trois minutes ; ici, elle couterait le releve entier.

    Le cas qui boucle est ecrit en **Python pur**, et c'est dit dans le conftest : un appel
    bloquant en C ne rendrait pas la main a l'interpreteur et le minuteur ne le verrait pas.
    """
    shutil.copy(RACINE / "tests" / "conftest.py", tmp_path / "conftest.py")
    (tmp_path / "conftest.py").write_text(
        (tmp_path / "conftest.py")
        .read_text(encoding="utf-8")
        .replace(
            "DELAI_ORDINAIRE: float = FACTEUR_DU_DELAI * CAS_LE_PLUS_LENT_MESURE",
            "DELAI_ORDINAIRE: float = 1.0",
        ),
        encoding="utf-8",
    )
    (tmp_path / "test_sous_suite.py").write_text(
        "import time\n"
        "\n"
        "def test_qui_boucle_en_python_pur():\n"
        "    compte = 0\n"
        "    while True:\n"
        "        compte += 1\n"
        "\n"
        "def test_qui_finit_dans_son_delai():\n"
        "    time.sleep(0.1)\n"
        "    assert True\n",
        encoding="utf-8",
    )

    resultat = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=tmp_path,
    )
    sortie = resultat.stdout + resultat.stderr

    assert "1 failed, 1 passed" in sortie, (
        f"la sous-suite devait rendre exactement un echec et un succes.\n{sortie}"
    )
    assert "DelaiDeGardeDepasse" in sortie, (
        f"le cas est tombe, mais pas sur le minuteur : le type de l'echec n'est pas celui "
        f"qui permet de compter les depassements a part.\n{sortie}"
    )
    assert "test_qui_boucle_en_python_pur" in sortie
    assert "n'a pas rendu la main" in sortie


@pytest.mark.skipif(
    not garde.MINUTEUR_DISPONIBLE,
    reason="SIGALRM/setitimer absents",
)
def test_le_minuteur_est_desarme_apres_chaque_cas():
    """ETABLIT : aucun minuteur ne reste arme entre deux cas.

    POPULATION : le processus qui execute ce cas-ci, entre l'appel precedent et celui-la.

    Un `setitimer` laisse arme apres un cas ferait tomber un cas ULTERIEUR, choisi au hasard
    par l'ordre de collecte -- et le releve accuserait le mauvais. Le crochet desarme dans un
    `finally` ; ce cas verifie que le desarmement a bien eu lieu, en lisant le temps qui reste
    au minuteur au moment ou le cas suivant commence.
    """
    import signal

    # Le crochet arme le minuteur AUTOUR de cet appel, donc il est arme maintenant : ce qui
    # reste doit etre positif et au plus le delai ordinaire. Ce qui serait fautif, c'est un
    # reste qui ne correspondrait a aucun des deux delais -- signe d'un minuteur herite.
    restant, _ = signal.getitimer(signal.ITIMER_REAL)
    assert 0.0 < restant <= garde.DELAI_ORDINAIRE, (
        f"il reste {restant} s au minuteur, pour un delai ordinaire de "
        f"{garde.DELAI_ORDINAIRE} s : le minuteur de ce cas n'est pas celui qu'on croit"
    )
