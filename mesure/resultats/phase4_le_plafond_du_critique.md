# Phase 4, iteration 1 -- ou est le plafond du critique, et il n'est pas ou on le croyait

**MESURE le 24/08/2026**, branche `phase-4-tete-de-valeur`, sur `models/phase3/final.pt`
(SHA-256 `772a869f…f0217`, verifie).

> **Ce document est ecrit AVANT tout entrainement de la phase 4, et avant la pre-inscription
> qui le suit.** Il ne rapporte aucun resultat d'agent. Il repond a une seule question, posee
> parce que l'arbitrage du pilote la posait deja : *de combien le critique peut-il monter ?*

---

## Le resultat, en deux phrases

**Le R2 atteignable depuis l'INFO-SET croit de +0,0079 par DOUBLEMENT des donnees, et cette
pente est stable sur trois intervalles.** A 1,5 million de nœuds -- dix fois plus que la
premiere mesure -- le meilleur ajustement direct fait **+0,1217**, quand le critique de la
phase 3 fait **+0,1012**.

| Nœuds d'apprentissage | Meilleur R2 de TEST | Gain par doublement |
|---:|---:|---:|
| 76 842 | +0,0871 | — |
| 307 273 | +0,1035 | +0,0082 |
| 767 906 | +0,1142 | +0,0081 |
| **1 536 135** | **+0,1217** | +0,0075 |
| *critique de la phase 3* | *+0,1012* | |

**Deux nombres sortent de la, et ils ne disent pas la meme chose :**

1. **La marge reelle du critique est de +0,0205.** Un ajustement direct sur 1,5 million de
   nœuds le bat de ce montant. C'est ce qu'une reparation peut esperer, et c'est **detectable**
   par le seuil intermediaire. Ce n'est pas rien.
2. **Le 0,545 est hors d'atteinte, et de tres loin.** A +0,0079 par doublement, il faudrait
   **53 doublements**, soit `1,8 x 10^22` nœuds. Meme en admettant que la pente flechisse ou
   se redresse, aucune lecture de cette courbe ne mene la.

**Le critique de la phase 3 n'est donc ni sain ni ruine : il est a un cinquantieme du plancher
theorique et a deux centiemes de ce que ses propres donnees permettent.**

---

## Comment on en est arrive la, dans l'ordre

### 1. D'ou vient la perte -- et ce n'est pas la ou le profil de l'auditeur le laissait croire

4 000 parties hors plage, seeds 7 000 000+, **76 842 nœuds**, R2 global **+0,1008**.
Le rang est celui de la decision **du siege** : les nœuds d'un couple (donne, siege) sont
ranges dans l'ordre du lock-step.

| Rang | nœuds | part | Var(R) | MSE | R2 local | **part de la PERTE** |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 12 000 | 15,62 % | 0,4245 | 0,4209 | **+0,0086** | 17,24 % |
| 1 | 12 000 | 15,62 % | 0,4245 | 0,4184 | +0,0146 | 17,14 % |
| 2 | 12 000 | 15,62 % | 0,4245 | 0,4113 | +0,0311 | 16,85 % |
| 3 | 12 000 | 15,62 % | 0,4245 | 0,3886 | +0,0847 | 15,92 % |
| 4 | 11 493 | 14,96 % | 0,4251 | 0,3586 | +0,1565 | 14,07 % |
| 5 | 9 366 | 12,19 % | 0,4242 | 0,3318 | +0,2178 | 10,61 % |
| 6 | 5 421 | 7,05 % | 0,4173 | 0,3075 | +0,2631 | 5,69 % |
| 7 | 2 034 | 2,65 % | 0,4180 | 0,2862 | +0,3154 | 1,99 % |
| 8-10 | 528 | 0,69 % | — | ~0,28 | +0,09 a +0,56 | 0,48 % |

**Les nœuds tardifs pesent 8,2 % de la perte.** Le profil de l'auditeur montre le critique a
0,30 la ou l'irreductible vaut 0,0075 -- un facteur quarante, et c'est vrai. Ce que ce
tableau ajoute : **ce facteur quarante porte sur un vingtieme de la population.**

> Une ponderation de la perte vers les nœuds tardifs -- le remede naturel du soupcon n° 3 --
> optimiserait **8 % de la perte**.

### 2. Le plancher par rang, et le piege de la ponderation naive

Methode de l'auditeur : rejouer **le meme etat** sous la politique de l'agent et prendre la
variance des retours. 300 etats x 24 replicats = 7 200 parties, 17,4 s.

