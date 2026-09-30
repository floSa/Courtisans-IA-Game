"""Le delai de garde de la suite : **un test qui boucle doit se distinguer d'un test lent.**

Pourquoi ce fichier existe
---------------------------
La campagne de mutation de la phase 4 a rendu un troisieme verdict, `EXPIRE` : la mutation
`masse-binomiale-part-de-zero` fait partir la recurrence de la loi binomiale de `k = 0`, le
premier terme vaut `1e-1760` -- zero en flottant -- et le balayage qui cherche le `n` d'une
puissance cible ne converge jamais. La suite n'a **rendu aucun verdict**. Elle a tourne
2 h 48 sur une passe qui en prend moins de trois, et rien dans `tests` ne l'a signale : il a
fallu que `outillage/mutation.py`, qui est exterieur, se dote d'un minuteur.

`EXPIRE` est un etat de l'OUTIL. Il ne doit pas devenir la case ou l'on range ce qu'on ne sait
pas -- et pour qu'il n'y serve pas, il faut que la suite sache elle-meme dire « ce cas ne
finit pas ». C'est ce que ce fichier fait, et il le fait pour toute la suite et pas pour le
seul cas qui a revele le manque : `mesure/binomiale.py` dimensionne un budget, et l'iteration 1
de la phase 4 pre-inscrit un budget.

Ce que le minuteur PEUT voir, et ce qu'il ne peut pas
------------------------------------------------------
Le minuteur est `signal.setitimer(ITIMER_REAL)` : le systeme envoie `SIGALRM` au bout du delai
et le gestionnaire leve **dans le cas lui-meme**, avec sa pile complete. Le cas echoue, et la
suite continue -- c'est la difference avec un minuteur de processus, qui tuerait le reste de la
campagne et rendrait le releve inutilisable.

Il ne voit pas tout, et le dire fait partie de la parade :

- **Un appel bloquant en C ne rend pas la main a l'interpreteur.** Un produit matriciel de
  torch, un `subprocess.run` sans `timeout`, une lecture sur un socket : le signal est bien
  delivre, mais le gestionnaire Python ne s'execute qu'au retour dans l'interpreteur. Un cas
  bloque **la** ne sera pas interrompu. La boucle de `binomiale`, elle, est du Python pur.
- **Il ne mesure rien.** Il ne dit pas qu'un cas est lent, il dit qu'un cas a depasse un delai.
  Le releve des durees se lit avec `--durations`, pas ici.
- **Il ne s'arme pas hors d'un systeme POSIX.** La ou `SIGALRM` n'existe pas, ce fichier ne
  protege rien -- et `MINUTEUR_DISPONIBLE` le dit, plutot que de laisser croire a une garde
  absente.

Le delai, et d'ou il sort
---------------------------
**MESURE le 24/08/2026**, `uv run pytest -q --durations=30`, **trois passes**, sur la machine
du projet. Suite entiere : 166,34 / 163,17 / 168,19 s. Le cas le plus lent est le meme aux
trois passes -- `tests/agents/test_campagne.py::test_le_garde_fou_du_RUN_REEL_ne_declenche_sur_aucun_checkpoint`
--, a **13,76 / 13,40 / 14,70 s**, soit une etendue de 1,30 s pour un maximum de **14,70 s**.

**Un seul delai, et non deux, et c'est la mesure qui l'a decide.** L'intention etait d'en
donner un plus large aux cas marques `lent` (critere A3). Les trois passes disent que le
marqueur ne designe pas les cas lents : les cinq cas marques plafonnent a **2,90 s**
(`test_l_echelle_dagregation_sur_son_propre_code`), quand le plus lent de la suite, **cinq fois
plus long**, n'en porte aucun. Un second delai indexe sur ce marqueur aurait elargi la garde
la ou elle n'est pas necessaire et l'aurait laissee etroite la ou elle l'est. Le marqueur dit
« gros volume de parties », pas « long » -- ce n'est pas un defaut du marqueur, c'est un
contresens sur ce qu'il nomme, et il a failli entrer ici.

Un cas qui a besoin de plus se marque `minuteur(secondes=...)` **avec la mesure qui le
justifie**, et non en relevant le delai de toute la suite.
"""

