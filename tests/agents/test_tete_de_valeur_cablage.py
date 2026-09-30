"""La tete de valeur : sa FORME, son BRANCHEMENT, et la taille de la tete de politique.

Ce fichier ne dit pas si la tete de valeur predit bien -- ca, c'est la mesure de la phase 4.
Il dit que **la machine ne peut pas mentir en silence** sur trois points que la campagne de
mutation de l'etape 0 a trouves sans defense : la valeur rendue est-elle aplatie, sert-elle
vraiment de ligne de base a PPO, et la tete de politique a-t-elle exactement la taille de
l'espace d'action du moteur.

Les trois ont la meme propriete, et c'est pour ca qu'ils sont ensemble : **s'ils etaient faux,
rien ne leverait.** Une valeur non aplatie diffuse la MSE en `n x n` et rend une perte qui
descend quand meme. Une ligne de base debranchee laisse l'agent apprendre, plus lentement et
sur autre chose. Une tete trop grande donne des sorties qu'aucun etat ne rend legales.

Ces trois lignes sont **celles que l'iteration 1 de la phase 4 va modifier**. Un organe qu'on
repare sans que la suite sache qu'il est branche se repare a l'aveugle.
"""

from __future__ import annotations

import copy
import random

import torch
from torch import nn, optim

from agents import entrainement
from agents import reseau as reseau_module
from courtisans.engine import Engine
from courtisans.infoset import tenseur
from mesure.instance import ENTRAINEMENT_3J

CONFIG = ENTRAINEMENT_3J
APPAREIL = torch.device("cpu")


def _reseau(graine: int = 0) -> reseau_module.ReseauPolitiqueValeur:
    torch.manual_seed(graine)
    etat = Engine(CONFIG).reset(0)
    return reseau_module.ReseauPolitiqueValeur(
        len(tenseur(etat, 0)), 6 * 2 * (CONFIG.joueurs - 1)
    )


# ---------------------------------------------------------------------------------
# 1. La FORME de la valeur rendue
# ---------------------------------------------------------------------------------


def test_la_valeur_rendue_porte_une_valeur_par_ligne_et_pas_une_colonne():
    """ETABLIT : `forward` rend une valeur **aplatie**, forme `(n,)`, sur des lots de 1 a 7.

    POPULATION : sept lots d'observations aleatoires de la taille du moteur, n = 1..7.

    L'invariant est ecrit dans `reseau.forward` : « `valeurs` est aplatie : une valeur par
    ligne ». Une sortie `(n, 1)` a exactement les memes `n` nombres et se lit pareil ; elle ne
    se distingue qu'a la forme, ou plus loin, quand quelque chose la met face a un vecteur.
    """
    modele = _reseau()
    for n in range(1, 8):
        observations = torch.randn(n, modele.taille_observation)
        logits, valeurs = modele(observations)
        assert logits.shape == (n, modele.nb_actions)
        assert valeurs.dim() == 1, (
            f"lot de {n} : valeurs de dimension {valeurs.dim()}, forme "
            f"{tuple(valeurs.shape)} -- attendu une seule dimension"
        )
        assert valeurs.shape == (n,)


def test_la_perte_de_valeur_est_la_moyenne_des_n_erreurs_et_non_des_n_carre():
    """ETABLIT : `mse_loss(valeurs, retours)` vaut la moyenne des `n` erreurs de ligne.

    POPULATION : un lot de 6 observations aleatoires face a 6 retours distincts.

    C'est la CONSEQUENCE de la forme, et c'est elle qui compte : `nn.functional.mse_loss`
    diffuse. Une valeur en colonne `(n, 1)` face a des retours en vecteur `(n,)` produit une
    matrice `n x n` de differences croisees et une perte moyennee sur `n^2` termes dont `n^2-n`
    n'existent pas. **Rien ne leve, et la perte descend.** Le nombre attendu est recalcule ici
    a la main, terme a terme, sans passer par `mse_loss`.
    """
    modele = _reseau(graine=1)
    torch.manual_seed(7)
    n = 6
    observations = torch.randn(n, modele.taille_observation)
    retours = torch.tensor([-1.0, -0.5, 0.0, 0.25, 0.75, 1.0])

    _, valeurs = modele(observations)
    perte = nn.functional.mse_loss(valeurs, retours)

    plat = valeurs.reshape(-1).tolist()
    assert len(plat) == n
    attendu = sum((plat[i] - retours[i].item()) ** 2 for i in range(n)) / n

    assert perte.item() == torch.tensor(attendu).item() or abs(
        perte.item() - attendu
    ) < 1e-6, (
        f"perte {perte.item():.8f} pour une moyenne de {n} erreurs attendue a "
        f"{attendu:.8f} -- un ecart de ce genre est la signature d'une diffusion en n x n"
    )
    # Et le temoin de ce que la diffusion produirait, pour que le chiffre ci-dessus ne soit
    # pas un nombre sans echelle : la meme perte sur une valeur en colonne.
    diffuse = nn.functional.mse_loss(
        valeurs.reshape(n, 1).expand(n, n), retours.expand(n, n)
    )
    assert abs(diffuse.item() - attendu) > 1e-3, (
        "le lot tire ne separe pas les deux lectures : le cas ne prouverait rien"
    )


