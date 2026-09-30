"""Les garde-fous de `experiences/statuts.py` (cible auxiliaire des statuts finaux).

1. Avec des statuts CERTAINS (ceux d'aujourd'hui), l'ecart espere redonne exactement l'ecart du
   tenseur : la formule du « greedy probabiliste » contient bien le decompte du greedy.
2. Les donnees generees sont bien formees : un statut final par partie, repete sur toutes ses
   vues, classes 0 a 2.
3. L'agent a statuts est aveugle AU CIBLAGE (meme discipline que `agent_valeur`), avec son
   temoin positif : sans les mondes tires a l'aveugle, sa decision depend de l'identite des dos.
4. Il joue des parties completes, toujours legalement.
"""
from __future__ import annotations

import random

import numpy as np
import pytest

from courtisans.cards import Role
from courtisans.engine import Engine, Phase
from courtisans.infoset import tenseur
from mesure.instance import ENTRAINEMENT_3J

torch = pytest.importorskip("torch")

from experiences.pimc import determiniser, greedy_rollout  # noqa: E402
from experiences.statuts import (  # noqa: E402
    F,
    J,
    Reseau,
    _lot,
    agent_statuts,
    ecart_espere,
    vue_domaines,
)


@pytest.fixture(scope="module")
def modele(tmp_path_factory):
    chemin = tmp_path_factory.mktemp("statuts") / "alea.pt"
    torch.manual_seed(0)
    torch.save(Reseau().state_dict(), chemin)
    return str(chemin)


def _etats(nb, depart):
    moteur = Engine(ENTRAINEMENT_3J)
    for d in range(nb):
        etat = moteur.reset(depart + d)
        glouton = greedy_rollout(random.Random(d))
        while True:
            yield etat
            if etat.is_terminal():
                break
            etat.apply(glouton(etat))


def test_statuts_certains_redonnent_le_decompte_du_tenseur():
    vus = 0
    for etat in _etats(15, 9_900_000):
        for j in range(J):
            signe, dom = vue_domaines(etat, j)
            certain = np.eye(3)[signe + 1][None]
            assert ecart_espere(certain, dom[None])[0] == pytest.approx(tenseur(etat, j)[-1])
            vus += 1
    assert vus > 15 * 30


def test_donnees_bien_formees():
    d = _lot(([(1, ["experiences.pimc:greedy_rollout"] * J)], 9_900_100, 3, 0.0))
    n = len(d["X"])
    assert n > 3 * 30
    assert d["S"].shape == (n, F) and set(np.unique(d["S"])) <= {0, 1, 2}
    assert d["D"].shape == (n, J, F)
    for partie in np.unique(d["P"]):
        lignes = d["S"][d["P"] == partie]
        assert (lignes == lignes[0]).all(), "le statut final doit etre le meme sur toutes les vues"


def test_agent_statuts_aveugle_au_ciblage_avec_temoin(modele):
    noeuds = differe_corrige = differe_temoin = 0
    for etat in _etats(60, 9_910_000):
        if etat.phase() is not Phase.CIBLAGE:
            continue
        moi = etat.current_player()
        if not any(p.carte.role is Role.ESPION and p.poseur != moi
                   for p in etat.cibles_courantes()):
            continue
        noeuds += 1
        for k in range(2):
            monde = determiniser(etat, moi, random.Random(100 + k))
            for aveugle in (True, False):
                kw = {"poids_valeur": 1.0, "aveugle": aveugle}
                vrai = agent_statuts(random.Random(k), modele, **kw)(etat)
                faux = agent_statuts(random.Random(k), modele, **kw)(monde)
                if aveugle:
                    differe_corrige += vrai != faux
                else:
                    differe_temoin += vrai != faux
    assert noeuds >= 20
    assert differe_corrige == 0
    assert differe_temoin > 0, "le temoin ne triche pas : ce test ne verrait pas la fuite"


def test_agent_statuts_joue_une_partie_legale(modele):
    moteur = Engine(ENTRAINEMENT_3J)
    etat = moteur.reset(9_920_000)
    pols = [agent_statuts(random.Random(j), modele, poids_valeur=1.0) for j in range(J)]
    while not etat.is_terminal():
        a = pols[etat.current_player()](etat)
        assert a in etat.legal_actions()
        etat.apply(a)
