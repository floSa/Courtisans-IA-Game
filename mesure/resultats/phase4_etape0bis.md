# Phase 4, etape 0 bis -- les trois reserves de la phase 3, levees avec leur parade

**MESURE le 24/08/2026**, branche `phase-4-tete-de-valeur`.

| | |
|---|---|
| **passe de BASE du dernier rejeu** | **1290 verts, 0 rouge** (cible `tests`) |
| **TEMOINS, les 20 fichiers mutes edites sans effet** | **1290 verts, 0 rouge** |
| cas ajoutes a l'etape 0 bis | **10** |

> **Une reserve levee dont la mutation survit toujours n'est pas levee : elle est reecrite.**
> Les trois sont donc rendues avec le cas qui les ferait revenir en tombant, et deux d'entre
> elles avec la mutation qui les mesure.

## Le tableau avant / apres

| Mutation | Avant | Apres |
|---|---|---|
| `separation-exacte-toujours-disjointe` (reserve 2) | SURVIT | **detectee**, 1 rouge |
| `intitule-du-garde-fou-sans-population` (reserve 3) | SURVIT | **SURVIT encore**, puis **detectee**, 2 rouges |

**Avec ces deux-la, les onze survivantes de l'etape 0 sont toutes tombees.**

---

## Reserve 1 -- un intitule « 99 % » qui couvre deux risques

**Le libelle etait faux, et aucune conclusion ne bouge.** Les bornes de Clopper-Pearson
publiees sont **unilaterales au risque 1 %**. Le rapport les annoncait « borne haute a 99 % »,
sans qualificatif, quand tout le reste du document publie des intervalles **bilateraux** a
99 % -- dont la queue vaut 0,5 %.

| Zero observe | Publie (unilaterale, 1 %) | Bilaterale (queue 0,5 %) | L'agent y vaut |
|---|---:|---:|---:|
| `0/1967` | **0,2338 %** | 0,2690 % | 35,87 % |
| `0/10382` | **0,0443 %** | 0,0510 % | 3,66 % |

L'agent est au-dela des deux lectures : **la separabilite tient dans les deux cas.** Mais un
lecteur qui recalcule en bilateral -- ce que l'etiquette « 99 % » lui dit de faire -- ne
retrouve pas le nombre publie et ne peut pas savoir lequel des deux il tient. C'est la faute
maison du projet appliquee a une etiquette : **un chiffre exact sur une population que sa
phrase ne nomme pas.**

**La parade est dans le GENERATEUR, pas dans le document.** `mesure/resultats/phase3.md` est
produit par `mesure/rapport_phase3.py` ; corriger le seul fichier aurait laisse l'etiquette
revenir a la generation suivante. La lateralite est ecrite **une fois**
(`rapport_phase3.LATERALITE_EXACTE`), et un cas exige qu'aucune phrase de borne exacte ne se
publie sans elle, sur les quatre cas de la regle.

**Le document publie est corrige aux cinq sites**, et le controle est chiffre : compare token
a token contre `HEAD`, **5 fois « 99 % » retires, 5 fois « 1 % » ajoutes**. Les deux seuls
autres ajouts sont 35,87 % et 3,66 %, que la nouvelle phrase nomme au lieu d'ecrire
« l'agent est au-dela », et qui figurent deja dans la meme ligne du tableau. **Aucun chiffre
publie n'a ete modifie ni supprime.**

## Reserve 2 -- un rendu ecrit pour UN des QUATRE cas

Le calcul de `separer_un_taux_degenere` traite les quatre cas depuis le tour 2. **Le rendu
n'en redigeait qu'un**, en dur : « le zero **de la ligne de base** ». Trois des quatre en
sortaient faux, aucun ne l'etant sur les donnees de la phase 3 -- latent, pas faux :

- un zero du cote de l'**agent** aurait ete attribue a la ligne de base, et la phrase aurait
  dit l'inverse de ce que le tableau montre ;
- un taux a **100 %** aurait ete annonce « le zero », avec une « borne haute » quand c'est une
  borne basse ;
- **deux** cotes degeneres auraient fait parler de « l'intervalle de l'autre cote », qui
  n'existe pas -- l'autre cote est degenere lui aussi et n'a pas d'intervalle normal.

**Le defaut n'etait pas dans la phrase, il etait dans le CABLAGE.** `Comparaison` ne recevait
que la borne, jamais le cote : `separer_un_taux_degenere` calcule un `SeparationExacte` qui
porte `cote`, et `comparer` n'en gardait que `borne`. **Un rendu ne peut pas nommer ce qu'on
ne lui donne pas.** La parade est donc posee sur le cablage -- `Comparaison.separation` --, et
les quatre cas sont rediges a un seul site.

### Et pourquoi la mutation survivait, ce que la reserve n'annoncait pas