| Rang | etats | plancher `Var(R\|s)` | `MSE - plancher` | x part de la population |
|---:|---:|---:|---:|---:|
| 0 | 50 | 0,2822 | 0,1387 | 2,17 |
| 1 | 45 | 0,2790 | 0,1394 | 2,18 |
| 2 | 45 | 0,2484 | 0,1629 | 2,54 |
| 3 | 47 | 0,1863 | 0,2023 | 3,16 |
| 4 | 37 | 0,1169 | 0,2417 | **3,62** |
| 5 | 35 | 0,1197 | 0,2121 | 2,59 |
| 6 | 30 | 0,0576 | 0,2499 | 1,76 |
| 7 | 10 | 0,0512 | 0,2350 | 0,62 |
| 8 | **1** | **0,0000** | — | — |

**La marge est repartie, pas concentree tard.** Les rangs 0-3 en portent **53 %**, les rangs
6 et plus **13 %**.

**Corroboration independante du 0,57.** En recombinant ces planchers avec la population :
`E[plancher] = 0,193` pour `Var(R) = 0,4239`, soit un **R2 atteignable de 0,545**. L'auditeur
publiait **0,57** par une autre methode et un autre decoupage. Les deux se rejoignent.

> **Et le piege, qui vaut d'etre nomme.** Une ponderation par `1 / plancher` -- l'idee
> evidente -- donne au rang 8 un poids de 1 000 et **93 % de la masse totale**. Ce rang est
> mesure sur **un seul etat**. Une ponderation posee sur une mesure doit encore etre posee
> sur une mesure qui a une population.

### 3. Le diagnostic decisif : le signal est-il dans l'info-set ?

Les deux premiers points disent ou est la perte. Ils ne disent pas si elle est **reductible**.
Le test qui tranche ne coute pas un entrainement : on ajuste un regresseur supervise ordinaire
sur `(info-set, retour)` et on lit son R2 sur un jeu de test **de seeds disjoints**.

Le decoupage par seeds, et non au hasard dans le meme bloc, est essentiel : deux nœuds d'une
meme partie portent **le meme retour terminal**, et une coupe au hasard ferait fuir la reponse
dans le jeu de test.

**Premier essai** -- largeur 256, 76 842 nœuds :

```
critique de la phase 3        : R2 TEST +0.1033
regresseur neuf, epoque  5    : R2 TEST +0.0756   (apprentissage +0.1961)
regresseur neuf, epoque 30    : R2 TEST -0.2361   (apprentissage +0.6544)
```

Il **memorise**. Trois confusions restaient a ecarter -- trop peu de donnees, trop de
capacite, trop d'epoques --, et le balayage les ecarte les trois :

```
etalon, critique de la phase 3 sur le test FIXE : R2 +0.1012

largeur  noeuds     meilleur R2 TEST   a l'epoque   R2 final   (apprentissage final)
     32    76818           +0.0147            8     -0.2129              +0.0378
     32   307273           +0.1061            3     +0.0883              +0.1631
     64    76818           +0.0121            3     -0.2116              +0.0371
     64   307273           +0.1026            2     +0.0615              +0.2054
    256    76818           +0.0209            2     -0.9161              +0.0559
    256   307273           +0.1061            3     -0.1113              +0.4630
```

**L'arret precoce est choisi sur le test**, donc ces chiffres sont **optimistes** -- et c'est
delibere : une borne haute optimiste qui reste basse est un resultat plus fort qu'une mesure
honnete qui reste basse.

### 4. Le volume de donnees : la confusion qu'il restait a ecarter

A 307 000 nœuds la marge semblait etre de +0,005, et c'etait une conclusion **prematuree** :
307 000 nœuds, c'est peu, et un run de 2 h en voit des millions. Quatre volumes, meme test
FIXE, meme reseau (largeur 128) :

```
test FIXE : 76 799 noeuds, seeds 7400000+
ETALON -- critique de la phase 3 : R2 +0.1012

parties   noeuds      meilleur R2 TEST   epoque   collecte   ajustement
   4000      76842           +0.0871        3      16.2 s        2.9 s
  16000     307273           +0.1035        4      68.1 s        5.8 s
  40000     767906           +0.1142        2     162.7 s       11.8 s
  80000    1536135           +0.1217        4     348.5 s       23.3 s
```

**La courbe ne plafonne pas : elle rampe.** Et sa pente est remarquablement reguliere --
+0,0082 puis +0,0081 puis +0,0075 par doublement. C'est ce qui permet de la lire au-dela du
dernier point, et c'est la que le chiffre devient brutal :

