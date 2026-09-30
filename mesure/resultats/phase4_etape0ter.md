# Phase 4, etape 0 ter -- les neuf trous combles, et celui qui a resiste au cas ecrit pour lui

**MESURE le 24/08/2026**, `uv run python outillage/mutation.py --noms ...`, sur la branche
`phase-4-tete-de-valeur`. Chaque mutation = une passe entiere de la suite.

| | |
|---|---|
| **passe de BASE du rejeu des dix** | **1276 verts, 0 rouge** (cible `tests`) |
| **passe de BASE du rejeu apres correction** | **1278 verts, 0 rouge** |
| **TEMOINS, les 20 fichiers mutes edites sans effet** | identiques a la base aux deux rejeux |
| cas ajoutes a l'etape 0 ter | **27** (22 pour les neuf trous, 5 pour le minuteur) |

> **Le compte de base est en tete parce que les verdicts sont des ECARTS lus contre lui.**

## Le tableau avant / apres

L'etat « avant » est celui du jeu 5, releve accepte de l'etape 0
(`mutations_campagne_VALIDE_jeu5.log`, base 1251).

| Mutation | Avant | Apres | Rouges |
|---|---|---|---:|
| `perception-decide-sur-un-noeud-de-chance` | SURVIT | **detectee** | 2 |
| `valeur-non-aplatie` | SURVIT | **detectee** | 2 |
| `avantage-sans-ligne-de-base` | SURVIT | **detectee** | 1 |
| `tete-plus-grande-que-l-espace-d-action` | SURVIT | **detectee** | 1 |
| `garde-fou-se-contente-d-un-ecart-etabli` | SURVIT | **detectee** | 1 |
| `garde-fou-sans-bonferroni` | SURVIT | **detectee** | 1 |
| `pool-garde-les-plus-anciens` | SURVIT | **detectee** | 1 |
| `adversaires-partagent-un-alea` | SURVIT | **detectee** | 2 |
| `masse-binomiale-part-de-zero` | **EXPIRE** | **detectee** | 11 |
| `politique-reseau-observe-le-siege-zero` | SURVIT | **SURVIT encore**, puis detectee | 0, puis 1 |

**Neuf sur dix au premier rejeu. La dixieme est le resultat qui vaut le plus, et elle a son
paragraphe.**

## Celle qui a survecu au cas ecrit pour elle

`politique-reseau-observe-le-siege-zero` a **survecu au rejeu**, alors qu'un cas avait ete
ecrit pour elle et qu'il etait vert sur code sain. C'est le cas que le §4 de l'arbitrage
annonce comme « le resultat le plus interessant du lot », et il s'est produit.

**La cause est dans le cas, pas dans le code mesure.** `agents/politique_reseau.py` a **deux
portes d'entree** -- `politique_reseau`, qui echantillonne, et `politique_reseau_deterministe`.
La docstring de module enonce son invariant pour les deux : « Cette fonction ecrit
`tenseur(etat, etat.current_player())` ». Le cas ne parcourait que la deterministe -- celle
qui est, de son propre aveu, « rapportee a cote, jamais a sa place ». **Celle qui restait a
decouvert est celle que `evaluer_le_garde_fou` et la mesure appellent reellement.**

Ce que ca dit, et qui depasse ce trou-la : **un cas ecrit pour une ligne ne couvre pas
forcement la fonction, et un cas ecrit pour une fonction ne couvre pas forcement le module.**
La regle du §4 -- ecrire depuis l'invariant et non depuis la mutation -- est necessaire et ne
suffit pas : encore faut-il visiter **tous les sites** ou l'invariant est cense tenir.

Deux cas ont ete ajoutes, et ils ne font pas la meme chose :

- la porte echantillonnee est **refaite a la main**, meme graine, depuis l'info-set du
  decideur : une reimplementation etablit que le RESULTAT est le bon ;
- un **temoin** pose sur `tenseur` regarde l'argument lui-meme, sur les deux portes : il
  etablit que la REGLE est tenue partout, quel que soit le nombre de portes que ce module
  gagnera plus tard.

Apres correction, la mutation est **detectee**.

## La solidite des detections, mesuree et non supposee

Le rapport de l'etape 0 reprochait a 14 des 45 detections de ne tenir qu'a **un seul rouge**.
Sept des neuf detections ci-dessus tiennent a un ou deux rouges. Il fallait donc savoir si
c'est le signe de cas minces, ou de mutations etroites -- **les deux se lisent pareil dans le
tableau, et ils ne demandent pas le meme travail.**

La mesure : l'invariant est **nie a tous ses sites**, la negation etant ecrite depuis la
docstring et non lue dans `outillage/mutation.py`, puis les 27 cas neufs sont rejoues.
Journal : `phase4_journaux/solidite_des_cas_neufs.log`.

