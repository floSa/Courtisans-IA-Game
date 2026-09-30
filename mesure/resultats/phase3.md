# Phase 3 -- le premier agent entraine

Genere par `uv run python -m mesure.phase3_mesure`. Aucune interpretation : chaque chiffre porte sa decomposition, sa composition et son denominateur. Les seuils rappeles sont ceux de `mesure/phase3_hypothese_et_instrument.md`, commite **avant** l'entrainement.

Instance : `familles=4`, 5 roles, `exemplaires=2`, `joueurs=3` -- 40 cartes, 4 tours par joueur.

Algorithme : **PPO a masque d'actions**, reseau unique partage par les trois sieges, tete de valeur, `gamma = 1`, `lambda = 1`. Pool d'entrainement : 60 % copie courante, 40 % checkpoint fige. **Ni le greedy ni l'aleatoire n'entrent dans le pool.**

## 1. Le juge -- gain moyen contre deux greedys

**Composition : 1 agent entraine contre 2 greedys, sieges permutes.** 2000 donnes x 3 sieges = **6000 parties**. Bootstrap **par donne**, 10000 rechantillons.

**Le niveau nul du gain moyen est exactement 0,0000**, et il n'est pas estime : sous l'hypothese nulle, l'esperance du gain mesure vaut 0 par la somme nulle du paragraphe 5.2 et par la permutation systematique des sieges. Voir le paragraphe 1 de la pre-inscription.

| Grandeur | Valeur | Niveau nul |
|---|---:|---:|
| **Gain moyen** | **-0.1643** | **0,0000** (exact) |
| IC 99 % bootstrap par donne | [-0.1824 ; -0.1462] | |
| Part de victoire fractionnee | 22.38 % | 33.33 % (exact) |
| Part de victoire stricte | 16.87 % | **inconnu d'avance -- jamais un seuil** |

**Seuil du protocole : la borne basse de l'IC 99 % est-elle strictement positive ?** Elle vaut **-0.1824**. **NON.** La borne haute est negative : **l'agent est battu par le greedy**.

### Le gain par siege -- a cote de la moyenne, jamais a sa place

**L'avantage de siege est massif dans cette composition** : contraste apparie entre sieges extremes **+0,5735**, IC 99 % [+0,5218 ; +0,6240], mesure sur la population de l'hypothese nulle. Un chiffre d'un seul siege ne se compare **jamais** a un chiffre agrege sur trois.

| Siege occupe | Gain moyen de l'agent |
|---|---:|
| siege 0 | -0.3069 |
| siege 1 | -0.1998 |
| siege 2 | +0.0139 |

Somme des trois : **-0.4928**, soit **trois fois le gain moyen** (-0.1643 x 3 = -0.4928).

> **Ce n'est PAS un controle de nullite, et une premiere redaction de ce rapport le presentait comme tel.** Elle ecrivait « elle n'est nulle qu'a la precision d'echantillonnage », ce qui n'est vrai que **sous l'hypothese nulle**. Chaque siege portant le meme nombre de parties, la somme des trois moyennes vaut `3 x moyenne` **par identite arithmetique**, quel que soit l'agent : elle ne vaut zero que si le gain moyen vaut zero. Ce qui est nul par construction, c'est la somme des gains des **trois sieges d'une meme partie** -- invariant I5 --, et c'est verifie au paragraphe 6, partie par partie.

## 2. Le dimensionnement, remesure sur la composition reelle

La pre-inscription mesure `sigma` et `rho` **sous l'hypothese nulle** -- le greedy mis a la place de l'agent. Un agent different a une distribution de gain differente : l'ecart entre le **SUPPOSE** de la pre-inscription et le **MESURE** ci-dessous est un chiffre, et non un oubli.

| Grandeur | Pre-inscription (hypothese nulle) | Mesure ici |
|---|---:|---:|
| `sigma(gain)` | 0,6494 | **0.5710** |
| `rho` intra-donne | −0,1400 | **-0.0565** |
| effet de plan (analyse de variance) | 0,7200 | **0.8870** |
| effet de plan (bootstrap) | 0,7223 | **0.8817** |

**Ecart de gain detectable a ce budget** : **+0.0237** sur 6000 parties, 99 % bilateral et 80 % de puissance. La pre-inscription annoncait **+0,0243**.

**Demi-largeur de l'IC 99 % du gain** : **0.0181** sur 6000 parties.

> **LA REGLE PRE-INSCRITE PORTE SUR LA DEMI-LARGEUR, PAS SUR `sigma`, ET ELLE N'EST PAS FRANCHIE.** Le paragraphe 3 de la pre-inscription ecrit : « la **demi-largeur** reelle sera remesuree sur la campagne finale et publiee a cote de celle-ci ; si **elle** en differe de plus de 10 %, c'est que `sigma` a bouge et il faudra le dire ». Le declencheur est donc la demi-largeur.
>
> Mesuree : **0.0181** contre **0,0183** pre-inscrits, au **meme budget de 6 000 parties** -- soit **-1.1 %**. **Elle reste dans la marge de 10 %, donc le declencheur pre-inscrit n'est pas franchi.**
>
> **Et `sigma` a pourtant bouge de -12.1 %** -- 0.5710 contre 0,6494. Une premiere redaction de ce rapport declarait sur cette base « `sigma` a bouge de plus de 10 % », en attribuant a la marge une grandeur qu'elle ne surveillait pas ; l'audit l'a relevee, et le pilote avait propage l'erreur sans la voir. Le fait reste vrai, c'est la regle citee qui etait la mauvaise.
>
> **La regle etait aveugle au mouvement qu'elle pretendait detecter, et c'est le resultat interessant.** Une demi-largeur ne depend pas de `sigma` seul mais de `sigma x sqrt(effet de plan / n)`. Ici `sigma` a **chute** de 12.1 % pendant que l'effet de plan **montait** de 0,7200 a 0.8870 : `0,6494 x sqrt(0,7200)` = 0.5510 contre `0.5710 x sqrt(0.8870)` = 0.5377, soit -2.4 %. **Les deux mouvements se compensent dans la demi-largeur.** Une regle de surveillance posee sur un produit ne detecte pas le mouvement d'un seul de ses facteurs : c'est `sigma` qu'il fallait surveiller, et la pre-inscription surveillait le produit.
>
> Les deux grandeurs sont donc publiees separement, et c'est la lecon : `sigma` = **0.5710** (pre-inscrit 0,6494), effet de plan = **0.8870** (pre-inscrit 0,7200), demi-largeur = **0.0181** (pre-inscrite 0,0183).