# ---------------------------------------------------------------------------------
# 2. Le BRANCHEMENT : la tete de valeur est la ligne de base de PPO
# ---------------------------------------------------------------------------------


def test_la_valeur_predite_change_la_perte_de_politique_donc_elle_sert_de_ligne_de_base():
    """ETABLIT : changer `V(s)` -- et rien d'autre -- change la perte de politique.

    POPULATION : une vague reelle de 24 parties d'entrainement, mise a jour deux fois depuis
    le MEME etat de modele et d'optimiseur, avec les memes observations, actions, masques,
    log-probabilites et gains ; seules les `valeurs` different.

    C'est **a quoi la tete de valeur sert**. Le module ecrit « a `lambda = 1` l'avantage vaut
    `R - V(s)` » : si c'est vrai, `V` entre dans l'avantage, donc dans la perte de politique,
    donc deux `V` distincts donnent deux pertes distinctes. Si la ligne de base etait
    debranchee, l'avantage vaudrait `R` seul et les deux pertes seraient **identiques au bit
    pres** -- et l'agent apprendrait quand meme, plus lentement, sans que rien ne le signale.

    Le cas ne regarde pas la valeur de la perte : il regarde qu'elle DEPEND de `V`.
    """
    modele = _reseau(graine=3)
    trajectoires, jouees = entrainement.jouer_une_vague(modele, [], 24, 900_000, APPAREIL)
    assert jouees == 24
    assert len(trajectoires) > 0

    depart = copy.deepcopy(modele.state_dict())

    def perte_de_politique_avec(valeurs: list[float]) -> float:
        clone = _reseau(graine=3)
        clone.load_state_dict(depart)
        vague = copy.deepcopy(trajectoires)
        vague.valeurs = valeurs
        optimiseur = optim.Adam(
            clone.parameters(), lr=entrainement.TAUX_APPRENTISSAGE
        )
        return entrainement.mettre_a_jour(
            clone, optimiseur, vague, APPAREIL, random.Random(0)
        )["politique"]

    nb = len(trajectoires)
    # Deux series de valeurs predites, toutes deux plausibles et de meme echelle que les
    # gains : ni l'une ni l'autre n'est degeneree, et elles ne different que par le profil.
    montante = [-1.0 + 2.0 * i / (nb - 1) for i in range(nb)]
    descendante = list(reversed(montante))

    avec_montante = perte_de_politique_avec(montante)
    avec_descendante = perte_de_politique_avec(descendante)

    assert avec_montante != avec_descendante, (
        f"deux lignes de base opposees donnent la meme perte de politique "
        f"({avec_montante!r}) : l'avantage ne soustrait pas V(s)"
    )
    # Et le controle de non-vacuite : la meme fonction, appelee deux fois sur la MEME serie,
    # rend bien deux fois le meme nombre. Sans lui, l'inegalite ci-dessus pourrait venir du
    # non-determinisme et non de la ligne de base.
    assert perte_de_politique_avec(montante) == avec_montante


