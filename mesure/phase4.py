"""L'instrument de la phase 4, iteration 1 : la tete de valeur. **Il ne decide rien.**

Ce module produit les deux grandeurs de l'iteration 1 et **une seule tranche**.

Le seuil INTERMEDIAIRE, diagnostique
--------------------------------------
Le R2 du critique, **hors plage d'entrainement**, par la methode de la phase 3 : MSE sur la
variance des retours, sur les nœuds. Il dit si la reparation a repare ce qu'elle visait.

**Ce n'est pas un niveau, c'est un ECART APPARIE, et il porte sa lateralite.** La barre n'est
pas « R2 superieur a *x* » : c'est l'ecart de R2 entre le critique neuf et celui de la phase 3,
**sur le meme echantillon hors plage**, borne basse de l'IC 99 % bootstrap par donne
strictement positive. Trois raisons, toutes du paragraphe 0.2 :

- un niveau se compare a une population que sa phrase ne nomme pas ; un ecart nomme ses deux
  termes ;
- l'appariement par donne annule la variance de l'echantillon, qui est **la meme** pour les
  deux critiques -- c'est tout l'interet, et c'est pour ca que l'echantillon est fixe ;
- on cherche une **amelioration** : la borne basse suffit, et la lateralite fait partie du
  chiffre.

**Le 0,57 de l'auditeur n'apparait dans aucun denominateur de ce module.** Il est calcule sur
l'etat COMPLET ; un critique qui ne voit qu'un info-set ne peut pas l'atteindre, et personne ne
sait de combien il en est loin. C'est une borne superieure de contexte, jamais une cible et
jamais un diviseur.

Le seuil DECISIF, et il est ailleurs
--------------------------------------
Le gain moyen contre **deux copies de l'agent de la phase 3**, sieges permutes, borne basse de
l'IC 99 % bootstrap par donne strictement positive. Il se mesure avec
`mesure.phase3.jouer_composition` et `mesure.bootstrap`, qui existent deja et qui ne sont pas
reecrits ici -- le paragraphe 2 des conventions interdit la seconde definition.

**Le piege de cette iteration, ecrit ici parce que c'est ici qu'on serait tente de l'oublier :
on peut faire monter le R2 sans que l'agent joue mieux.** Un R2 qui monte et un gain qui ne
bouge pas est un resultat publiable, et il etablirait que le critique n'etait pas la limite.

L'echantillon hors plage est FIXE, et ce choix se paie
-------------------------------------------------------
Les nœuds sont ceux que visite la politique de l'agent de la phase 3, hors plage. Les deux
critiques sont ensuite evalues sur **ces memes observations**.

C'est ce qui rend l'appariement possible. C'est aussi une limite qu'il faut nommer : l'agent
neuf visitera une **autre** distribution d'etats, et ce chiffre ne dit rien de sa qualite de
prediction sur la sienne. Il dit « sur une distribution de reference fixee, lequel des deux
predit le mieux », et pas autre chose.
"""

from __future__ import annotations

import hashlib
import random
import statistics
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import torch

from agents import entrainement
from mesure import bootstrap as boot

#: L'adversaire du seuil decisif. **Il n'est pas dans le depot** -- `models/` est ignore, et
#: 500 Ko de binaire n'ont rien a y faire. C'est donc son IDENTITE qui y est, et un cas la
#: verifie : sans elle, un jour, le juge decisif tournerait contre un autre adversaire que
#: celui qu'il nomme, et rien ne le dirait.
CHEMIN_AGENT_PHASE3 = "models/phase3/final.pt"
EMPREINTE_AGENT_PHASE3 = (
    "772a869fa2c10c9d28fd6d9d70f3a7aa555f18c27f4075b664c4d183f83f0217"
)
OCTETS_AGENT_PHASE3 = 503_025

#: La RECETTE qui le reproduit, parce qu'une empreinte prouve l'identite et ne dit pas
#: comment refaire le fichier.
RECETTE_AGENT_PHASE3 = (
    "uv run python -m agents.campagne --dossier models/phase3 "
    "(phase 3, run du 21/08/2026, plafond 2 h, checkpoint toutes les 15 min)"
)

#: Le bloc de seeds de l'echantillon hors plage. Disjoint de tout ce que la phase 3 emploie :
#: 100 000+ entrainement, 60 000+ verdict, 70 000+ pool, 40 000+ garde-fou, 5 000 000+ le
#: hors-plage de l'auditeur.
DEPART_HORS_PLAGE = 7_000_000

#: Les trois passes prennent trois blocs DISJOINTS : une vague de `PARTIES_HORS_PLAGE` parties
#: consomme autant de donnes, et 100 000 les separent largement.
ECART_ENTRE_PASSES = 100_000

#: **MESURE le 24/08/2026.** A 500 parties le R2 du critique de la phase 3 va de +0,0922 a
#: +0,1249 sur trois passes -- une etendue de 0,033, trop large pour fonder un seuil. A 4 000
#: parties il va de +0,1005 a +0,1008, **etendue 0,0003**, pour 14,9 a 15,1 s par passe. Le
#: budget est choisi sur cette mesure, pas sur un chiffre rond.
PARTIES_HORS_PLAGE = 4_000