**Les quatre cas ETAIENT testes.** Mais tous avec des donnees **separables** du cote a un seul
degenere. Un calcul qui rendrait « disjoints » quoi qu'il arrive sur cette branche passait les
quatre.

> **Un predicat ne se teste pas sur les seules donnees qui le rendent vrai.**

Le cas qui manquait : agent `30/100` = 30,0 % contre ligne de base `0/20`. La borne exacte du
zero vaut **20,57 %**, la borne basse de l'intervalle normal de l'agent vaut **18,20 %** :
elles se croisent, donc l'ecart n'est **pas** etabli. Plus son symetrique du cote du cent --
`20/20` contre `18/20` --, parce que les deux branches du meme `if` sont ecrites separement et
que tester l'une ne dit rien de l'autre. Les deux bornes sont recalculees a la main dans le
cas : il ne demande pas au module de se confirmer lui-meme.

## Reserve 3 -- la parade des intitules, et il en fallait DEUX

### La forme d'appel, qui est celle du depot

`_cle_d_un_intitule` resolvait un appel en cherchant le nom de la fonction dans les
**globales** du module ou l'appel est ecrit. Pour `campagne_module.intitule_du_garde_fou()`,
elle cherchait `intitule_du_garde_fou` dans `mesure/phase3_mesure.py`, ou seul
`campagne_module` existe. La resolution echouait **sans rien dire**, la cle retombait sur le
texte source, et un doublon avec un litteral passait.

**La cause reelle est plus profonde que la reserve.** L'import de `mesure/phase3_mesure.py`
est **local a une fonction** (ligne 864) : l'alias n'est donc pas un attribut du module, et
`getattr(module, alias)` ne pouvait pas le trouver, meme en suivant le chemin pointe. La
resolution passe desormais par les **imports declares dans le fichier**, lus dans son AST.

C'est **la seule forme d'appel que le depot ecrit** hors des tests. La parade laissait passer
exactement ce qu'elle avait a garder -- et c'est la **deuxieme fois** qu'elle est prise sur une
forme syntaxique qu'elle ne voyait pas : le tour 2 ne lisait que les litteraux, le tour 3 que
les appels nus.

> **Une parade syntaxique doit etre eprouvee sur le style reel du depot**, pas sur la forme que
> son auteur avait en tete. Un cas neuf balaie donc `mesure/` et `agents/` et tombe si un
> argument `intitule=` construit par appel y est **transcrit au lieu d'etre resolu**.

### La seconde parade, que le rejeu a rendue necessaire

`intitule-du-garde-fou-sans-population` **a survecu a tout ce qui precede.** Et c'est logique :

- la parade des intitules ne mord que sur une **COLLISION**, deux campagnes qui portent le
  meme nom ;
- la mutation, elle, **vide le nom de sa population** ;
- un nom vide ne heurte rien tant que son quasi-jumeau du pool garde le sien -- « 1 agent
  entraine FINAL contre 2 aleatoires, 500 donnes, seeds 70000+ ».

**Deux parades pour un meme defaut, et elles ne se remplacent pas.** L'une empeche deux
campagnes de porter le meme nom ; l'autre empeche un nom de ne rien dire. La faute d'origine
de la phase 3 -- **70,13 % et 70,03 % publies sous le meme intitule**, et le controle R2 « les
noms sont distincts » qui ne voyait rien -- demandait les deux.

La seconde est ecrite depuis la docstring, qui l'enoncait deja : « Le nom porte donc desormais
**l'agent, le nombre de donnes et le depart des seeds** ». Deux cas la tiennent : le nom
contient sa population, et **deux populations distinctes ne peuvent pas porter le meme nom**
-- ce qui est la propriete, et elle est plus forte que la premiere.

## Ce que ce document N'ETABLIT PAS

- **Il ne dit pas que la phase 3 etait fausse.** Aucune de ses conclusions ne bouge, et aucun
  de ses chiffres n'a ete touche. Deux des trois reserves etaient **latentes** : elles se
  seraient manifestees a la premiere phase produisant un taux a 100 % ou un zero cote agent.
- **Il ne dit pas que la parade des intitules est complete.** Elle couvre desormais le
  litteral, l'appel nu et l'appel qualifie. Une quatrieme forme -- un nom passe par variable,
  par exemple -- la traverserait encore, et c'est la troisieme fois que cette phrase serait
  vraie.
- **Il ne dit rien de la tete de valeur.** L'iteration 1 commence apres ce document.

## Reproduire

```
UV_LINK_MODE=copy uv run python outillage/mutation.py --noms separation-exacte-toujours-disjointe,intitule-du-garde-fou-sans-population
```

| Journal | Ce qu'il porte |
|---|---|
| `phase4_journaux/mutations_rejeu_des_RESERVES_avant_seconde_parade.log` | la reserve 2 detectee, la 3 survivante |
| `phase4_journaux/mutations_rejeu_de_la_RESERVE_3_apres_seconde_parade.log` | la reserve 3 detectee, 2 rouges |