def test_deux_vagues_qui_ne_different_que_par_leurs_gains_donnent_deux_avantages_distincts():
    """ETABLIT : le retour `R` entre lui aussi dans l'avantage -- le pendant du cas precedent.

    POPULATION : la meme vague reelle de 24 parties, gains remplaces par deux profils opposes.

    Ce cas existe pour que le precedent ne puisse pas etre satisfait par un avantage qui
    vaudrait `-V(s)` : `R - V(s)` demande les DEUX termes, et un cas par terme.
    """
    modele = _reseau(graine=3)
    trajectoires, _ = entrainement.jouer_une_vague(modele, [], 24, 900_000, APPAREIL)
    depart = copy.deepcopy(modele.state_dict())
    nb = len(trajectoires)

    def perte_de_politique_avec_gains(gains: list[float]) -> float:
        clone = _reseau(graine=3)
        clone.load_state_dict(depart)
        vague = copy.deepcopy(trajectoires)
        vague.gains = gains
        optimiseur = optim.Adam(
            clone.parameters(), lr=entrainement.TAUX_APPRENTISSAGE
        )
        return entrainement.mettre_a_jour(
            clone, optimiseur, vague, APPAREIL, random.Random(0)
        )["politique"]

    montants = [-1.0 + 2.0 * i / (nb - 1) for i in range(nb)]
    assert perte_de_politique_avec_gains(montants) != perte_de_politique_avec_gains(
        list(reversed(montants))
    )


# ---------------------------------------------------------------------------------
# 3. La TAILLE de la tete face a l'espace d'action du moteur
# ---------------------------------------------------------------------------------


def _indices_legaux_rencontres(donnes: int) -> set[int]:
    """Tous les indices d'action que le moteur rend legaux sur `donnes` parties jouees au hasard."""
    moteur = Engine(CONFIG)
    alea = random.Random(20250824)
    vus: set[int] = set()
    for donne in range(donnes):
        etat = moteur.reset(donne)
        while not etat.is_terminal():
            legales = etat.legal_actions()
            vus |= set(legales)
            etat.apply(alea.choice(legales))
    return vus


def test_la_tete_de_politique_a_exactement_la_taille_de_l_espace_d_action_du_moteur():
    """ETABLIT : les indices que le moteur rend legaux couvrent la tete, **exactement**.

    POPULATION : tous les nœuds de decision de 120 parties d'`entrainement-3j` jouees au
    hasard -- soit l'ensemble des indices que le moteur a rendus legaux au moins une fois.

    `construire` promet une taille « mesuree et non ecrite en dur », et dit ce qu'une mauvaise
    taille produirait : « un agent qui croit poser une carte et en pose une autre ». Le cas
    verifie les DEUX sens de l'egalite, ce qu'un controle sur le seul etat initial ne peut pas
    faire :

    - **aucun indice legal hors de la tete** -- une tete trop petite, et `masque` leverait ;
    - **aucune sortie de tete qu'aucun etat ne rend legale** -- une tete trop grande, et rien
      ne leve : le reseau porte des logits pour des actions qui n'existent pas, la politique
      leur donne une masse qui n'est jamais tiree, et l'entropie publiee compte des actions
      fantomes.

    Le second sens est celui qu'aucun cas ne tenait.
    """
    modele = entrainement.construire(APPAREIL)
    vus = _indices_legaux_rencontres(donnes=120)

    hors_tete = sorted(i for i in vus if i >= modele.nb_actions)
    assert not hors_tete, (
        f"le moteur rend legaux les indices {hors_tete}, hors d'une tete de "
        f"{modele.nb_actions} : l'agent choisirait une action que le reseau ne note pas"
    )

    jamais_legaux = sorted(set(range(modele.nb_actions)) - vus)
    assert not jamais_legaux, (
        f"la tete porte {modele.nb_actions} sorties dont {jamais_legaux} qu'aucun des nœuds "
        f"de 120 parties ne rend legales : la tete est plus grande que l'espace d'action"
    )


def test_construire_leve_si_le_moteur_expose_une_action_hors_de_la_tete():
    """ETABLIT : `construire` refuse de rendre un reseau dont la tete est trop PETITE.

    POPULATION : le seul etat initial d'`entrainement-3j`, avec un espace d'action rabote.

    C'est le sens que le controle de `construire` tient deja ; il est ecrit ici pour que le
    cas precedent, qui tient l'autre sens, ne passe pas pour un doublon.
    """
    import pytest

    etat = Engine(CONFIG).reset(0)
    plus_grand = max(etat.legal_actions())
    modele = entrainement.construire(APPAREIL)
    assert plus_grand < modele.nb_actions

    with pytest.raises(ValueError, match="hors de la tete"):
        reseau_module.masque([etat.legal_actions()], nb_actions=plus_grand)