## 3. Le pool -- chaque composition, nommee

**Aucune de ces lignes n'est le juge.** Le juge est le gain moyen contre deux greedys, et lui seul. Les autres compositions repondent a d'autres questions.

| Composition | Parties | Gain moyen | IC 99 % | Part fractionnee | Neutre |
|---|---:|---:|---|---:|---:|
| 1 agent entraine contre 2 greedys, sieges permutes | 6000 | -0.1643 | [-0.1824 ; -0.1462] | 22.38 % | 33.33 % |
| 1 agent entraine FINAL contre 2 aleatoires, 500 donnes, seeds 70000+ (la composition du garde-fou, mesuree sur l'agent final) | 1500 | +0.5505 | [+0.5070 ; +0.5937] | 70.03 % | 33.33 % |
| 1 agent entraine, variante DETERMINISTE, contre 2 greedys (robustesse -- jamais a la place de la reference) | 6000 | -0.1679 | [-0.1855 ; -0.1503] | 22.14 % | 33.33 % |
| 1 agent entraine contre 2 copies de `checkpoint_01.pt` | 1500 | +0.2050 | [+0.1598 ; +0.2523] | 47.00 % | 33.33 % |
| 1 agent entraine contre 2 copies de `checkpoint_02.pt` | 1500 | +0.1957 | [+0.1482 ; +0.2433] | 46.38 % | 33.33 % |
| 1 agent entraine contre 2 copies de `checkpoint_03.pt` | 1500 | +0.1420 | [+0.0982 ; +0.1858] | 42.80 % | 33.33 % |
| 1 agent entraine contre 2 copies de `checkpoint_04.pt` | 1500 | +0.1232 | [+0.0812 ; +0.1665] | 41.54 % | 33.33 % |
| 1 agent entraine contre 2 copies de `checkpoint_05.pt` | 1500 | +0.0395 | [-0.0018 ; +0.0810] | 35.97 % | 33.33 % |
| 1 agent entraine contre 2 copies de `checkpoint_06.pt` | 1500 | +0.0227 | [-0.0198 ; +0.0648] | 34.84 % | 33.33 % |
| 1 agent entraine contre 2 copies de `checkpoint_07.pt` | 1500 | +0.0405 | [-0.0037 ; +0.0837] | 36.03 % | 33.33 % |
| 1 agent entraine contre 2 copies de `checkpoint_08.pt` | 1500 | +0.0225 | [-0.0173 ; +0.0635] | 34.83 % | 33.33 % |

### Ce que ces lignes disent, et ce qu'elles ne disent pas

La pre-inscription annonce, au paragraphe 6, que **« un agent qui ecrase ses propres checkpoints mais ne bat pas le greedy est le symptome exact de l'effondrement de convention en self-play »**. C'est la contrepartie assumee d'avoir sorti le greedy du pool d'entrainement.

**Confrontee aux chiffres, cette phrase ne s'applique qu'a moitie, et il faut le dire plutot que de la laisser conclure a notre place.**

- l'agent bat son **premier** checkpoint de **+0.2050** -- un ecart reel, mais sur un adversaire vieux de quinze minutes ;
- il bat son **dernier** de **+0.0225**, IC 99 % [-0.0173 ; +0.0635], **qui contient zero** : sur les quinze dernieres minutes, l'amelioration contre lui-meme n'est **pas etablie** a ce budget.

**« Ecraser » ne decrit donc pas ce qui est mesure.** La marge sur un checkpoint decroit a mesure que le checkpoint se rapproche de l'agent final, ce qui est attendu et ne prouve rien a soi seul : un checkpoint recent est un adversaire plus fort. Ce que ces lignes etablissent est plus etroit -- **l'agent a progresse contre lui-meme sur la duree du run**, et cette progression n'a pas suffi a atteindre le greedy.

**Ce qu'elles n'etablissent PAS** : qu'une convention de self-play soit la cause. Une convention stable et un apprentissage inacheve produisent tous deux un agent qui bat ses anciennes versions sans battre un adversaire exterieur. **Rien ici ne separe les deux hypotheses**, et il faudrait pour cela une population que cette phase n'a pas mesuree -- par exemple un second agent entraine depuis une autre graine, qui n'aurait aucune raison de partager la convention du premier.

### La variante deterministe -- rapportee a cote, jamais a la place

**Une mesure de consequence, et elle ne se lit qu'en juxtaposant les deux nombres** -- c'est la meme forme qu'en phase 2 pour le departage du greedy, et la meme raison : un renvoi vers une autre section ne se lit pas.

| | |
|---|---:|
| gain moyen, agent echantillonne (reference) | **-0.1643** |
| gain moyen, agent deterministe | **-0.1679** |
| ecart | **-0.0036** |
| demi-largeur de l'IC 99 % de la reference | 0.0181 |
| l'ecart, en demi-largeurs | **0.20** |

**Autrement dit : prendre l'action la plus probable plutot que d'echantillonner ne deplace pas le gain de l'agent a ce budget.** L'entropie de sa politique est basse -- 0,34 au dernier checkpoint --, donc les deux departages tirent le plus souvent la meme action, et ce chiffre le confirme plutot que de le supposer.

**Ce que ce chiffre n'etablit pas** : que la variante deterministe soit une bonne politique. Elle est **biaisee** -- l'indice d'une action de pose encode l'assignation, la position au banquet et l'adversaire vise --, et son seul usage est d'etre rapportee ici.

## 4. Le garde-fou -- un agent contre deux aleatoires

**Ce n'est pas un juge.** Depasser 86,52 % ne dit rien sur le fait de battre le greedy : le greedy y est deja. C'est un detecteur d'agent qui n'apprend pas.

Le **86,52 %** est une **moyenne sur les trois sieges**, agregee sur les 10 002 parties de la campagne B de la phase 2, et il ne se compare qu'a une mesure agregee de la meme facon. La colonne ci-dessous l'est.

Composition : **1 agent entraine AU CHECKPOINT contre 2 aleatoires, 600 donnes, seeds 40000+ (garde-fou)**. Chaque checkpoint : 600 donnes x 3 sieges, **les memes donnes a chaque fois**. IC corrige de **Bonferroni pour 8 regards**.

### Les niveaux -- et ils ne decident de rien

| # | s | Parties d'entrainement | Entropie | Part fractionnee | IC (Bonferroni) | Gain moyen |
|---:|---:|---:|---:|---:|---|---:|
| 1 | 902 | 185344 | 0.4726 | 57.33 % | [53.92 % ; 60.85 %] | +0.3600 |
| 2 | 1800 | 380928 | 0.3515 | 59.52 % | [55.92 % ; 63.20 %] | +0.3928 |
| 3 | 2701 | 564736 | 0.3811 | 61.77 % | [58.21 % ; 65.06 %] | +0.4265 |
| 4 | 3601 | 751104 | 0.3909 | 63.22 % | [59.90 % ; 66.61 %] | +0.4483 |
| 5 | 4501 | 935424 | 0.3435 | 65.06 % | [61.77 % ; 68.31 %] | +0.4758 |
| 6 | 5402 | 1119744 | 0.3428 | 67.56 % | [64.17 % ; 70.77 %] | +0.5133 |
| 7 | 6302 | 1303552 | 0.3091 | 69.27 % | [66.14 % ; 72.53 %] | +0.5390 |
| 8 | 7201 | 1486336 | 0.3370 | 70.13 % | [67.05 % ; 73.19 %] | +0.5519 |

> **Huit intervalles de NIVEAU ne disent pas si l'agent progresse, et une premiere redaction de ce rapport a conclu comme s'ils le disaient.** Elle ecrivait « croissance monotone sans exception » et « il progressait encore au dernier ». **Les deux sont retirees.** La monotonie de cette colonne est une propriete de ce tirage : une remesure sur les **memes donnes** avec un autre aleatoire de politique porte deux inversions, dont le dernier pas. Ce qui decide est en dessous.

### Les ecarts -- et ce sont eux qui decident

**Bootstrap apparie par donne, memes donnes des deux cotes, meme correction de Bonferroni.** Un ecart apparie ne coute pas une partie de plus : les donnes du garde-fou sont les memes a chaque checkpoint, la pre-inscription l'avait prevu, il ne manquait que de garder la serie.

**Un ecart ne se lit pas au recouvrement de deux intervalles de niveau.** Ici 7 des 7 couples consecutifs se recouvrent, alors que l'ecart des extremes est etabli : le recouvrement ignore la correlation que l'appariement rend forte.

| Ecart apparie | Valeur | IC (Bonferroni) | Etabli ? |
|---|---:|---|---|
| ckpt 1 -> 2 (portee 1) | +2.19 pt | [-1.58 pt ; +6.09 pt] | non -- dans le bruit |
| ckpt 2 -> 3 (portee 1) | +2.25 pt | [-1.82 pt ; +6.30 pt] | non -- dans le bruit |
| ckpt 3 -> 4 (portee 1) | +1.45 pt | [-2.69 pt ; +5.38 pt] | non -- dans le bruit |
| ckpt 4 -> 5 (portee 1) | +1.83 pt | [-1.99 pt ; +5.56 pt] | non -- dans le bruit |
| ckpt 5 -> 6 (portee 1) | +2.50 pt | [-1.41 pt ; +6.44 pt] | non -- dans le bruit |
| ckpt 6 -> 7 (portee 1) | +1.71 pt | [-1.87 pt ; +5.40 pt] | non -- dans le bruit |
| ckpt 7 -> 8 (portee 1) | +0.86 pt | [-2.83 pt ; +4.29 pt] | non -- dans le bruit |
| ckpt 1 -> 4 (portee 3) | +5.89 pt | [+1.72 pt ; +10.36 pt] | **etabli** |
| ckpt 2 -> 5 (portee 3) | +5.54 pt | [+1.31 pt ; +9.44 pt] | **etabli** |
| ckpt 3 -> 6 (portee 3) | +5.79 pt | [+1.51 pt ; +9.81 pt] | **etabli** |
| ckpt 4 -> 7 (portee 3) | +6.05 pt | [+2.56 pt ; +9.75 pt] | **etabli** |
| ckpt 5 -> 8 (portee 3) | +5.07 pt | [+1.35 pt ; +8.69 pt] | **etabli** |
| **ckpt 1 -> 8 (portee 7)** | **+12.80 pt** | [+8.33 pt ; +17.40 pt] | **ETABLI** |

**Ce qui est etabli : l'agent apprend.** Du premier au dernier checkpoint, **+12.80 pt**, IC [+8.33 pt ; +17.40 pt], qui **exclut 0**. C'est la seule lecture de cette section qui tienne, et elle tient franchement.

**Ce qui n'est PAS etabli : qu'il progressait ENCORE a la fin.** Aucun des 7 pas consecutifs n'est etabli, et le dernier -- ckpt 7 -> 8 -- vaut +0.86 pt, IC [-2.83 pt ; +4.29 pt], qui **contient 0**. Un quart d'heure de progres vaut environ +1.83 pt, quand la demi-largeur des IC apparies ci-dessus va de +3.56 pt a +4.06 pt : **ce budget ne peut pas trancher un pas isole**, et aucune redaction ne le lui fera dire.

> **La barre qui juge un ecart est la demi-largeur de SON PROPRE intervalle apparie, pas le 2,75 pt de la pre-inscription.** Ce 2,75 est un ecart detectable **iid sur un NIVEAU** a 1 800 parties ; les ecarts ci-dessus sont **apparies**, et leur precision reelle est celle que le bootstrap rend. Les deux mènent ici a la meme conclusion, mais les confondre serait comparer deux grandeurs qui ne portent pas sur la meme chose -- et une premiere redaction de ce paragraphe le faisait.

**Critere terminal du protocole** : au dernier checkpoint, la part fractionnee vaut **70.13 %** contre **86,52 %**. **NON franchi.**

**Declencheur du garde-fou** -- l'ecart apparie de portee 3, a partir du checkpoint 4 : **non declenche** -- les 5 ecarts de portee 3 sont tous des progres etablis, intervalle entierement au-dessus de 0.

> **Ce verdict est RECALCULE ici, il n'est pas relu dans le journal.** Le champ `declenche` du `journal.jsonl` de ce run a ete ecrit **pendant** le run, donc par la regle en vigueur ce jour-la, qui a depuis ete retiree deux fois. Le tour 2 le relisait tel quel pendant que la phrase au-dessus decrivait la regle courante : les deux concordent sur ce run, et rien ne le garantissait. Un verdict se recalcule avec la regle qu'on publie, ou il ne se publie pas.

> **Le critere terminal n'est pas franchi, et la raison que le protocole lui pretait etait fausse -- mais pas pour la raison que ce rapport donnait au premier tour.**
>
> Le protocole ecrivait : « si apres 2 h l'agent n'a pas depasse 86,52 %, on arrete : **l'agent n'apprend pas**, et rallonger ne dira rien de plus ». La premisse est verifiable, et l'ecart des extremes la contredit : +12.80 pt, IC [+8.33 pt ; +17.40 pt]. **L'agent apprend.**
>
> **Ce qui ne suit pas, et que la premiere redaction en tirait :** « il n'a pas fini d'apprendre », donc « rallonger le budget ». Cette conclusion demandait que la courbe montre encore une pente a la fin, et **aucun ecart mesure ici ne le montre**. Ce que cette section etablit s'arrete a : l'agent a appris entre le premier et le dernier checkpoint. Ce qu'il ferait d'un quart d'heure de plus n'est pas mesure.
>
> Le garde-fou lui-meme a ete corrige une **quatrieme** fois sur cette section. Sa version du 21/08/2026 se declenchait sur trois checkpoints consecutifs a intervalles recouvrants -- or 7 des 7 couples se recouvrent ici, donc elle aurait arrete ce run au **checkpoint 3, a 45 minutes sur 120**. La regle generale qui manquait aux quatre versions : **un garde-fou ne peut chercher qu'un progres plus grand que l'ecart detectable a son propre budget.** D'ou la portee 3, et `agents.campagne.portee_minimale` qui la calcule.

## 5. Les comportements B1 a B7

**La ligne de base est REGENEREE**, et ce n'est pas une commodite : ma composition est un agent contre deux greedys, un seul siege mesure. Sa ligne de base est donc **trois greedys, UN seul siege compte**, et elle n'existe pas dans le depot. Meme composition, meme decalage de graine `6000000`, memes seeds **que la phase 2** : seuls les sieges **comptes** changent.

> **« Memes seeds » designe la phase 2, PAS la campagne de l'agent**, et une premiere redaction laissait croire le contraire. La ligne de base joue les donnes **0 a 1999** -- celles de `phase2.campagne_b`, `DEPART_B = 0` --, l'agent les donnes **60000 a 61999**. **Les deux echantillons ne partagent aucune donne, et la comparaison n'est donc PAS appariee** : c'est une comparaison entre deux echantillons independants, et l'ecart detectable ci-dessous en tient compte des deux cotes. Regenerer la ligne de base sur les donnes de l'agent aurait change la population de reference pour une seconde raison, et elle n'aurait plus ete celle de la phase 2.

`comportements.ecart_de_taux` **leve** si les grains different. Elle est appelee plutot que contournee : une ligne dont le grain differe fait tomber la mesure au lieu de produire un nombre qu'il faudrait relire.

**Le detectable est calcule sur les DEUX effectifs**, chacun avec son taux et son denominateur -- `phase3_mesure.ecart_detectable_deux_echantillons`. La formule de la phase 2 suppose deux echantillons de meme taille ; les denominateurs d'action n'y obeissent pas, et l'ecart pouvait atteindre 67 % sur `B4-strict`. **Aucune ligne ne change de statut**, mais le chiffre publie au premier tour etait faux.

**Les exclusions sont recalculees au budget de 6000 parties**, jamais recopiees : ce sont des proprietes du couple `(ligne, budget)`. Voir `mesure/phase3_budget_des_comportements.py`.

> **La regle « hors budget » de la pre-inscription ne s'applique pas ici, et il faut le dire plutot que de la laisser croire appliquee.** Le paragraphe 9.2 annoncait que les huit lignes hors budget a 6 000 parties ne seraient pas comparees, et les nommait ; ces huit noms sont calcules sur l'ecart **greedy contre hasard** de la phase 2, qui n'est pas l'ecart de cette phase. La branche qui les excluait etait par ailleurs **inatteignable** -- `ecart=None` rendait `hors_budget` toujours faux --, donc elle n'a jamais rien exclu : elle est retiree. Le critere qui s'exerce est `|ecart| > detectable`, **le meme critere** exprime sur l'ecart effectivement mesure, et la colonne « Separable ? » publie desormais le nombre de parties que chaque ligne non separable demanderait.


**2 ligne(s) sont tranchees par une AUTRE regle, et le tableau la nomme.** `B4-contre-nature`, `B4-meurtre-couteux` porte(nt) un **zero absolu** d'un cote. Sur un zero, la variance binomiale est nulle : la formule normale rendrait « tout est detectable », ce qui est exactement faux, donc `ecart_detectable_deux_echantillons` rend `None`. **Ce `None` etait imprime « non separable a ce budget » au tour 2** -- une conclusion que rien n'avait calculee, et fausse. Un zero se traite par sa **borne exacte**, celle de Clopper-Pearson, qui ne suppose aucune normalite : `0/1967` a pour borne haute exacte unilaterale au risque 1 % (Clopper-Pearson) **0.2338 %** quand l'agent vaut **35.87 %** ; `0/10382` a pour borne haute exacte unilaterale au risque 1 % (Clopper-Pearson) **0.0443 %** quand l'agent vaut **3.66 %**. Le rendu **leve** desormais sur toute ligne qu'aucune regle n'a tranchee, plutot que de lui donner un verdict par defaut.

> **Le tour 2 se contredisait dans ce document meme** : ce tableau declarait `B4-contre-nature` non separable, et le paragraphe 6 argumentait une demi-page sur ce que son ecart de +35.87 pt etablit. C'est le tableau qui avait tort.

> **Les lignes `-par-partie` portent ici les MEMES nombres que leur ligne au grain du couple, et ce n'est pas un defaut.** Un seul siege est mesure par partie, donc « au moins un des 1 sieges » et « le siege mesure » comptent exactement la meme chose. C'est deja le cas de la colonne a un siege de la phase 2. Les deux sont gardees pour que le grain reste lisible dans le libelle, et parce que `ecart_de_taux` leve si on les compare a une population qui en agrege trois.

| Compteur | Agent | Ligne de base | Ecart | Detectable | Separable ? |
|---|---|---|---:|---:|---|
| `B1-collectif` | 70.37 % (4222/6000) | 72.20 % (4332/6000) | -1.83 pt | 2.82 % | non separable a ce budget -- il en faudrait 14220 de chaque cote |
| `B1-collectif-par-partie` | 70.37 % (4222/6000) | 72.20 % (4332/6000) | -1.83 pt | 2.82 % | non separable a ce budget -- il en faudrait 14220 de chaque cote |
| `B1-motif` | 42.48 % (2549/6000) | 45.83 % (2750/6000) | -3.35 pt | 3.10 % | **separable** |
| `B1-motif-par-partie` | 42.48 % (2549/6000) | 45.83 % (2750/6000) | -3.35 pt | 3.10 % | **separable** |
| `B1-savoir-commun` | 43.13 % (2588/6000) | 46.28 % (2777/6000) | -3.15 pt | 3.10 % | **separable** |
| `B1-savoir-commun-par-partie` | 43.13 % (2588/6000) | 46.28 % (2777/6000) | -3.15 pt | 3.10 % | **separable** |
| `B1-strict` | 28.05 % (1683/6000) | 28.53 % (1712/6000) | -0.48 pt | 2.81 % | non separable a ce budget -- il en faudrait 202842 de chaque cote |
| `B1-strict-par-partie` | 28.05 % (1683/6000) | 28.53 % (1712/6000) | -0.48 pt | 2.81 % | non separable a ce budget -- il en faudrait 202842 de chaque cote |
| `B1-tentative` | 55.53 % (3332/6000) | 61.28 % (3677/6000) | -5.75 pt | 3.07 % | **separable** |
| `B1-tentative-par-partie` | 55.53 % (3332/6000) | 61.28 % (3677/6000) | -5.75 pt | 3.07 % | **separable** |
| `B2-banquet` | 30.56 % (4383/14340) | 36.70 % (5284/14399) | -6.13 pt | 1.90 % | **separable** |
| `B2-cibles` | 79.18 % (11354/14340) | 82.65 % (11901/14399) | -3.47 pt | 1.58 % | **separable** |
| `B2-contestee` | 68.36 % (9803/14340) | 74.26 % (10692/14399) | -5.89 pt | 1.82 % | **separable** |
| `B2-contestee-publique` | 66.40 % (9522/14340) | 72.55 % (10447/14399) | -6.15 pt | 1.85 % | **separable** |
| `B2-destination/banquet-Disgrace` | 18.15 % (2602/14340) | 15.76 % (2270/14399) | +2.38 pt | 1.51 % | **separable** |
| `B2-destination/banquet-Estime` | 12.42 % (1781/14340) | 20.93 % (3014/14399) | -8.51 pt | 1.49 % | **separable** |
| `B2-destination/domaine adverse` | 32.74 % (4695/14340) | 35.41 % (5099/14399) | -2.67 pt | 1.91 % | **separable** |
| `B2-destination/domaine propre` | 36.69 % (5262/14340) | 27.89 % (4016/14399) | +8.80 pt | 1.88 % | **separable** |
| `B2-fragile-2` | 77.11 % (11057/14340) | 81.81 % (11780/14399) | -4.71 pt | 1.63 % | **separable** |
| `B3-expose` | 43.92 % (10542/24000) | 41.25 % (9899/24000) | +2.68 pt | 1.54 % | **separable** |
| `B3-expose-vraie` | 48.80 % (11712/24000) | 46.48 % (11156/24000) | +2.32 pt | 1.56 % | **separable** |
| `B3-simultane` | 6.73 % (1615/24000) | 9.60 % (2304/24000) | -2.87 pt | 0.85 % | **separable** |
| `B4-brut` | 31.93 % (3814/11945) | 15.93 % (1967/12349) | +16.00 pt | 1.84 % | **separable** |
| `B4-contre-nature` | 35.87 % (1368/3814) | 0.00 % (0/1967) | +35.87 pt | - | **separable** -- par bornes exactes : le zero de la ligne de base a pour borne haute exacte unilaterale au risque 1 % (Clopper-Pearson) **0.2338 %**, et l'autre cote vaut 35.87 % |
| `B4-departage` | 53.88 % (2055/3814) | 68.38 % (1345/1967) | -14.50 pt | 4.52 % | **separable** |
| `B4-meurtre-couteux` | 3.66 % (298/8131) | 0.00 % (0/10382) | +3.66 pt | - | **separable** -- par bornes exactes : le zero de la ligne de base a pour borne haute exacte unilaterale au risque 1 % (Clopper-Pearson) **0.0443 %**, et l'autre cote vaut 3.66 % |
| `B4-strict` | 10.25 % (391/3814) | 31.62 % (622/1967) | -21.37 pt | 3.96 % | **separable** |
| `B4-tout-dos` | 4.95 % (591/11945) | 3.63 % (448/12349) | +1.32 pt | 0.89 % | **non compare** : texte de la definition : elle ne nomme aucun autre joueur |
| `B5-pire-cas` | 18.52 % (1647/8893) | 13.44 % (1219/9068) | +5.08 pt | 1.87 % | **separable** |
| `B5-renfort` | 18.23 % (2270/12454) | 13.27 % (1746/13159) | +4.96 pt | 1.56 % | **non compare** : texte de la definition : elle ne nomme aucun autre joueur |
| `B7-gaspillage` | 0.10 % (24/24000) | 0.08 % (19/24000) | +0.02 pt | 0.09 % | non separable a ce budget -- il en faudrait 120418 de chaque cote |
| `B7-gaspillage-vraie` | 0.13 % (32/24000) | 0.10 % (24/24000) | +0.03 pt | 0.11 % | non separable a ce budget -- il en faudrait 61242 de chaque cote |
| `B7-lumiere` | 10.27 % (2464/24000) | 9.60 % (2304/24000) | +0.67 pt | 0.93 % | non separable a ce budget -- il en faudrait 11754 de chaque cote |
| `B7-occasions` | 0.81 % (195/24000) | 0.62 % (148/24000) | +0.20 pt | 0.26 % | non separable a ce budget -- il en faudrait 10802 de chaque cote |

## 6. B4 -- le piege de lecture, et pourquoi je refuse la lecture flatteuse

**Quatre compteurs de B4 sont definis par rapport a `greedy.evaluer_actions`**, c'est-a-dire par l'evaluation **myope** du greedy lui-meme -- `B4-strict`, `B4-departage`, `B4-contre-nature` et `B4-meurtre-couteux`. Chez le greedy leur valeur est **tautologique** : `choisir` prend un argmax, donc il ne peut pas se contredire. Les deux zeros absolus de la phase 2 sont dans ce lot.

**Chez un agent dont l'argmax n'est pas celui de l'etalon, ces compteurs cessent d'etre tautologiques.** Ils mesurent alors une chose et une seule : **a quelle frequence l'agent contredit l'evaluation myope du greedy.**

| Compteur | Agent | Ligne de base (3 greedys) | Ce que l'ecart mesure |
|---|---|---|---|
| `B4-contre-nature` | 35.87 % (1368/3814) | 0.00 % (0/1967) | desaccord avec l'evaluation myope |
| `B4-meurtre-couteux` | 3.66 % (298/8131) | 0.00 % (0/10382) | desaccord avec l'evaluation myope |
| `B4-brut` | 31.93 % (3814/11945) | 15.93 % (1967/12349) | desaccord avec l'evaluation myope |
| `B4-strict` | 10.25 % (391/3814) | 31.62 % (622/1967) | desaccord avec l'evaluation myope |

### La lecture que la phase 2 propose, et pourquoi elle ne tient pas ici

Le rapport de la phase 2 ecrit : « pour un agent de la phase 3, ce meme zero cesse d'etre tautologique : son argmax n'est pas celui de l'etalon, donc `B4-contre-nature` devient un vrai diagnostic -- et **un refus par anticipation d'un retournement y comptera, ce qui se lit comme un signe de planification** et non comme un defaut ».

**Je refuse cette lecture pour cet agent, et le motif est dans le paragraphe 1.** `B4-contre-nature` vaut **35.87 %** chez lui contre **0.00 %** chez le greedy -- un ecart **separable**, et le paragraphe 5 dit par quelle regle : la borne haute exacte unilaterale au risque 1 % (Clopper-Pearson) de ce zero vaut 0.2338 %. Deux hypotheses expliquent le meme chiffre :

1. **l'agent voit quelque chose que l'evaluation myope ne voit pas** -- il refuse un meurtre localement gagnant parce qu'il anticipe un retournement. C'est la lecture flatteuse ;
2. **l'agent joue moins bien** -- il refuse des meurtres qu'il aurait fallu commettre.

**Les deux produisent exactement le meme compteur.** Ce qui les separe n'est pas dans B4, il est dans le juge : **l'agent est battu par le greedy**, gain moyen negatif borne haute comprise. Un agent qui contredit massivement l'evaluation d'un adversaire qui le bat n'a pas etabli qu'il voit plus loin ; il a etabli qu'il decide autrement. La seconde hypothese est la plus economique, et rien ici ne la refute.

**Ce que ce compteur etablit, mot pour mot** : l'agent contredit l'evaluation myope du greedy a cette frequence. **Il n'etablit ni planification, ni erreur** -- il faudrait pour trancher une evaluation de reference qui ne soit ni myope ni celle de l'agent, et cette phase n'en a pas.

La meme reserve vaut pour `B4-meurtre-couteux`, `B4-strict` et `B4-departage`, dont les denominateurs sortent du meme argmax.

## 7. L'audit de ce resultat, par ses propres controles

**Les zeros absolus de la ligne de base -- ceux que R4 nomme ci-dessous, avec leurs comptes -- sont confrontes a un cas construit a la main**, comme le paragraphe 0.2 l'exige, par quatre cas de `tests/mesure/test_comportements.py` : deux qui fabriquent le nœud et exigent que le compteur le classe, un qui retrouve les zeros sur de vraies parties, et **un contre-cas** ou une politique uniforme en produit -- sans lui, un compteur mort rendrait le meme zero. Le controle R4 les **liste** desormais : au premier tour il ne regardait que l'agent, et imprimait « aucune » pendant que le rapport en publiait deux.

**Ces controles sont ecrits et commites AVANT que l'agent ne soit mesure** -- `mesure/phase3_audit.py`. Un controle ecrit apres avoir vu un chiffre est un controle que le chiffre a passe par construction.

Ils portent sur des **unites**, des **denominateurs** et des **populations**, jamais sur des valeurs : reproduire un nombre ne le valide pas, et un facteur trois indu a survecu a deux verifications reussies en phase 2 pour cette raison.

| Question | Controle | Verdict | Preuve |
|---|---|---|---|
| Q1 | le niveau nul du juge, recalibre sur les seeds du verdict | concluant | gain moyen +0.0062, IC 99 % [-0.0124 ; +0.0255] sur 6000 parties, seeds 60000-61999 |
| Q1 | la somme des gains vaut 0 dans chaque partie (I5, paragraphe 5.2) | concluant | ecart maximal a zero : 0.000e+00 sur 6000 parties de « 1 agent entraine contre 2 greedys, sieges permutes » |
| Q2 | chaque siege exactement une fois par donne | concluant | 2000 donnes verifiees, 0 desequilibrees |
| Q2 | le bootstrap tire des donnes -- deux routes vers l'effet de plan concordent | concluant | effet bootstrap 0.8817, effet par analyse de variance 0.8870 ; un bootstrap qui tirerait des parties rendrait 1,0000 |
| Q3 | les plages de donnes ne se chevauchent pas | concluant | dimensionnement [20000, 22000); entrainement [100000, 1586336); garde-fou [40000, 40600); pool aleatoire [70000, 70500); pool checkpoint 1 [80000, 80500); pool checkpoint 2 [81000, 81500); pool checkpoint 3 [82000, 82500); pool checkpoint 4 [83000, 83500); pool checkpoint 5 [84000, 84500); pool checkpoint 6 [85000, 85500); pool checkpoint 7 [86000, 86500); pool checkpoint 8 [87000, 87500); variante deterministe [90000, 92000); verdict [60000, 62000) ; disjointes |
| R1 | le denominateur du verdict est `donnes x sieges` | concluant | 2000 donnes x 3 sieges = 6000, rapporte : 6000 |
| R2 | chaque composition est nommee, et les noms sont distincts | concluant | 12 compositions, 12 noms distincts |
| R3 | les lignes comparees sont au meme grain | concluant | 32 lignes comparees sur 34, 0 a grains differents |
| R4 | les zeros et les cent pour cent, des DEUX cotes, listes pour traitement individuel | *releve* -- il liste, il ne juge pas | 2 valeur(s) extreme(s) sur 34 lignes : B4-contre-nature [ligne de base] = 0/1967 -> bornes exactes -- un taux degenere, B4-meurtre-couteux [ligne de base] = 0/10382 -> bornes exactes -- un taux degenere |
| R5 | l'unite -- observations par partie -- relevee des deux cotes, numerateurs non regardes | *releve* -- il liste, il ne juge pas | 5 compteur(s) dont l'unite differe de plus de 5 % : B4-contre-nature 0.636 vs 0.328, B4-departage 0.636 vs 0.328, B4-meurtre-couteux 1.355 vs 1.730, B4-strict 0.636 vs 0.328, B5-renfort 2.076 vs 2.193. Un ecart n'est pas fautif en soi -- un denominateur d'action depend de la politique -- mais il doit etre lu avant de comparer les taux. |

**8 controles eprouves, aucun en echec ; 2 releves, qui ne s'y comptent pas -- R4, R5.**

> **Un controle qui ne peut pas echouer ne se compte pas parmi les concluants**, et c'est desormais une regle du paragraphe 0.2 du protocole. Une premiere redaction de ce rapport annoncait « dix controles, aucun en echec » alors que **deux** d'entre eux passaient un `True` **litteral** : ils listaient les zeros et les ecarts d'unite sans jamais pouvoir tomber. Le compte rendu affirmait par-dessus que **chacun** des dix etait verifie capable d'echouer, alors que le fichier de tests n'en cassait que six.
>
> Les deux constructeurs sont donc distincts -- `_epreuve` et `_releve` --, `tests/mesure/test_phase3_audit.py` **lit l'AST de `mesure/phase3_audit.py`** pour refuser qu'un booleen litteral soit passe a `_epreuve`, et les quatre controles qui n'etaient pas casses le sont, chacun par reinjection de la faute qu'il pretend attraper.

## 8. Ce que ces chiffres n'etablissent PAS

**Ecrit avant la mesure.** Les points 1 a 6 sont le paragraphe 10 de la pre-inscription, mot pour mot ; le point 7 vient de son paragraphe 9.2, et le point 8 du paragraphe 2.2. Une premiere redaction attribuait les sept au seul paragraphe 10, dont elle omettait par ailleurs un point -- celui sur `sigma`, ici rendu au 8.

1. **B1 et B3 mesurent la frequence a laquelle un MOTIF apparait, jamais une planification.** Ecrire « l'agent planifie des retournements dans X % des parties » serait faux quel que soit X. Le chiffre s'intitule *frequence du motif*, jamais *frequence de planification*.
2. **B1 est plafonne par les 7,40 % de parties portant une perte d'acquis qu'aucun siege ne pouvait voir**, mesures en phase 1. Ces retournements sont **invulnerables a toute planification, par n'importe quel agent** : c'est un plafond du mesurable, pas un defaut d'agent.
3. **Battre le greedy ne dit pas que l'agent est fort.** Le greedy a un horizon d'un tour, et son gain publie est un **plancher** de lui-meme -- son ciblage est plus myope que sa specification. Aucun chiffre ici ne borne la distance entre l'agent et un bon joueur.
4. **Rien ici ne se transporte a `complet-3j`** -- 6 familles, 90 cartes, 10 tours.
5. **Le controle de collision de tenseurs est un echantillon, pas une preuve d'injectivite.**
6. **Aucun resultat de cette phase ne valide le moteur.** Elle le suppose conforme ; c'est la phase 0 qui l'etablit, et elle est close.
7. **B7 devient separable par le bas a ce budget, il ne devient pas informatif.** `B7-occasions` vaut 1,22 % des poses au banquet : l'occasion de se manifester est rare, et un taux bas se lit sur ce fond-la. *(Paragraphe 9.2.)*
8. **`sigma` est mesure sous l'hypothese nulle et SUPPOSE valoir sous l'agent.** Il est remesure au paragraphe 2, et il a bouge. *(Paragraphe 2.2.)*

**Trois limites de plus, que le premier tour n'ecrivait pas et que l'audit a etablies.**

9. **La courbe du garde-fou n'etablit pas que l'agent progressait ENCORE a la fin.** Elle etablit qu'il a progresse du premier au dernier checkpoint. Aucun pas consecutif n'atteint l'ecart detectable de ce budget -- voir le paragraphe 4.
10. **Les 20 mutations de `outillage/mutation.py` ne couvrent AUCUN fichier de cette phase.** Elles ciblent toutes `courtisans/`, ce que le paragraphe 0.3 du protocole impose -- `agents/greedy.py` est la ligne de base de toutes les phases et ne porte aucune mutation. « 20 mutations, toutes detectees » ne dit donc **rien** de `agents/reseau.py`, `agents/entrainement.py`, `agents/campagne.py` ni de `mesure/phase3*.py` : ce que ces fichiers ont, ce sont leurs tests, pas une preuve que ces tests mordent. **Etendre le perimetre des mutations est un arbitrage de perimetre, remonte au pilote et non decide ici.**
11. **Les comportements comparent deux echantillons de donnes DISJOINTES** -- 0 a 1999 pour la ligne de base, 60000 a 61999 pour l'agent. La comparaison n'est pas appariee, et sa puissance est celle de deux echantillons independants.

**Deux limites de plus, etablies par l'audit croise du tour 2 -- qui a REJETE les corrections du tour 1 sur des defauts qu'elles avaient elles-memes introduits.**

12. **Les deux lignes a zero absolu ne sont pas separees par la regle du reste du tableau.** Elles le sont par des bornes exactes, un critere de non-recouvrement, plus conservateur et de puissance differente -- voir le paragraphe 5. Deux verdicts « separable » du meme tableau ne viennent donc pas tous du meme raisonnement, et la colonne le dit ligne par ligne. **Ce que le tour 1 en publiait etait faux**, et ce que le tour 2 en publiait -- « non separable a ce budget » -- etait une conclusion qu'aucun calcul n'avait rendue.
13. **Le garde-fou n'a jamais ete eprouve en conditions reelles sur un effondrement.** Sa version 5 laissait passer une chute etablie -- **17,80 points sur le support de l'auditeur du tour 2**, qui n'est pas un checkpoint de ce run -- parce qu'elle demandait « l'ecart est-il etabli ? » au lieu de « est-ce un progres etabli ? ». Le defaut est corrige et un cas hostile le tient, mais **il a ete trouve par un auditeur, pas par le run** : ce run n'a pas eu d'effondrement, donc rien n'a exerce cette branche en vrai. **Cinquieme defaut du meme garde-fou, et le cinquieme est ne dans la correction du quatrieme.**

## 9. Duree machine -- 10 passe(s)

**10 passes**, etendue publiee. Le temps mural mesure l'etat de la machine, pas le cout du code : le rapport max/min ci-dessous est a lire comme tel, et non comme une variation du programme.

| Etape | Minimum | Maximum | Rapport max/min |
|---|---:|---:|---:|
| 1 agent contre 2 greedys | 81.2 s | 92.7 s | 1.14 |
| 1 agent contre 2 aleatoires | 16.1 s | 20.0 s | 1.24 |
| 1 agent DETERMINISTE contre 2 greedys | 82.8 s | 90.9 s | 1.10 |
| 1 agent contre 2 x checkpoint_01.pt | 18.8 s | 23.0 s | 1.22 |
| 1 agent contre 2 x checkpoint_02.pt | 21.3 s | 24.8 s | 1.16 |
| 1 agent contre 2 x checkpoint_03.pt | 18.8 s | 21.6 s | 1.15 |
| 1 agent contre 2 x checkpoint_04.pt | 19.1 s | 23.1 s | 1.21 |
| 1 agent contre 2 x checkpoint_05.pt | 22.2 s | 26.8 s | 1.21 |
| 1 agent contre 2 x checkpoint_06.pt | 19.0 s | 24.5 s | 1.29 |
| 1 agent contre 2 x checkpoint_07.pt | 18.9 s | 22.4 s | 1.19 |
| 1 agent contre 2 x checkpoint_08.pt | 18.8 s | 21.8 s | 1.16 |
| ligne de base : 3 greedys, 1 siege compte | 73.0 s | 85.7 s | 1.17 |
| auto-audit | 80.5 s | 92.2 s | 1.15 |

Total par passe : 505.4 s, 504.9 s, 499.4 s, 502.2 s, 493.7 s, 494.8 s, 493.9 s, 565.7 s, 518.3 s, 524.3 s -- etendue 493.7-565.7 s, rapport 1.15.
