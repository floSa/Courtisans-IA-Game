"""Les garde-fous de `experiences/` : ce qui doit rester vrai pour que ses chiffres vaillent.

Chaque propriete porte son temoin positif : un controle qui ne peut pas echouer ne prouve rien.

1. `tenseur_rapide` rend `infoset.tenseur` bit a bit -- sinon les agents ne voient pas ce que
   le depot croit qu'ils voient.
2. La determinisation PIMC est aveugle : re-tirer les dos adverses et la pioche ne change pas
   le tenseur du siege, alors que le plateau reel, lui, change.
3. L'agent d'apres-coup est aveugle AU CIBLAGE : sa decision ne depend pas de l'identite
   reelle des dos. Sans le correctif du 27/09 elle en dependait (temoin `aveugle=False`).
4. La permutation des familles laisse gains et scores invariants (C18), ce qui rend
   l'augmentation de `experiences.iteration` legitime.
5. **Caracterisation d'un defaut du tenseur officiel** : au ciblage, il ne dit pas quelle
   carte porte l'indice « cible i ». Si ce test tombe, le defaut a ete corrige -- tant mieux,
   et le paragraphe 3.4 de `experiences/REVUE_CRITIQUE.md` est a mettre a jour.
"""

from __future__ import annotations

import random

import pytest

from courtisans.cards import Role
from courtisans.config import GameConfig
from courtisans.engine import Engine, Phase
from courtisans.infoset import tenseur
from mesure.instance import ENTRAINEMENT_3J

torch = pytest.importorskip("torch")

from experiences.iteration import permuter_familles  # noqa: E402
from experiences.pimc import determiniser, greedy_rollout  # noqa: E402
from experiences.rapide import appliquer, tenseur_rapide  # noqa: E402
from experiences.valeur import agent_valeur  # noqa: E402

COMPLETE = GameConfig(familles=6, roles=tuple(Role), exemplaires=3, joueurs=3)
V1B = "experiences/modeles/v1b.pt"


def _parties(config, nb, depart, politique="aleatoire"):
    """Rend chaque etat de `nb` parties, terminal compris."""
    moteur = Engine(config)
    for d in range(nb):
        rng = random.Random(d)
        etat = moteur.reset(depart + d)
        glouton = greedy_rollout(random.Random(d))
        while True:
            yield etat
            if etat.is_terminal():
                break
            if politique == "greedy":
                action = glouton(etat)
            else:
                action = rng.choice(etat.legal_actions())
            appliquer(etat, action)


@pytest.mark.parametrize("config", [ENTRAINEMENT_3J, COMPLETE], ids=["reduite", "complete"])
def test_tenseur_rapide_egal_au_tenseur_officiel(config):
    vus = 0
    for etat in _parties(config, 20, 9_800_000):
        for j in range(config.joueurs):
            assert tenseur_rapide(etat, j) == tenseur(etat, j)
            vus += 1
    assert vus > 20 * 30  # il a bien inspecte des etats, pas une partie vide


def test_determinisation_aveugle_avec_temoin():
    inspecte = plateau_change = 0
    for etat in _parties(ENTRAINEMENT_3J, 25, 9_700_000, "greedy"):
        moi = 0 if etat.is_terminal() else etat.current_player()
        monde = determiniser(etat, moi, random.Random(inspecte))
        assert tenseur(monde, moi) == tenseur(etat, moi)
        inspecte += 1
        plateau_change += [p.carte for p in monde._posees] != [p.carte for p in etat._posees]
    assert plateau_change > 0.3 * inspecte, "le brouilleur ne brouille rien : temoin mort"


def test_agent_valeur_aveugle_au_ciblage_avec_temoin():
    noeuds = differe_corrige = differe_temoin = 0
    for etat in _parties(ENTRAINEMENT_3J, 60, 9_600_000, "greedy"):
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
                vrai = agent_valeur(random.Random(k), V1B, aveugle=aveugle)(etat)
                faux = agent_valeur(random.Random(k), V1B, aveugle=aveugle)(monde)
                if aveugle:
                    differe_corrige += vrai != faux
                else:
                    differe_temoin += vrai != faux
    assert noeuds >= 20
    assert differe_corrige == 0
    assert differe_temoin > 0, "le temoin ne triche pas : ce test ne verrait pas la fuite"


def test_permutation_des_familles_laisse_les_gains_invariants():
    termines = [e for e in _parties(COMPLETE, 15, 9_500_000, "greedy") if e.is_terminal()]
    for i, etat in enumerate(termines):
        perm = list(range(COMPLETE.familles))
        random.Random(i).shuffle(perm)
        m = permuter_familles(etat, perm)
        assert m.returns() == etat.returns()
        assert m.scores() == etat.scores()
        assert tenseur_rapide(m, 0) != tenseur_rapide(etat, 0) or perm == sorted(perm)


def test_CARACTERISATION_le_tenseur_officiel_ne_dit_pas_qui_est_la_cible_i():
    """Inverser l'ordre d'arrivee des cartes de la zone change la carte designee par chaque
    indice de ciblage, et ne change pas le tenseur. Mesure au paragraphe 3.4 de la revue :
    64 % des noeuds de ciblage en jeu greedy."""
    aveugles = 0
    for etat in _parties(ENTRAINEMENT_3J, 40, 7_000_000, "greedy"):
        if etat.phase() is not Phase.CIBLAGE:
            continue
        cibles = etat.cibles_courantes()
        if len({(p.carte.famille, p.carte.role) for p in cibles}) < 2:
            continue
        zone = etat.assassin_en_resolution().zone
        m = etat.clone()
        dans = [p for p in m._posees if p.zone == zone]
        m._posees = [p for p in m._posees if p.zone != zone] + dans[::-1]
        j = etat.current_player()
        if [p.carte for p in m.cibles_courantes()] != [p.carte for p in cibles]:
            assert tenseur(m, j) == tenseur(etat, j)
            aveugles += 1
    assert aveugles >= 10


def test_cibles_td_lambda_1_redonne_monte_carlo_et_respecte_les_episodes():
    """Les retours TD(lambda) de `experiences.iteration` : a lambda = 1 ils valent le gain
    final ; a lambda < 1 la vue terminale garde le gain reel, les autres s'en ecartent, et
    une vue augmentee recoit exactement la cible de son originale."""
    import numpy as np

    from experiences.iteration import _jouer_lot, cibles_td
    from experiences.valeur import V as Reseau

    X, G, M, E, T, A = _jouer_lot((V1B, [], 9_400_000, 3, 0.05, 1, 0.3, 0.4))
    b = {"X": X, "G": G, "M": M, "E": E, "T": T, "A": A}
    net = Reseau()
    net.load_state_dict(torch.load(V1B, map_location="cpu"))
    dev = torch.device("cpu")
    assert np.allclose(cibles_td(b, net, 1.0, dev), G)
    c = cibles_td(b, net, 0.7, dev)
    derniers = [np.flatnonzero(E == e)[-1] for e in np.unique(E)]
    assert np.allclose(c[derniers], G[derniers])
    assert not np.allclose(c, G)
    aug = np.flatnonzero(A == 1)
    assert len(aug) > 0 and np.array_equal(c[aug], c[aug - 1])
    assert np.all(A[aug - 1] == 0) and np.all(E[aug] == E[aug - 1]) and np.all(T[aug] == T[aug - 1])