from __future__ import annotations

import signal
from collections.abc import Iterator

import pytest

#: Vrai la ou `SIGALRM` et `setitimer` existent. Faux ailleurs, et alors **rien n'est arme**.
MINUTEUR_DISPONIBLE: bool = hasattr(signal, "SIGALRM") and hasattr(signal, "setitimer")

#: Le facteur applique au cas le plus lent mesure. **Quatre**, et pas un chiffre de confort :
#: l'etendue des trois passes est de 1,30 s sur 14,70, soit 9 % ; un facteur 2 laisserait la
#: garde a 29 s, ce qu'une machine deux fois plus lente que celle-ci franchirait sans qu'aucun
#: code ne soit faux. A quatre, la suite tolere une machine quatre fois plus lente, et une
#: boucle infinie coute **moins d'une minute** au lieu des 15 minutes du minuteur de
#: `outillage/mutation.py`, ou des 2 h 48 sans minuteur du tout.
FACTEUR_DU_DELAI: float = 4.0

#: Le cas le plus lent de la suite, **MESURE**, maximum des trois passes du 24/08/2026.
CAS_LE_PLUS_LENT_MESURE: float = 14.70

#: Le delai de garde d'un cas. Il n'est pas rond, et c'est voulu : il est le produit d'une
#: mesure par un facteur, tous deux ecrits au-dessus. `58,8 s = 4 x 14,70 s`.
DELAI_ORDINAIRE: float = FACTEUR_DU_DELAI * CAS_LE_PLUS_LENT_MESURE


class DelaiDeGardeDepasse(Exception):
    """Un cas n'a pas rendu la main dans son delai. **Ce n'est pas un echec d'assertion.**

    Le type est distinct pour que le releve puisse compter les depassements a part : un cas
    qui boucle et un cas qui affirme quelque chose de faux ne demandent pas le meme travail,
    et les confondre est exactement ce qui a coute 2 h 48.
    """


def delai_pour(item: pytest.Item) -> float:
    """Le delai de ce cas-la : l'ordinaire, sauf marqueur `minuteur(secondes=...)` explicite.

    Le marqueur ne se pose pas pour faire passer un cas : il se pose avec la mesure qui le
    justifie, ecrite dans la docstring du cas. Un delai releve sans mesure est un delai qui
    n'attrapera plus rien.
    """
    marqueur = item.get_closest_marker("minuteur")
    if marqueur is not None:
        return float(marqueur.kwargs["secondes"])
    return DELAI_ORDINAIRE


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item: pytest.Item) -> Iterator[None]:
    """Arme le minuteur autour de l'APPEL du cas, pas autour de ses fixtures.

    Le decoupage est volontaire : une fixture partagee coute son temps une fois pour plusieurs
    cas, et le compter dans le delai du premier ferait echouer un cas pour ce qu'un autre lui
    a demande.
    """
    delai = delai_pour(item)
    if not MINUTEUR_DISPONIBLE or delai <= 0.0:
        yield
        return

    def au_delai(numero, pile):  # noqa: ANN001, ARG001
        raise DelaiDeGardeDepasse(
            f"{item.nodeid} n'a pas rendu la main en {delai:.1f} s. "
            f"Le cas le plus lent de la suite pese {CAS_LE_PLUS_LENT_MESURE:.2f} s mesurees. "
            f"Si ce cas-ci est legitimement plus long, marque-le "
            f"`@pytest.mark.minuteur(secondes=...)` en donnant la mesure qui le justifie -- "
            f"ne releve pas le delai de toute la suite sans elle."
        )

    ancien = signal.signal(signal.SIGALRM, au_delai)
    signal.setitimer(signal.ITIMER_REAL, delai)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, ancien)