| Invariant nie | Sites nies | Cas neufs qui tombent |
|---|---:|---:|
| la valeur est aplatie | 1 | **2** |
| l'avantage vaut `R - V(s)` | 1 | **1** |
| la tete a la taille de l'espace d'action | 1 | **1** |
| le siege observe est celui qui decide | **3** | **3** |
| un alea par (donne, siege, place) | 1 | **2** |
| `percevoir` leve sur un nœud sans decision | 1 | **1** |
| le garde-fou demande un PROGRES etabli | 1 | **1** |
| l'IC est corrige pour huit regards | **2** | **2** |
| le pool garde les plus recents | 1 | **1** |

**Aucune negation ne passe.** Et la ligne du siege tranche la question posee : l'invariant y
vit a **trois** sites, les trois cas tombent quand les trois sont nies, alors que la mutation
n'a produit **qu'un seul rouge**. Elle ne touche donc qu'un site sur trois. **La detection a
un rouge n'etait pas un cas mince : c'etait une mutation etroite.** Ce controle ne dit rien
des lignes que ces neuf invariants ne couvrent pas.

Une precision sur `garde-fou-se-contente-d-un-ecart-etabli`, ou un seul cas tombe sur trois
ecrits : c'est **correct et non une faiblesse**. `etabli` et `progres_etabli` ne different
que sur un ecart etabli NEGATIF. Les deux autres cas -- le progres etabli qui laisse courir,
l'intervalle qui contient zero et qui arrete -- tiennent des etats ou les deux predicats
coincident. Ils sont ecrits parce qu'un declencheur qui declenche sur tout ne detecte rien.

## `EXPIRE` a disparu, et c'est le minuteur qui l'a fait

`masse-binomiale-part-de-zero` **rend enfin un verdict : detectee, 11 rouges.** Elle n'a plus
besoin des 15 minutes du delai de garde de l'outil : la suite la tue elle-meme.

C'etait la raison d'etre du §3.3 de l'arbitrage -- « `EXPIRE` doit rester un etat de l'outil,
ce ne doit pas devenir une case ou l'on range ce qu'on ne sait pas ». Le delai est
**58,8 s = 4 x 14,70 s**, et les deux nombres sont mesures : trois passes de la suite entiere
le 24/08 (166,34 / 163,17 / 168,19 s), meme cas le plus lent aux trois passes
(13,76 / 13,40 / **14,70** s). Voir `tests/conftest.py`.

**Un seul delai, et c'est la mesure qui l'a decide.** L'intention etait d'en donner un plus
large aux cas marques `lent` (critere A3). Les trois passes disent que **ce marqueur ne
designe pas les cas lents** : les cinq cas marques plafonnent a **2,90 s**, quand le plus lent
de la suite -- **cinq fois plus long** -- n'en porte aucun. Le marqueur dit « gros volume de
parties », pas « long ». Un second delai indexe dessus aurait elargi la garde la ou elle est
inutile et l'aurait laissee etroite la ou elle sert.

## Ce que ce document N'ETABLIT PAS

- **Il ne dit pas que les neuf endroits sont bien couverts.** Il dit qu'une negation de chacun
  des neuf invariants, a tous ses sites, fait tomber au moins un cas. Un dixieme defaut sur la
  meme ligne, qui ne nierait aucun de ces neuf invariants, resterait invisible.
- **Il ne comble aucun des deux trous restants.** `intitule-du-garde-fou-sans-population` et
  `separation-exacte-toujours-disjointe` sont les reserves 3 et 2, traitees a l'etape 0 bis.
- **Il ne mesure aucune couverture.** Les ~2 500 lignes que les 57 motifs n'echantillonnent
  pas restent exactement aussi peu tenues qu'avant.
- **Il ne dit rien de la tete de valeur elle-meme.** Il dit que la suite sait desormais qu'elle
  est branchee, aplatie, et de la bonne taille. Savoir qu'un organe est branche n'est pas
  savoir qu'il fonctionne, et l'iteration 1 commence apres ce document.

## Reproduire

Le rejeu des dix :

```
UV_LINK_MODE=copy uv run python outillage/mutation.py --noms valeur-non-aplatie,avantage-sans-ligne-de-base,tete-plus-grande-que-l-espace-d-action,politique-reseau-observe-le-siege-zero,adversaires-partagent-un-alea,perception-decide-sur-un-noeud-de-chance,garde-fou-se-contente-d-un-ecart-etabli,garde-fou-sans-bonferroni,pool-garde-les-plus-anciens,masse-binomiale-part-de-zero
```

> **L'outil refuse de commencer si l'arbre porte des modifications non commitees**, parce
> qu'il restaure avec `git checkout` et les detruirait. Le journal se redirige donc **hors du
> depot** -- la garde s'est declenchee sur ce rejeu meme, et elle avait raison.

Les journaux bruts, tous gardes sous leur propre nom :

| Fichier | Ce qu'il porte |
|---|---|
| `phase4_journaux/mutations_rejeu_des_DIX_avant_correction.log` | 9 detectees, 1 survivante |
| `phase4_journaux/mutations_rejeu_du_siege_apres_correction.log` | la dixieme, detectee |
| `phase4_journaux/solidite_des_cas_neufs.log` | les neuf invariants nies, un par un |
