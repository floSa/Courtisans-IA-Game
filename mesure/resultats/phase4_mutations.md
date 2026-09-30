# Phase 4, etape 0 -- le perimetre des mutations, etendu a `agents/` et `mesure/`

**MESURE le 24/08/2026**, `uv run python outillage/mutation.py`, commit `b3e0bbe`.
Une mutation = une passe entiere de la suite.

| | |
|---|---|
| **passe de BASE, sans mutation** | **1251 verts, 0 rouge** (cible `tests`) |
| **TEMOINS, les 20 fichiers mutes edites sans effet** | **1251 verts, 0 rouge** -- identique a la base |
| mutations jouees | 57 |

> **Le compte de base est en tete parce que les 57 verdicts sont des ECARTS lus contre lui.**
> Un releve de mutation qui ne publie pas son zero ne se lit pas. Voir le §« L'incident »
> plus bas : sans ce zero, un seul rouge preexistant fait rapporter « toutes detectees ».

> **Ce document ne juge pas l'agent.** Il juge la SUITE DE TESTS. Une mutation qui survit
> ne dit rien du code mute -- elle dit que rien ne le tient.

## Le compte

| | mutations | detectees | **survivantes** | expirees |
|---|---:|---:|---:|---:|
| `courtisans/` -- les 20 d'origine | 20 | 20 | **0** | 0 |
| `agents/` (hors `greedy.py`) -- neuves | 20 | 11 | **9** | 0 |
| `mesure/` -- neuves | 17 | 14 | **2** | 1 |
| **total** | **57** | **45** | **11** | **1** |

**`agents/greedy.py` porte 0 mutation** -- §0.3 du protocole, l'etalon de toutes les phases.
L'exemption est une **donnee** que `principal` verifie (`FICHIERS_EXEMPTS`) et qu'un cas de
`tests/outillage/` tient, pas une phrase de docstring.

**Les 20 mutations du coeur sont toutes detectees, comme en phase 3.** Ce qui change, c'est
qu'on sait maintenant ce que ce chiffre ne disait pas : sur les 37 neuves, **11 survivent**.
Le code qui entraine et le code qui mesure sont tenus bien moins serre que le moteur -- et
c'est exactement l'endroit ou la phase 2 s'est trompee, avec un facteur trois indu qui
vivait dans le generateur et a survecu a deux verifications reussies.

### La solidite des 45 detections, chiffree

« Un test tombe » n'est pas « le bon test tombe pour la bonne raison ». Sur les
**45 detections** : rouges de **1 a 79**, mediane **5**.

- **14 des 45 ne tiennent qu'a UN SEUL test rouge** ;
- **20 des 45** tiennent a quatre rouges ou moins.

Ce chiffre dit combien de detections sont **a une reecriture de test de devenir des
survivantes**. Il ne dit pas qu'elles sont fausses : il dit qu'elles sont fines.

## La forme que ces trous ont, et c'est la lecture qui vaut plus que le compte

**9 des 11 survivantes cassent un invariant qui est ecrit, en toutes lettres,
dans un commentaire ou une docstring a cote de la ligne meme -- et defendu par rien d'autre.**
Verifie ligne a ligne, pas estime.