#: Le bloc de seeds du dimensionnement, disjoint du precedent.
DEPART_DIMENSIONNEMENT = 6_000_000
DECALAGE_ADVERSAIRE_DIMENSIONNEMENT = 6_500_000

#: Rechantillonnages du bootstrap. Le meme nombre que la phase 3 : ce n'est pas un reglage de
#: cette iteration, et le changer melangerait deux variables.
RECHANTILLONS = 10_000

#: La graine du bootstrap de l'ecart de R2. Distincte de celles de la phase 3.
GRAINE_BOOTSTRAP_R2 = 4_100_001


def empreinte(chemin: str | Path) -> str:
    """Le SHA-256 d'un fichier, en hexadecimal."""
    condensat = hashlib.sha256()
    with open(chemin, "rb") as fichier:
        for bloc in iter(lambda: fichier.read(1 << 20), b""):
            condensat.update(bloc)
    return condensat.hexdigest()


def verifier_l_agent_de_la_phase3(chemin: str = CHEMIN_AGENT_PHASE3) -> str:
    """Rend l'empreinte du fichier present, ou **leve** si ce n'est pas le bon adversaire.

    Raises:
        FileNotFoundError: si le fichier manque. Il n'est pas dans le depot et il n'est pas
            sauvegarde ; `RECETTE_AGENT_PHASE3` dit comment le refaire, et rien n'etablit
            qu'on retomberait sur les memes poids.
        ValueError: si l'empreinte differe. **Le seuil qui tranche l'iteration se mesure
            contre ce fichier** : le laisser passer, c'est publier un gain contre un
            adversaire que le rapport ne nomme pas.
    """
    fichier = Path(chemin)
    if not fichier.exists():
        raise FileNotFoundError(
            f"{chemin} est absent. C'est l'adversaire du seuil DECISIF de l'iteration 1, il "
            f"n'est pas suivi par git et il n'est pas sauvegarde. Recette : "
            f"{RECETTE_AGENT_PHASE3}"
        )
    trouvee = empreinte(fichier)
    if trouvee != EMPREINTE_AGENT_PHASE3:
        raise ValueError(
            f"{chemin} n'est pas l'agent de la phase 3.\n"
            f"  attendu : {EMPREINTE_AGENT_PHASE3}\n"
            f"  trouve  : {trouvee}\n"
            f"Le seuil qui tranche l'iteration se mesure contre ce fichier. Un gain publie "
            f"contre un autre adversaire est un chiffre exact sur une population que sa "
            f"phrase ne nomme pas."
        )
    return trouvee


@dataclass(frozen=True)
class EchantillonHorsPlage:
    """Les nœuds sur lesquels les deux critiques sont compares. **Fixe, et le meme pour les deux.**

    Attributes:
        observations: l'info-set de chaque nœud de decision, tel que le moteur le rend.
        retours: le gain terminal du siege qui decidait a ce nœud -- la cible du critique.
        donnes: la donne d'ou vient le nœud. **C'est l'unite de rechantillonnage**, jamais le
            nœud : deux nœuds d'une meme partie ne sont pas independants.
        depart: le premier seed du bloc, pour que la population soit nommee.
        nb_parties: le nombre de parties jouees.
    """

    observations: tuple[tuple[float, ...], ...]
    retours: tuple[float, ...]
    donnes: tuple[int, ...]
    depart: int
    nb_parties: int

    def __len__(self) -> int:
        return len(self.retours)

    def intitule(self) -> str:
        """La population en toutes lettres. Recopiee dans le rapport, jamais reecrite."""
        return (
            f"{self.nb_parties} parties de self-play a 3 copies de l'agent de la phase 3, "
            f"HORS plage d'entrainement, seeds {self.depart}+, {len(self)} nœuds"
        )


def echantillon_hors_plage(
    modele, depart: int = DEPART_HORS_PLAGE, parties: int = PARTIES_HORS_PLAGE
) -> EchantillonHorsPlage:
    """Joue un bloc hors plage et rend ses nœuds. **Le pool est vide, donc c'est du self-play.**

    Les trois sieges sont joues par la politique de `modele` : la composition de l'auditeur de
    la phase 3, et la distribution d'etats de reference sur laquelle les deux critiques sont
    compares.
    """
    trajectoires, jouees = entrainement.jouer_une_vague(
        modele, [], parties, depart, torch.device("cpu")
    )
    return EchantillonHorsPlage(
        observations=tuple(tuple(o) for o in trajectoires.observations),
        retours=tuple(trajectoires.gains),
        donnes=tuple(trajectoires.donnes),
        depart=depart,
        nb_parties=jouees,
    )


def valeurs_predites(modele, observations: Sequence[Sequence[float]]) -> tuple[float, ...]:
    """`V(s)` d'un critique sur des observations deja collectees, par lots de 4096."""
    predites: list[float] = []
    with torch.no_grad():
        for debut in range(0, len(observations), 4096):
            lot = torch.tensor(
                [list(o) for o in observations[debut : debut + 4096]],
                dtype=torch.float32,
            )
            _, valeurs = modele(lot)
            predites += valeurs.reshape(-1).tolist()
    return tuple(predites)