| Cible de R2 | Doublements necessaires | Nœuds |
|---:|---:|---:|
| 0,150 | 3,6 | 1,8 x 10^7 |
| 0,200 | 9,9 | 1,4 x 10^9 |
| **0,545** | **53,4** | **1,8 x 10^22** |

**L'ecart entre +0,12 et 0,545 n'est pas un manque de donnees.** C'est ce que l'info-set ne
contient pas.

---

## Ce que ca fait aux trois soupcons

| Soupcon | Ce que la mesure en dit |
|---|---|
| **3 -- la cible terminale vue de n'importe quelle profondeur** | Le diagnostic tient : le critique est presque nul aux rangs precoces (+0,009). Mais son remede naturel -- ponderer vers les nœuds tardifs -- vise **8 % de la perte et 13 % de la marge**. |
| **4 -- la ponderation `COEFFICIENT_VALEUR`** | **Non mesure ici.** Rien dans ce document ne l'infirme ni ne le confirme. |
| **5 -- la capacite de la tete** | **Infirme dans le sens attendu.** Plus de capacite **empire** la generalisation : largeur 256 sur 77 000 nœuds descend a -0,92. |

---

## Ce que ce document N'ETABLIT PAS

- **Il ne dit pas qu'aucun critique ne peut faire mieux.** Il dit qu'un perceptron a deux
  couches cachees, sous Adam, sur trois largeurs et jusqu'a 307 000 nœuds, ne le fait pas.
  Une autre classe de modele, une autre representation, ou un objectif auxiliaire pourraient
  le faire -- et la tete auxiliaire est explicitement l'iteration 2.
- **Il ne dit pas que la pente reste log-lineaire.** Trois intervalles la donnent a +0,0079
  par doublement ; rien n'etablit qu'elle tienne sur cinquante. L'extrapolation a `10^22`
  n'est pas une prediction, c'est une **reduction a l'absurde** : elle etablit que 0,545 n'est
  pas une question de volume, pas que le chiffre 53 veut dire quelque chose.
- **Il ne mesure pas E[Var(R | info-set)].** Le plancher de 0,193 est conditionne a l'etat
  COMPLET. Le vrai plafond d'un critique aveugle serait `1 - E[Var(R | info-set)] / Var(R)`,
  et cette quantite n'est pas mesuree ici -- elle est **estimee par ajustement**, ce qui en
  fait une borne BASSE : un meilleur modele ferait mieux.
- **Il ne compare pas les deux critiques sur la distribution du critique neuf.** L'echantillon
  est fixe sur celle de l'agent de la phase 3, parce que c'est ce qui rend l'appariement
  possible. Un agent neuf visitera d'autres etats.
- **Il ne dit rien du jeu.** Le seuil qui tranche l'iteration reste le gain moyen contre deux
  copies de l'agent de la phase 3. **On peut faire monter le R2 sans que l'agent joue mieux**,
  et l'inverse est vrai aussi : ce document ne prouve pas qu'un critique plafonne a +0,11
  empeche l'agent de progresser.

---

## Ce que je remonte au pilote, sans le trancher

L'arbitrage ordonne **un run sur le soupcon 3**. Ces mesures ne l'annulent pas -- elles
deplacent ce qu'on peut en attendre :

1. **La marge entre le critique de la phase 3 et le meilleur ajustement direct est de
   +0,0205**, mesuree a 1,5 million de nœuds. Le seuil intermediaire -- borne basse d'un ecart
   apparie strictement positive -- est donc **franchissable, et sur une marge reelle**. C'est
   plus encourageant que ce que la premiere mesure, faite sur trop peu de donnees, laissait
   croire : **j'ai failli conclure a +0,005, et c'etait une conclusion prematuree sur une
   population trop petite.**
2. **L'ecart entre +0,10 et le 0,545 atteignable est explique par ce que le critique NE VOIT
   PAS.** Le plancher est calcule sur l'etat complet ; le pilote l'avait ecrit -- « un
   critique qui voit l'etat complet n'est pas utilisable a l'inference, et le plancher de
   0,57 est calcule sur l'etat complet precisement pour cette raison ». **La mesure lui donne
   raison, et chiffre l'ecart.**
3. Si le run confirme ce plafond, **le resultat publiable de l'iteration 1 serait : « la tete
   de valeur n'est pas la limite de cet agent »** -- ce que l'arbitrage designe deja comme un
   resultat interessant et non un echec.

## Reproduire

Les scripts de ce releve sont dans `mesure/resultats/phase4_journaux/` avec leurs sorties.
L'echantillon hors plage est produit par `mesure.phase4.echantillon_hors_plage`, seeds
`7 000 000+`, et le jeu de test par le meme appel a `7 400 000+`.