| Survivante | Defense | Ou l'invariant est ecrit | Ce qu'il dit |
|---|---|---|---|
| `perception-decide-sur-un-noeud-de-chance` | code + prose | `agents/perception.py:114`, clause `Raises:` | « si l'etat est terminal ou sur un nœud de chance. Un agent n'y decide rien » |
| `valeur-non-aplatie` | prose seule | `agents/reseau.py:118`, docstring de `forward` | « `valeurs` est aplatie : une valeur par ligne » |
| `politique-reseau-observe-le-siege-zero` | prose seule | `agents/politique_reseau.py`, section entiere de la docstring de module | « Cette fonction ecrit `tenseur(etat, etat.current_player())`. C'est exactement la ligne que l'obstacle A rendait dangereuse » |
| `avantage-sans-ligne-de-base` | prose seule | `agents/entrainement.py:22`, docstring de module | « A `lambda = 1` l'avantage vaut `R - V(s)` » |
| `tete-plus-grande-que-l-espace-d-action` | code UNILATERAL | `agents/entrainement.py:379`, un `raise` | « l'espace d'action et le reseau ont divergé » -- mais le controle ne teste qu'un sens, tete trop PETITE, et sur le seul etat initial |
| `garde-fou-se-contente-d-un-ecart-etabli` | prose seule | `agents/campagne.py:398`, commentaire | « **`progres_etabli`, pas `etabli`.** La v5 demandait « etabli » [...] » |
| `garde-fou-sans-bonferroni` | prose seule | `agents/campagne.py:17`, docstring de module | « l'IC est donc corrige de **Bonferroni** : `risque / 8`, soit `z = 3,2272` » |
| `pool-garde-les-plus-anciens` | prose seule | `agents/campagne.py:379`, commentaire | « Le plafond garde les **plus recents** : un pool rempli de versions tres faibles dilue le signal » |
| `intitule-du-garde-fou-sans-population` | prose seule | `agents/campagne.py:249`, docstring | « Le nom porte donc desormais **l'agent, le nombre de donnes et le depart des seeds** » |
| `adversaires-partagent-un-alea` | prose seule | `mesure/phase3.py:265`, commentaire | « Un alea par (donne, siege de l'agent, place) : deux adversaires ne partagent jamais de generateur » |
| `separation-exacte-toujours-disjointe` | prose seule | `mesure/phase3_mesure.py:387`, docstring | « Si les deux ne se croisent pas, l'ecart est etabli » |

**La lecture : dans ce depot, les invariants les plus durement acquis sont defendus par de
la prose posee a cote de la ligne, et par rien d'autre.** L'obstacle A, la cinquieme version
du garde-fou, la composition annoncee de la phase 3 : trois choses qui ont coute cher a
etablir, trois commentaires, zero test. **Une prose ne tombe pas quand on la contredit.**

Les deux qui ne sont pas dans ce cas ne sont pas rassurantes pour autant :

- `perception-decide-sur-un-noeud-de-chance` a une **levee reelle** dans le code -- et
  aucun cas ne l'exerce, donc la retirer ne coute rien ;
- `tete-plus-grande-que-l-espace-d-action` a un **controle unilateral** : il attrape une tete
  trop petite, pas une tete trop grande, et il ne regarde que l'etat initial.

## L'incident : l'instrument qui a produit ce rapport a failli le rendre faux

**Il appartient a ce document parce qu'il porte sur l'instrument qui l'a produit.** Deux
defaillances, et la seconde est nee dans la correction de la premiere.

### 1. L'outil n'etablissait jamais sa ligne de base

`principal` verifiait que le depot etait propre ; il ne jouait **pas une seule fois la suite
non mutee**. `_jouer` rendait `(verts, rouges)` et l'outil ecrivait `detectee` des que
`rouges` etait non nul -- **sans jamais savoir si ce rouge venait de la mutation**.

La consequence se calcule : **un seul rouge preexistant fait que la campagne entiere
rapporte zero survivante.** Et ce n'etait pas une hypothese. La premiere version de ce
rapport a ete commitee sans etre inscrite dans `DOCUMENTS_DE_MESURE` ; la suite est passee
au rouge ; une campagne rejouee sur ce depot aurait rendu **56 detectees, 0 survivante,
1 expiree**. **L'outil annonce une suite parfaite exactement quand la suite est cassee.**

Parade : `_passe_de_base` joue la suite non mutee en tete de campagne, l'outil **refuse de
commencer** si elle n'est pas verte, et le compte est publie en tete de ce document.

### 2. La correction a refait le defaut, sous une autre forme

Les cas ecrits pour tenir l'outil verifiaient les invariants du catalogue en lisant le
**disque**. Or `_appliquer` remplace `avant` par `apres` : sous mutation le motif n'y est
plus, deux cas tombaient, **sur les 56 mutations a la fois**. Le rejeu a rendu
**56 detectees / 0 survivante**, soit exactement **+2 rouges sur chaque ligne, sans
exception**, et les onze survivantes reelles effacees.

**La passe de base ne pouvait pas le voir** : elle mesure le zero AVANT la premiere
mutation, quand ces deux cas sont encore verts.

Trois reponses, dont une seule ferme la classe :

1. les deux cas lisent `git show HEAD:<fichier>` -- la source **commitee**, qui est l'etat
   pristine par construction puisque l'outil refuse un depot sale et restaure par
   `git checkout`. **Verifie : 65 verts avec une mutation en place**, contre 63/2 avant ;
2. un **temoin negatif** -- une mutation qui n'ajoute qu'un commentaire, jouee apres la
   passe de base ; la suite doit rendre le meme compte. **MESURE : il n'aurait PAS attrape
   ce defaut-la** -- une mutation qui n'enleve rien ne peut pas reproduire un defaut cause
   par un motif enleve. Il est garde pour ce qu'il attrape vraiment, et cette limite est
   ecrite plutot que tue ;
3. **`tombes_sous_TOUTES_les_mutations`** : une mutation change UN comportement, donc un test
   qui tombe sous TOUTES ne reagit a aucune. C'est le controle qui aurait vu le defaut. Il ne
   coute **aucune passe** -- les noms sont deja dans la sortie de pytest -- et il **signale
   sans condamner** : un test tres general peut legitimement tomber partout.

### 3. Un HEAD qui bouge pendant la campagne rend une mutation PERMANENTE

**Le troisieme etage du meme escalier, et le plus couteux.** Le 24/08 a 08:05 une campagne
demarre ; a 08:11 elle joue sa premiere mutation, `espions-adverses-visibles`, qui edite
`courtisans/infoset.py`. A **08:11:24**, un commit tombe. Il porte deux fichiers : le document
qui est son objet, et `courtisans/infoset.py`, qui ne l'est pas -- un `git add -A` a balaye le
fichier **mute** en vol.

`_restaurer` fait alors `git checkout -- courtisans/infoset.py`, **qui restaure vers HEAD** :
donc vers la version mutee. La mutation devient permanente.

Ce que ca a casse, mesure :

- **l'invariant I7 saute dans HEAD** -- l'identite des Espions adverses fuite dans l'encodage,
  donc dans l'observation que voit tout agent ;
- la suite complete tombe de **1248/0 a 1169 verts / 79 rouges** sur arbre propre ;
- **les 56 mutations suivantes tournent sur un moteur casse** : ~79 rouges parasites sur
  chaque ligne, **zero survivante**, releve a jeter.

**C'est `tombes_sous_TOUTES_les_mutations` qui l'a fait remonter** -- il a nomme les 78 tests
qui tombaient partout, et c'est en les lisant que la cause est apparue. Le controle ne du
defaut precedent a attrape le suivant.

Deux parades, et il faut les deux. `_restaurer` restaure depuis le **SHA fige au demarrage**,
ce qui **empeche** la contamination meme si HEAD bouge ; `refus_si_head_a_bouge` compare le SHA
a chaque tour et **arrete** la campagne, parce qu'un HEAD qui bouge invalide la passe de base et
donc tous les ecarts. C'est le symetrique du controle de depot propre : celui-la protege le
travail en cours contre l'outil, celui-ci protege l'outil contre le travail en cours.

> **Consequence pratique, a lire avant de lancer une campagne : ne rien commiter pendant
> qu'elle tourne.** L'outil s'arrete desormais au lieu de se contaminer, mais il perd la
> campagne en cours.

**Le releve ci-dessous est le CINQUIEME jeu de la campagne.** Il reproduit les 57 verdicts
des jeux precedents valides **a l'identique, rouge pour rouge** -- les verts montent de +11,
qui est exactement le nombre de cas ajoutes depuis. C'est ce qui etablit qu'ils sont
reproductibles, et non seulement justes.

### Le compte des jeux, puisqu'il fait partie du resultat

**Cinq jeux ont ete payes, quatre pour des defauts de l'instrument, un seul du premier coup.**

| Jeu | Duree | Issue |
|---|---:|---|
| 1 | 4 h 47 + 48 min | bloque : pas de delai de garde. Verdicts bons mais non reproductibles |
| 2 | 2 h 45 | **invalide** : deux cas lisaient le disque, +2 rouges partout |
| 3 | 2 h 46 | valide -- le premier releve reproductible |
| 4 | 2 h 32 | **invalide** : HEAD empoisonne par un commit en vol |
| 5 | 2 h 50 | valide, et reproduit le jeu 3 rouge pour rouge |

**Aucun de ces quatre defauts n'etait dans les mutations ni dans la suite.** Tous les quatre
etaient dans l'instrument qui les mesure. C'est la lecon la plus chere de cette etape, et elle
vaut d'etre lue a cote du tableau des onze survivantes : **un outil qui juge une suite de tests
demande le meme soin que ce qu'il juge.**

## Le troisieme verdict : `EXPIRE`

`masse-binomiale-part-de-zero` n'a **pas rendu de verdict**, aux trois campagnes. Elle fait
partir la recurrence de la loi binomiale de `k = 0` au lieu du mode ; pour les `n` de l'ordre
de 10 000 des calculs de puissance, le premier terme vaut `1e-1760` -- zero en flottant --
et un balayage qui cherche le `n` d'une puissance cible ne converge jamais.

La premiere campagne a tourne **2 h 48** sur cette seule mutation, la ou une passe prend
~2,8 min, parce que `_jouer` n'avait pas de `timeout`. Delai de garde a
**15 minutes**, et un **troisieme etat**. Un blocage n'est ni
« detectee » ni « survit » : l'appeler « detectee » compterait comme un succes de la suite
un arret sans verdict, l'appeler « survit » designerait un trou qui n'est pas celui-la.

> **Et il dit quelque chose de la SUITE.** `tests` n'a **aucun delai de garde propre** : un
> test qui boucle y est indiscernable d'un test lent. Ce trou n'est pas comble par ce
> document.

## Ce que ce document N'ETABLIT PAS

- **Il ne dit pas que les 45 detections sont de bonnes detections.** 14 d'entre elles
  ne tiennent qu'a un seul rouge ; une detection a un rouge peut etre fortuite.
- **Il ne mesure aucune couverture.** 37 mutations sur ~2 500 lignes est un echantillon
  choisi, pas un balayage. Un trou qu'aucune de ces 37 ne vise reste invisible.
- **Il ne comble aucun des 11 trous.** Les combler est le travail de l'etape 0 ter.
- **Combler ces trous ne rendra pas la suite bonne.** Ca rendra tenus les endroits nommes
  ici. Les ~2 500 lignes que ces 37 motifs n'echantillonnent pas resteront exactement aussi
  peu tenues qu'avant.

## Reproduire

```
UV_LINK_MODE=copy uv run python outillage/mutation.py
```

Reprise partielle, sans rejouer ce qui a deja rendu un verdict :

```
UV_LINK_MODE=copy uv run python outillage/mutation.py --noms nom1,nom2
```

### Recompter la reproduction sans rejouer quoi que ce soit

**Les DEUX jeux valides sont dans le depot, sous des noms distincts**, parce que la
reproduction est le resultat qui compte le plus de cette etape et qu'elle ne se verifie
qu'en ayant les deux relevés sous la main :

- `mesure/resultats/phase4_journaux/mutations_campagne_VALIDE_jeu3.log` (base 1240)
- `mesure/resultats/phase4_journaux/mutations_campagne_VALIDE_jeu5.log` (base 1251)

`mesure/resultats/phase4_journaux/README.md` porte les deux commandes qui les comparent et
la sortie attendue de chacune : **57 lignes de meme nom, meme rouges, meme verdict** ; et
**+11 verts uniformement** sur les 56 mutations qui rendent un compte -- exactement le
nombre de cas ajoutes entre les deux jeux. Un ecart de verts qui varierait d'une mutation a
l'autre dirait que les cas neufs reagissent aux mutations, et il faudrait les regarder un
par un. Il ne varie pas.

## Le releve brut, les 57

| Mutation | Fichier | Verts | Rouges | Verdict |
|---|---|---:|---:|---|
| `espions-adverses-visibles` | `courtisans/infoset.py` | 1163 | 77 | detectee |
| `phase-et-assassin-absents` | `courtisans/infoset.py` | 1218 | 22 | detectee |
| `residu-compte-les-morts` | `courtisans/infoset.py` | 1232 | 8 | detectee |
| `meurtre-obligatoire` | `courtisans/engine.py` | 1176 | 64 | detectee |
| `fin-joueur-par-joueur` | `courtisans/engine.py` | 1161 | 79 | detectee |
| `noble-vaut-un` | `courtisans/cards.py` | 1195 | 45 | detectee |
| `points-au-poseur` | `courtisans/rules.py` | 1210 | 30 | detectee |
| `morts-comptes-au-decompte` | `courtisans/engine.py` | 1217 | 23 | detectee |
| `main-non-triee` | `courtisans/rules.py` | 1224 | 16 | detectee |
| `doublons-non-masques` | `courtisans/rules.py` | 1228 | 12 | detectee |
| `observation-sans-joueur` | `courtisans/engine.py` | 1167 | 73 | detectee |
| `observateur-absent` | `courtisans/openspiel_adapter.py` | 1223 | 17 | detectee |
| `libelle-de-cible-ambigu` | `courtisans/openspiel_adapter.py` | 1225 | 15 | detectee |
| `libelle-nomme-un-dos` | `courtisans/openspiel_adapter.py` | 1230 | 10 | detectee |
| `bornes-de-joueurs-desynchronisees` | `courtisans/openspiel_adapter.py` | 1239 | 1 | detectee |
| `player-obligatoire` | `courtisans/openspiel_adapter.py` | 1236 | 4 | detectee |
| `chaine-de-jeu-sans-config` | `courtisans/openspiel_adapter.py` | 1228 | 12 | detectee |
| `roles-separes-par-virgule` | `courtisans/openspiel_adapter.py` | 1227 | 13 | detectee |
| `tours-arrondis-au-dessus` | `courtisans/config.py` | 1189 | 51 | detectee |
| `vue-du-joueur-contourne-la-parade` | `courtisans/infoset.py` | 1196 | 44 | detectee |
| `perception-nomme-les-dos` | `agents/perception.py` | 1165 | 75 | detectee |
| `perception-decide-sur-un-noeud-de-chance` | `agents/perception.py` | 1240 | 0 | **SURVIT** |
| `masque-laisse-une-probabilite-aux-illegales` | `agents/reseau.py` | 1234 | 6 | detectee |
| `tirer-ne-verifie-plus-la-somme` | `agents/reseau.py` | 1239 | 1 | detectee |
| `valeur-non-aplatie` | `agents/reseau.py` | 1240 | 0 | **SURVIT** |
| `deterministe-ignore-le-masque` | `agents/reseau.py` | 1239 | 1 | detectee |
| `politique-reseau-observe-le-siege-zero` | `agents/politique_reseau.py` | 1240 | 0 | **SURVIT** |
| `charger-laisse-le-reseau-en-entrainement` | `agents/politique_reseau.py` | 1239 | 1 | detectee |
| `gain-du-siege-zero` | `agents/entrainement.py` | 1239 | 1 | detectee |
| `noeuds-du-pool-collectes` | `agents/entrainement.py` | 1239 | 1 | detectee |
| `avantage-sans-ligne-de-base` | `agents/entrainement.py` | 1240 | 0 | **SURVIT** |
| `alea-de-partie-partage` | `agents/entrainement.py` | 1239 | 1 | detectee |
| `composition-toujours-self-play` | `agents/entrainement.py` | 1239 | 1 | detectee |
| `tete-plus-grande-que-l-espace-d-action` | `agents/entrainement.py` | 1240 | 0 | **SURVIT** |
| `garde-fou-de-portee-un` | `agents/campagne.py` | 1236 | 4 | detectee |
| `garde-fou-se-contente-d-un-ecart-etabli` | `agents/campagne.py` | 1240 | 0 | **SURVIT** |
| `garde-fou-sans-bonferroni` | `agents/campagne.py` | 1240 | 0 | **SURVIT** |
| `pool-garde-les-plus-anciens` | `agents/campagne.py` | 1240 | 0 | **SURVIT** |
| `intitule-du-garde-fou-sans-population` | `agents/campagne.py` | 1240 | 0 | **SURVIT** |
| `garde-fou-se-compare-a-lui-meme` | `agents/campagne.py` | 1237 | 3 | detectee |
| `progres-etabli-redevient-etabli` | `mesure/bootstrap.py` | 1239 | 1 | detectee |
| `percentiles-apparies-unilateraux` | `mesure/bootstrap.py` | 1239 | 1 | detectee |
| `rho-sur-des-groupes-inegaux` | `mesure/bootstrap.py` | 1239 | 1 | detectee |
| `appariement-par-rang-de-valeur` | `mesure/bootstrap.py` | 1236 | 4 | detectee |
| `masse-binomiale-part-de-zero` | `mesure/binomiale.py` | - | - | EXPIRE |
| `clopper-pearson-borne-basse-unilaterale` | `mesure/binomiale.py` | 1236 | 4 | detectee |
| `r2-devient-r0` | `mesure/retournement.py` | 1232 | 8 | detectee |
| `r3-ignore-le-statut-final` | `mesure/retournement.py` | 1235 | 5 | detectee |
| `vue-d-un-siege-voit-tous-les-espions` | `mesure/partie.py` | 1236 | 4 | detectee |
| `part-fractionnee-ne-somme-plus-a-un` | `mesure/phase2.py` | 1235 | 5 | detectee |
| `quantile-sans-bonferroni` | `mesure/dimensionnement.py` | 1232 | 8 | detectee |
| `sieges-non-permutes` | `mesure/phase3.py` | 1235 | 5 | detectee |
| `adversaires-partagent-un-alea` | `mesure/phase3.py` | 1240 | 0 | **SURVIT** |
| `gain-lu-au-siege-zero` | `mesure/phase3.py` | 1239 | 1 | detectee |
| `separation-exacte-toujours-disjointe` | `mesure/phase3_mesure.py` | 1240 | 0 | **SURVIT** |
| `b4-strict-avale-le-departage` | `mesure/comportements.py` | 1239 | 1 | detectee |
| `b4-meurtre-couteux-au-mauvais-denominateur` | `mesure/comportements.py` | 1239 | 1 | detectee |