def r2(retours: Sequence[float], predites: Sequence[float]) -> float:
    """`1 - MSE / Var(retours)`. **La methode de la phase 3, sans un mot de plus.**

    Raises:
        ValueError: si les deux suites n'ont pas la meme longueur, ou si la variance des
            retours est nulle. Un R2 sur une variance nulle n'est pas « parfait » : il n'est
            pas defini, et le rendre `1.0` publierait une conclusion que rien n'a calculee.
    """
    if len(retours) != len(predites):
        raise ValueError(
            f"{len(retours)} retours pour {len(predites)} predictions : le R2 comparerait "
            f"deux populations"
        )
    if len(retours) < 2:
        raise ValueError(f"{len(retours)} nœud(s) : une variance ne se mesure pas la-dessus")
    variance = statistics.pvariance(retours)
    if variance <= 0.0:
        raise ValueError(
            "la variance des retours est nulle : le R2 n'est pas defini, et le rendre 1,0 "
            "publierait une conclusion que rien n'a calculee"
        )
    mse = statistics.fmean((r - v) ** 2 for r, v in zip(retours, predites))
    return 1.0 - mse / variance


def _par_donne(
    echantillon: EchantillonHorsPlage,
    avant: Sequence[float],
    apres: Sequence[float],
) -> list[list[tuple[float, float, float]]]:
    """Regroupe les nœuds par donne. **La donne est l'unite de rechantillonnage.**"""
    groupes: dict[int, list[tuple[float, float, float]]] = {}
    for donne, retour, a, b in zip(echantillon.donnes, echantillon.retours, avant, apres):
        groupes.setdefault(donne, []).append((retour, a, b))
    return [groupes[cle] for cle in sorted(groupes)]


def ecart_apparie_de_r2(
    echantillon: EchantillonHorsPlage,
    predites_avant: Sequence[float],
    predites_apres: Sequence[float],
    repetitions: int = RECHANTILLONS,
    alea: random.Random | None = None,
    risque: float = 0.01,
) -> boot.EcartApparie:
    """L'ecart de R2 entre deux critiques, sur le MEME echantillon, bootstrap par DONNE.

    **Le R2 n'est pas une moyenne, donc il ne s'apparie pas nœud a nœud.** C'est un rapport
    d'agregats : on rechantillonne les DONNES, on recalcule les deux R2 sur chaque
    rechantillon, et l'ecart de ce couple est la grandeur dont on prend l'intervalle. Un
    bootstrap qui tirerait des nœuds ignorerait que deux nœuds d'une meme partie portent le
    **meme** retour terminal, et rendrait un intervalle bien trop etroit.

    Rend un `bootstrap.EcartApparie`, donc le predicat `progres_etabli` est celui du projet et
    n'est pas recopie ici -- c'est la lecon des cinq versions du garde-fou.
    """
    alea = alea or random.Random(GRAINE_BOOTSTRAP_R2)
    groupes = _par_donne(echantillon, predites_avant, predites_apres)
    if len(groupes) < 2:
        raise ValueError(
            f"{len(groupes)} donne(s) : un bootstrap par donne ne se fait pas la-dessus"
        )

    def _r2_du_tirage(indices: Sequence[int]) -> tuple[float, float]:
        retours: list[float] = []
        avant: list[float] = []
        apres: list[float] = []
        for indice in indices:
            for retour, a, b in groupes[indice]:
                retours.append(retour)
                avant.append(a)
                apres.append(b)
        return r2(retours, avant), r2(retours, apres)

    observe_avant, observe_apres = _r2_du_tirage(range(len(groupes)))
    observe = observe_apres - observe_avant

    ecarts: list[float] = []
    for _ in range(repetitions):
        indices = [alea.randrange(len(groupes)) for _ in range(len(groupes))]
        try:
            tire_avant, tire_apres = _r2_du_tirage(indices)
        except ValueError:  # pragma: no cover -- variance nulle sur un tirage degenere
            continue
        ecarts.append(tire_apres - tire_avant)

    ecarts.sort()
    bas = ecarts[int(risque / 2 * len(ecarts))]
    haut = ecarts[min(len(ecarts) - 1, int((1 - risque / 2) * len(ecarts)))]
    return boot.EcartApparie(
        moyenne=observe, nb_donnes=len(groupes), intervalle=(bas, haut)
    )


__all__ = [
    "CHEMIN_AGENT_PHASE3",
    "DEPART_HORS_PLAGE",
    "EMPREINTE_AGENT_PHASE3",
    "EchantillonHorsPlage",
    "PARTIES_HORS_PLAGE",
    "RECETTE_AGENT_PHASE3",
    "ecart_apparie_de_r2",
    "echantillon_hors_plage",
    "empreinte",
    "r2",
    "valeurs_predites",
    "verifier_l_agent_de_la_phase3",
]
