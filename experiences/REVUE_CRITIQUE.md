# Revue critique du projet, et ce qui marche — 27/09/2026

Session autonome d'environ 1 h 30. Il s'agit d'une **exploration**, pas d'une phase au sens
du protocole : rien n'est pré-inscrit ni audité. Les chiffres sont néanmoins mesurés sur une
arène calibrée, et chaque ligne se rejoue par une commande (§6).

---

## 1. En une phrase

**Le projet a construit un excellent moteur et un appareil de mesure très rigoureux, puis il a
choisi un algorithme mal adapté au jeu et une architecture qui ne peut pas représenter une
partie des décisions. Il a ensuite diagnostiqué le mauvais organe, celui qui se voyait dans
les métriques.**

En une séance, sans entraînement lourd :

- trois agents simples battent le greedy avec des intervalles entièrement positifs : PIMC,
  valeur d'après-coup, recherche + valeur ;
- l'agent de valeur bat aussi le greedy **sur le vrai jeu à 90 cartes** : +0,169, IC 99 %
  [+0,112 ; +0,227] ;
- le PPO de la phase 3 est dernier partout.

**La voie suivante est l'itération experte** : une recherche qui simule ses adversaires
avec la politique apprise, puis un réseau qui distille cette recherche (§4).

## 2. Résultats de la séance

Juge : **gain moyen** de l'agent contre **deux greedys de référence**, les trois sièges
permutés sur chaque donne. Le niveau nul vaut exactement 0. L'IC est un bootstrap par donne,
99 % bilatéral, par percentiles, sur 5 000 rééchantillons. Les donnes d'arène sont prises à
partir de 5 000 000, celles des données d'apprentissage à partir de 8 000 000 : les deux plages
sont disjointes, et disjointes de toutes les plages du dépôt.

### 2.1 Instance réduite `entrainement-3j` (40 cartes, 4 tours) — contre deux greedys

| Agent | Gain moyen | IC 99 % | Parties | Donnes | Coût |
|---|---:|---|---:|---|---|
| greedy (contrôle du niveau nul) | +0,007 | [−0,032 ; +0,046] | 1 200 | 5 000 000+ | — |
| **PPO phase 3** (`models/phase3/final.pt`) | **−0,185** | [−0,226 ; −0,144] | 1 200 | 5 200 000+ | 2 h GPU |
| PIMC, 8 mondes, rollouts greedy | +0,129 | [+0,066 ; +0,193] | 600 | 5 000 000+ | 0 entraînement ; ~0,6 s/décision |
| PIMC, 24 mondes, rollouts greedy | +0,194 | [+0,124 ; +0,269] | 450 | 5 100 000+ | 0 entraînement ; ~2 s/décision |
| **Valeur d'après-coup v1** (40 k parties greedy) | **+0,120** | [+0,076 ; +0,166] | 1 200 | 5 200 000+ | 4,5 min de données + 30 s de GPU ; ~10 ms/décision |
| **Valeur d'après-coup v1b** (120 k parties greedy) | **+0,149** | [+0,105 ; +0,194] | 1 200 | 5 200 000+ | 12 min de données + 1 min de GPU |
| Valeur v2 (v1 + auto-jeu de v1) | +0,095 | [+0,049 ; +0,140] | 1 200 | 5 200 000+ | +9 min de données |
| **Recherche + valeur** : PIMC tronqué à 1 tour, 8 mondes, feuilles notées par v1b | **+0,202** | [+0,130 ; +0,274] | 600 | 5 500 000+ | ~0,3 s/décision |

### 2.2 Instance réduite — entre agents neufs

| Agent | Adversaires | Gain moyen | IC 99 % | Parties | Donnes |
|---|---|---:|---|---:|---|
| Valeur v2 | 2 × v1 | **+0,114** | [+0,071 ; +0,160] | 1 200 | 5 300 000+ |
| PIMC, 8 mondes, rollouts greedy | 2 × v1b (*) | −0,018 | [−0,093 ; +0,060] | 450 | 5 400 000+ |
| Recherche + valeur (v1b) | 2 × v1b | +0,013 | [−0,047 ; +0,076] | 600 | 5 500 000+ |
| Recherche + valeur, **adversaires simulés par v1b**, 4 mondes | 2 × v1b | +0,031 | [−0,053 ; +0,117] | 360 | 5 600 000+ |

(*) Les deux v1b de cette ligne sont de la version antérieure au correctif de fuite (§2.4).
Le correctif ne change pas le chiffre de v1b contre les greedys (+0,149 avant comme après).

**Ni PIMC seul, ni recherche + valeur ne battent v1b.** Les deux recherches simulent leurs
adversaires **avec le greedy**, c'est-à-dire exactement avec l'adversaire réel quand on les
juge contre le greedy. Une bonne partie de leur avance y est donc de l'**exploitation d'un
modèle d'adversaire exact**. Face à un adversaire qu'elles ne modélisent pas, elle
disparaît.

C'est l'enseignement le plus utile de la séance pour la suite : **dans la recherche, les
adversaires doivent être simulés par la politique apprise elle-même**, et pas par le
greedy. C'est exactement la boucle d'itération experte du §4.1. Et c'est aussi pourquoi le
greedy ne suffit pas comme seul juge (§4.3).

Premier essai dans ce sens (dernière ligne du tableau) : une estimation positive, mais **non
établie**. Avec 4 mondes et un seul tour d'horizon, la recherche ajoute peu à une valeur de
R² 0,18. Il faudra plus de mondes, plus de profondeur et des évaluations par lot, ou une
meilleure valeur. C'est le chantier du §4.1, pas un résultat.

### 2.3 Le vrai jeu : 90 cartes, 3 joueurs, 10 tours — contre deux greedys

`COURTISANS_INSTANCE=complete`. Tenseur de 293 entrées, 48 décisions par partie.

| Agent | Gain moyen | IC 99 % | Parties | Donnes |
|---|---:|---|---:|---|
| greedy (contrôle du niveau nul) | −0,012 | [−0,064 ; +0,044] | 900 | 5 000 000+ |
| **Valeur d'après-coup c1** (15 k parties greedy, R² ≈ 0,10) | **+0,076** | [+0,019 ; +0,137] | 900 | 5 000 000+ |
| **Valeur d'après-coup c1b** (60 k parties greedy) | **+0,169** | [+0,112 ; +0,227] | 900 | 5 000 000+ |

**La méthode tient sur le jeu réel, et elle y marche mieux.** Passer de 15 000 à 60 000
parties fait monter le gain de +0,076 à +0,169, sur les mêmes donnes. Les intervalles se
touchent à peine : c'est une tendance nette, pas un écart établi. Le réseau sur-apprend dès
la 2e époque : **les données sont le facteur limitant**, pas l'architecture. Coût de c1b :
les 15 000 parties de c1 en 7 min 37 s sur 11 cœurs, plus les 45 000 suivantes, qui n'ont pas
été chronométrées séparément ; l'entraînement prend environ 1 min de GPU.

### 2.4 Contrôles de l'instrument

- **Contrôle du niveau nul.** Le greedy mis à la place de l'agent donne +0,007, et
  l'intervalle contient 0.
- **L'arène est cohérente avec les mesures du dépôt.** Le PPO de la phase 3 y obtient −0,185 ;
  le dépôt publiait −0,164, IC [−0,182 ; −0,146]. Les deux intervalles se recouvrent.
- **Pas de fuite d'information** (`experiences/fuite_terminal.py`). Sur 19 977 vues, dont
  2 700 terminales, re-tirer l'identité des Espions adverses et la pioche ne change jamais le
  tenseur du siège. Le témoin positif mord : le brouillage modifie le plateau réel dans
  868 terminaux sur 900 et les scores réels dans 721.
- **Une fuite dans l'agent d'après-coup, trouvée et corrigée pendant la séance**
  (`experiences/fuite_apres_coup.py`). Au ciblage, jouer « tuer le dos n° i » **sur l'état
  réel** révèle la carte tuée, puisque la défausse est publique. La première version notait
  donc un meurtre en connaissant déjà sa victime. Correctif : au ciblage, chaque action est
  notée en moyenne sur 8 mondes re-tirés à l'aveugle.
  - Après correctif : sur 996 nœuds où un dos adverse est ciblable, 3 essais chacun, la
    décision sur l'état réel et sur un monde re-tiré diffère **0 fois sur 2 988**.
  - Témoin positif : l'ancienne version différait **514 fois sur 2 988**.
  - Tous les chiffres « valeur » du tableau 2.1 sont ceux de la version corrigée. L'effet
    de la fuite était faible : v1 passe de +0,128 à +0,120, v1b reste à +0,149.

### 2.5 À lire avec leurs limites

- Toutes les lignes ne portent pas sur les mêmes donnes. Les comparaisons **directes** entre
  agents neufs se lisent au tableau 2.2.
- PIMC à 24 mondes contre 8 mondes, v1b contre v1, recherche + valeur contre v1b face au
  greedy : les intervalles se recouvrent. Ce sont des **tendances**, pas des écarts établis.
- v2 bat v1 nettement, mais fait moins bien que v1 contre le greedy (non établi). C'est un
  signe de **non-transitivité** : il faut une ligue d'adversaires, pas un seul juge (§4.3).

## 3. Critique : ce qui a été bien fait, et ce qui ne l'a pas été

### 3.1 Ce qui est solide, et qu'il faut garder

- **Le moteur.** Il est conforme, testé par 18 contrôles de conformité et des invariants, et
  sa suite de mutation échoue quand il le faut. C'est le socle de tout, et il est
  irréprochable.
- **L'aveuglement prouvé des agents**, avec la perception et le brouilleur. Sans cela, aucun
  chiffre d'IA à information imparfaite ne vaut quoi que ce soit.
- **Le juge.** Gain moyen, sièges permutés, bootstrap par donne : c'est le bon juge.
  L'avantage de siège est énorme sous jeu greedy (siège 2 ≈ +0,44, siège 0 ≈ −0,27), et la
  permutation est indispensable.

### 3.2 Le déséquilibre processus / expériences

163 commits. Pour la partie IA, **un seul entraînement de 2 h**. L'essentiel de l'effort est
allé au protocole : cinq versions du garde-fou, trois tours d'audit par phase, tests de
mutation du code de *mesure*, débat sur la latéralité d'un « 99 % ».

Cette rigueur est celle d'un **essai confirmatoire**. Elle convient pour publier une
conclusion, pas pour **chercher** un algorithme. Le règlement « une variable à la fois,
pré-inscrite, auditée deux fois » donne une boucle d'itération de plusieurs jours. Or une
IA de jeu se trouve en faisant des dizaines d'essais rapides sur une arène fiable. Cette
arène, le projet l'a : il faut s'en servir.

**Recommandation.** Séparer deux régimes :

1. un régime **exploratoire**, avec une arène figée et calibrée (celle-ci ou `mesure/phase3`),
   des essais en minutes, un journal léger ;
2. un régime **confirmatoire**, avec pré-inscription et audit croisé, réservé au moment où
   l'on veut **affirmer** qu'un agent bat un autre.

### 3.3 Le choix de l'algorithme : PPO sans modèle contre un agent qui cherche

Le greedy est un **agent de recherche** : une recherche à un tour, avec un modèle exact du
décompte. Le projet lui a opposé un **PPO sans modèle**, entraîné de zéro sur un gain
terminal ±1 et épars. Il se privait ainsi des deux atouts du jeu :

- **un simulateur parfait** : le moteur, que l'on peut cloner à volonté ;
- **une information majoritairement publique** (§2.6 des règles). Dans l'instance à 3
  joueurs, au moment où l'on décide, **les mains adverses sont toujours vides**. La seule
  inconnue est l'identité des Espions adverses et l'ordre de la pioche. On peut donc
  échantillonner les mondes compatibles exactement, sans aucune approximation.

Dans les jeux de cartes à information imparfaite (Bridge, Skat, Dame de pique, Jass,
Hanabi), l'état de l'art repose sur **PIMC ou ISMCTS, plus une évaluation apprise**. Le PPO
de zéro n'y figure pas. **PIMC avec des rollouts greedy bat le greedy sans aucun
apprentissage** (§2), et cela s'est codé en 80 lignes.

### 3.4 Deux défauts d'architecture qui condamnaient le PPO

**a) Le ciblage de l'Assassin est aveugle. Mesuré, `experiences/ciblage_aveugle.py`.**

L'action de ciblage `i` signifie « tuer la i-ème cible valide », dans l'ordre d'arrivée des
cartes dans la zone. Or le tenseur ne contient que des **comptes agrégés** : il ne dit pas
quelle carte est la cible `i`. Sur 14 368 nœuds de ciblage en jeu greedy :

- 9 246 (**64 %**) ont au moins deux cibles d'identités différentes ;
- sur ces 9 246, **dans 100 % des cas**, inverser l'ordre d'arrivée change la carte désignée
  par chaque indice sans changer le tenseur **d'un bit**.

Le réseau choisit donc sa victime **à l'aveugle** deux fois sur trois. Même le refus change
d'indice d'un nœud à l'autre. L'Assassin est pourtant l'un des deux leviers de retournement
du jeu (§2.2 des règles). Le README l'annonçait comme dette n° 2 (« l'encodage par cible
n'est pas écrit »), et la phase 3 a entraîné quand même. Le taux de refus du PPO (31,9 %,
contre 15,9 % pour le greedy) a été lu comme « voit plus loin ou joue moins bien ». La
cause la plus simple est que **l'agent ne peut pas savoir qui il tue**.

**b) L'action de pose est un indice de permutation d'une main triée.**

La tête de 24 logits code « la 1re carte de la main triée au banquet, la 2e chez moi… ».
Pour apprendre ce que fait l'action 7, le réseau doit apprendre le tri canonique de la main,
puis le décodage en base mixte, puis leur conséquence. C'est apprenable, mais c'est un
détour énorme pour un signal ±1 épars. **La bonne représentation est la conséquence de
l'action** : l'état d'après-coup. L'agent « valeur d'après-coup » fait exactement cela : il
clone l'état, joue l'action, et note la vue qui en résulte. Les deux défauts disparaissent
par construction.

### 3.5 La conclusion trop hâtive : « le critique est mauvais »

C'est la réponse directe à ta question.

1. **Phase 3.** Le journal écrit : « La valeur n'est pas imprédictible dans ce jeu : **le
   critique est mauvais** ». Il appuie cette phrase sur un plancher de 0,57 calculé sur
   **l'état complet**, donc sur des informations qu'aucun joueur n'a. Conclusion tirée d'une
   grandeur inaccessible.
2. **Phase 4.** Le projet l'a découvert lui-même, et c'est à son crédit : l'itération 1 a été
   **réfutée avant d'être entraînée**. Mais il a fallu pour cela une phase entière.
3. **Le levier était mal choisi dès le départ, et c'était calculable sur papier.** Avec
   λ = 1, le critique ne sert qu'à **réduire la variance** de l'avantage `R − V(s)`. La
   variance résiduelle vaut `(1 − R²)·Var(R)`. Passer d'un R² de 0,10 à 0,12 réduit la
   variance de 2 %. Même le 0,57 fantôme ne l'aurait réduite que de moitié, ce qui ne
   transforme pas un agent à −0,16 en agent gagnant.
4. **La preuve par l'expérience.** Le réseau de valeur v1 a un R² de **0,17**, sur des
   parties greedy : c'est le même ordre de grandeur que le critique jugé « mauvais », qui
   était à 0,10, sur une autre population (l'auto-jeu du PPO), donc non directement
   comparable. **Utilisé pour noter des après-coups, il bat le
   greedy** à +0,120, et v1b, avec R² = 0,18, à +0,149. Sur le jeu complet, c1 gagne avec
   un R² d'environ 0,10. La précision du critique n'a jamais été le frein. Le frein, c'est ce
   qu'on fait de la valeur.

**Deuxième conclusion à ne pas tirer.** La phase 4 écrit que la direction « réparer le
critique » est « fermée pour cet agent et cette observation ». C'est juste au sens étroit.
Mais la tentation, avec la tête auxiliaire de l'itération 2, est de continuer à polir le
même PPO. **Je recommande d'abandonner la ligne PPO sur indices d'action**, et non de
l'itérer.

### 3.6 Autres points

- **L'effondrement d'entropie.** Au premier checkpoint (15 min), l'entropie vaut déjà 0,47,
  pour un maximum de ln 24 ≈ 3,18. Elle finit à 0,34 (`models/phase3/journal.jsonl`). La
  politique s'est figée très tôt. C'est cohérent avec un signal épars et une architecture
  qui ne voit pas ses actions.
- **L'efficacité en échantillons.** Le PPO a consommé **1 486 336 parties** en 2 h, et il
  perd contre le greedy. La valeur v1 en a consommé **40 000**, soit 37 fois moins, et elle
  le bat. La dose de calcul n'a jamais été le problème, contrairement à ce que laisse
  entendre la question récurrente du « budget non désigné ».
- **L'instance à 40 cartes et 4 tours** est très petite : 12 poses par partie. C'est bien
  pour itérer vite, mais tout ce qui est construit doit **passer à l'échelle** vers 90 cartes
  et 10 tours. PIMC y coûtera nettement plus cher par décision (rollouts plus longs, estimation non
  mesurée), alors que l'après-coup reste bon marché. Il faut le mesurer tôt.
- **L'historique ancien** (AlphaZero, CFR, Deep CFR, BC, DAgger, AWR, les logs à la racine).
  CFR vise un équilibre de Nash, et **à 3 joueurs Nash ne garantit rien** sur le fait de
  gagner. L'abandon était justifié. Ces logs encombrent la racine : à ranger dans un dossier
  `historique/`.
- **torch n'est pas dans `pyproject.toml`** : un `uv sync` le retire. Le PPO n'est plus
  reproductible depuis le lock. À ajouter dans un groupe `ia`.

## 4. La prochaine marche — réécrite le 27/09 au soir, après les mesures

> Les pistes pour aller plus loin, détaillées et classées, sont dans
> [PISTES.md](PISTES.md).

Ce qui a été **mesuré** aujourd'hui ordonne les leviers. Dans l'ordre :

1. **Un moteur beaucoup plus rapide — le levier n° 1.** Tout ce qui a marché augmente le
   nombre de parties utiles : TD(λ), 60 000 parties au lieu de 15 000 (+0,076 → +0,169),
   débit doublé. Tout ce qui n'a pas marché (réseau plus gros, recherche courte) bute sur le
   bruit ou sur le coût. Le moteur Python plafonne à environ 55 parties/s sur 11 cœurs.
   **Porter le cœur (règles + tenseur) en Rust derrière pyo3**, ou en code vectorisé, et le
   valider par la suite de conformité existante : le dépôt est déjà conçu pour rejouer
   C1–C18 sur plusieurs moteurs (`COURTISANS_MOTEUR`), et `experiences/test_rapide.py`
   montre comment exiger l'égalité bit à bit. Un facteur 20 à 50 est réaliste : des millions
   de parties par heure, au lieu de 200 000.
2. **Une recherche profonde, une fois le moteur rapide.** La recherche à 1 tour n'apporte
   rien de mesurable (+0,038 NS) ; une recherche **jusqu'à la fin** (PIMC ou ISMCTS avec la
   politique apprise en rollout) coûte trop cher en Python. Avec un moteur rapide, c'est la
   vraie **itération experte** : la recherche joue, le réseau distille la recherche.
3. **Régler TD(λ).** λ = 0,7 a débloqué le plateau ; λ = 0,5 est en cours (`iteration7`).
   À explorer ensuite : λ plus bas, et le retrait des vieilles données Monte-Carlo, qui
   diluent les cibles TD.
4. **Modéliser l'adversaire.** Mesuré : la valeur d'une position dépend fortement de qui
   joue en face (R² de c1b à −0,12 hors de son contexte). Un humain n'est ni un greedy ni
   notre IA. Donner au réseau des indices sur le style des adversaires, observés pendant la
   partie (ce qu'ils ont posé où), est la suite logique.
5. **Inférence sur les Espions.** Les mondes simulés tirent les dos uniformément ; les
   pondérer par la vraisemblance des coups adverses est le gain classique du PIMC au Bridge
   et au Skat. Ne vaut qu'avec la recherche du point 2.
6. **Le juge.** Garder la ligue et le tournoi (`experiences/tournoi.py`) comme juges ;
   remplacer, dans le gardien, le plancher « meilleur niveau atteint », biaisé vers le haut
   (malédiction du gagnant), par une remesure de la courante sur des donnes neuves.

## 5. Suite du 27/09 après-midi : la boucle d'auto-jeu sur le jeu complet

`experiences/iteration.py`, jeu complet (90 cartes, 3 joueurs). À chaque génération :
16 000 parties jouées par la politique courante (5 % de coups aléatoires), apprentissage de
V à partir des poids courants, puis jugement sur des donnes **fixes** : 300 contre 2 greedys,
150 contre 2 × c1b (l'ancre), 150 contre 2 × la politique courante. Suivi lisible :
`uv run python -m experiences.suivi experiences/resultats/iteration3.jsonl`.

Trois versions de la boucle, parce que les deux premières ont échoué, et leurs échecs
**sont** le résultat.

| Version | Ce qui change | Ce qui s'est passé | Journal |
|---|---|---|---|
| v1 | ligue tirée siège par siège (60 % courante, 25 % anciennes, 15 % greedy), fenêtre des 3 dernières générations | **dérive** : gen 1 bat c1b (+0,35) mais recule contre le greedy (+0,169 → +0,118) ; gen 2 **perd** contre gen 1 (−0,053) et tombe à +0,054 contre le greedy. Chaque génération apprenait à exploiter la précédente | `iteration1_derive.jsonl` |
| v2 | toutes les données gardées (plafond 14 M vues, parties greedy comprises), **gardien** : bat la courante et ne recule pas de plus de 0,03 contre le greedy | gen 1 bat c1b (+0,125) mais **perd contre le greedy** (−0,075) ; rejetée | `iteration2_rejet.jsonl` |
| v3 | **un contexte par partie** : 30 % contre 2 greedys, 40 % auto-jeu pur, 30 % contre les anciennes versions | gen 1 acceptée (+0,405 contre c1b, +0,159 contre le greedy), gen 2 acceptée à la limite ; puis, gardien corrigé (`iteration4`), **trois rejets** : plateau | `iteration3.jsonl`, `iteration4.jsonl` |
| v4 | **retours TD(λ = 0,7)** au lieu du gain final seul | **ça repart** : gens 1, 3, 5 acceptées ; contre le greedy +0,148 → +0,220 → +0,247 → **+0,303** | `iteration5.jsonl` |

**La mesure qui explique l'échec de la v2.** Sur les parties entre agents appris, c1b a un R²
de **−0,12** : il y prédit moins bien qu'une constante. La valeur d'une position dépend
fortement de **qui sont les adversaires**. Tirée siège par siège, la ligue ne produisait le
contexte « 2 greedys en face » qu'une partie sur 16, alors que c'est celui du juge. Tirée par
partie, elle le produit trois fois sur dix.

**Le gardien avait lui-même un défaut**, corrigé en cours de route : sa tolérance contre le
greedy se mesurait par rapport à la politique *courante*, donc elle se cumulait d'une
génération à l'autre (+0,169 → +0,159 → +0,148, un cliquet vers le bas). Le plancher est
désormais **le meilleur niveau jamais atteint** moins 0,03, et il faut battre la courante
d'au moins +0,02.

**Ce qui a débloqué : TD(λ).** Le diagnostic du plateau était le bruit de la cible. Une
mesure dédiée le confirme (`experiences/capacite.py`) : trois tailles de réseau plafonnent
au même R² (≈ 0,057) et sur-apprennent dès la 2e époque, **la plus grande faisant pire**.
5,6 M vues ne portent qu'environ 60 000 issues indépendantes, puisque toutes les vues d'une
partie partagent le même gain. Avec TD(λ), la cible d'une vue mélange la valeur prédite de
la vue suivante du même siège et le gain final, comme dans TD-Gammon :
`G_t = (1 − λ) V(v_{t+1}) + λ G_{t+1}`. La variance chute.

| Génération (TD) | Verdict | Contre 2 greedys | Contre 2 courantes | Contre 2 c1b |
|---|---|---|---|---|
| départ (v3 gen 2) | — | +0,148 [+0,090 ; +0,207] | — | — |
| 1 | acceptée | +0,220 [+0,160 ; +0,278] | +0,045 | +0,343 |
| 2 | rejetée | +0,184 | +0,011 | +0,289 |
| 3 | acceptée | +0,247 [+0,191 ; +0,304] | +0,038 | +0,363 |
| 4 | rejetée | +0,241 | +0,007 | +0,358 |
| 5 | **acceptée** | **+0,303 [+0,248 ; +0,362]** | +0,057 | **+0,403 [+0,313 ; +0,485]** |

Les 300 donnes contre le greedy sont les **mêmes** à chaque ligne (5 000 000 à 5 000 299) :
c1b y fait +0,169, et le rejeu de c1b redonne ce chiffre au bit près.

**Deux leviers mesurés, et qui ne marchent pas :**

- **Un réseau plus gros.** Voir ci-dessus.
- **Une recherche courte au moment de jouer**, soit 1 tour d'adversaires simulés par la
  politique apprise dans 4 mondes : +0,038, IC [−0,053 ; +0,133], contre la même valeur sans
  recherche, pour 25 fois plus de calcul. Non établi.

**Le goulot est donc la vitesse du moteur**, qui fixe le nombre de parties par heure.
`experiences/rapide.py` calcule désormais le tenseur en une passe : 48 µs contre 318 µs pour
l'officiel, sous charge, égal bit à bit sur 52 181 états et 4 configurations. La boucle
`iteration6` repart de la gen 5 avec ce moteur et 24 000 parties par génération : environ
55 parties/s, deux fois plus qu'avant.

**`iteration6`** (`iteration6.jsonl`) : gens 3, 5 et 6 acceptées, 1, 2, 4, 7 et 8 rejetées.
Contre le greedy, 0,295 → **0,328** → 0,300, puis plateau vers +0,30.

### 5.1 Le tournoi du 27/09 au soir — le juge qui tranche

`experiences/tournoi.py` : chaque agent contre deux copies de chaque autre, sur les mêmes
120 donnes (5 900 000 à 5 900 119), soit 56 confrontations et 20 160 parties. Brut dans
`experiences/resultats/tournoi_27_09.txt`. Ligne = l'agent, colonne = ses deux adversaires.

| | greedy | c1b | it3/g1 | it5/g3 | it5/g5 | it6/g3 | it6/g5 | it6/g6 | **moyenne** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| greedy | — | +0,140 | −0,061 | −0,084 | −0,108 | −0,156 | −0,094 | −0,099 | −0,066 |
| c1b | +0,172 | — | −0,174 | −0,230 | −0,229 | −0,229 | −0,302 | −0,276 | −0,181 |
| it3/gen_01 | +0,127 | +0,315 | — | −0,060 | −0,035 | −0,076 | −0,194 | −0,160 | −0,012 |
| it5/gen_03 | +0,278 | +0,376 | +0,066 | — | −0,030 | +0,001 | −0,063 | −0,071 | +0,080 |
| it5/gen_05 | +0,251 | +0,380 | +0,024 | +0,051 | — | +0,003 | −0,026 | −0,011 | +0,096 |
| it6/gen_03 | +0,321 | +0,447 | +0,138 | −0,004 | +0,007 | — | −0,026 | −0,014 | +0,124 |
| it6/gen_05 | +0,373 | +0,421 | +0,128 | +0,076 | +0,081 | +0,000 | — | +0,009 | +0,155 |
| **it6/gen_06** | **+0,382** | **+0,474** | +0,188 | +0,053 | +0,033 | +0,024 | +0,019 | — | **+0,168** |

À lire ainsi :

- **Le classement suit l'ordre d'entraînement** : la progression est réelle, pas un tirage
  favorable du gardien. Chaque confrontation directe entre générations proches reste petite
  (+0,02 à +0,08) et ne serait pas établie seule ; c'est la **cohérence de toute la
  matrice** qui porte la conclusion.
- **c1b bat le greedy (+0,172) et finit dernier.** Spécialisé contre le greedy, il perd
  contre tout le reste, y compris quand le greedy l'affronte en double (+0,140 pour le
  greedy). C'est la démonstration qu'un juge unique ne suffit pas.

**La meilleure IA à ce jour : `experiences/modeles/meilleur.pt`** (= `iteration6/gen_06.pt`).
Contre 2 greedys, sur 400 donnes (5 000 000 à 5 000 399), soit 1 200 parties : gain
**+0,289**, IC 99 % [+0,236 ; +0,341]. Elle **gagne seule 48,8 % des parties** ; un greedy
mis à sa place, sur les mêmes donnes, en gagne seul 28,5 %. Écart de score moyen : **+0,56
point** pour elle, −2,39 pour le greedy à sa place.

**`iteration7`** (λ = 0,5, à partir de `meilleur.pt`) : gen 2 acceptée (+0,039 contre
it6/gen_06), gens 1, 3, 4, 5 rejetées. Plateau. Un faux essai au passage : l'arrêt précoce,
jugé sur le gain final alors que l'apprentissage visait des cibles TD, avait rendu les poids
de départ à l'identique (`iteration7_poids_inchanges.jsonl`). Corrigé, et c'est devenu un
contrôle gratuit : la même IA contre elle-même donne +0,018 [−0,029 ; +0,066].

**En cours (lancé le 27/09 à 22 h, 2 h 30, sans surveillance) :** `iteration8`, TD(λ = 0,7) à
partir de `iteration7/gen_02`, **sans les vieilles données Monte-Carlo** : seulement les
18 fichiers qui portent des épisodes, donc des cibles TD. Suivi :
`uv run python -m experiences.suivi experiences/resultats/iteration8.jsonl`.

### 5.2 Les intuitions de l'auteur du jeu, mises à l'épreuve (27/09, soir)

L'auteur voit la bonne stratégie comme **« un greedy, mais stratégique en fin de partie,
selon les cartes qui restent »**. Il pointe aussi les **égalités du greedy**, les
**Espions qui sèment le doute** et les **familles perdues qu'il ne faut pas chercher à
sauver**. Quatre mesures.

**1. Où l'IA s'écarte-t-elle du greedy ?** (`experiences/ressemblance.py`, IA contre
2 greedys, 40 donnes, 1 200 décisions de pose)

| Tours restants | Le greedy a une égalité | L'IA joue un coup optimal pour le greedy | Points immédiats cédés |
|---:|---:|---:|---:|
| 10 (début) | 93 % | 48 % | 0,9 |
| 9 à 4 | 55 à 78 % | 16 à 24 % | 1,5 à 2,6 |
| 3 à 1 (fin) | 53 à 60 % | 38 à 48 % | 1,4 à 1,6 |

L'IA s'écarte le plus en **milieu** de partie, en y sacrifiant environ 2 points immédiats
par tour. En fin de partie, elle se rapproche du greedy : le score immédiat y devient
presque le score final.

**2. Le départage des égalités.** `greedy_departage` est le greedy, dont les seules égalités
sont départagées par le réseau. Écarts **appariés** sur 200 donnes contre 2 greedys
(`experiences/apparie.py`) :

| | Écart | IC 99 % |
|---|---:|---|
| greedy + départage, moins greedy | **+0,188** | [+0,102 ; +0,273] |
| IA complète, moins greedy + départage | **+0,111** | [+0,015 ; +0,205] |
| IA complète, moins greedy | +0,299 | [+0,204 ; +0,394] |

**Environ 60 % de l'avance de l'IA vient du départage des égalités, et 40 % de ses écarts
volontaires.** Les deux sont établis.

**3. Le calcul de fin de partie** (`experiences/fin_de_partie.py`). L'IA apprise joue, puis
sur son dernier tour elle simule chaque coup **jusqu'au bout** dans N mondes compatibles
avec ce qu'elle sait.

| Variante | Adversaires | Gain | IC 99 % |
|---|---|---:|---|
| 1 tour, 16 mondes, simulation par l'IA | 2 greedys | +0,313 (IA seule : +0,272, mêmes donnes) | — |
| 1 tour, 16 mondes, simulation par le greedy | 2 × meilleur | +0,004 | [−0,056 ; …] |
| 1 tour, 16 mondes, simulation par l'IA | 2 × meilleur | +0,050 | [−0,005 ; …] |
| 2 tours, 16 mondes | 2 × meilleur | +0,050 (apparié au précédent : 0,000) | — |
| **1 tour, 32 mondes** | **2 × meilleur** | **+0,088** | **[+0,034 ; …]** |
| 1 tour, 64 mondes | 2 × meilleur | +0,076 (apparié à 32 mondes : −0,013 [−0,049 ; +0,023]) | [+0,021 ; …] |

Le calcul de fin de partie **aide quand il simule correctement les adversaires**. Passer de
16 à 32 mondes aide (apparié : +0,038 [+0,003 ; +0,076]), mais **le gain sature vers 32
mondes**, et l'étendre à deux tours n'apporte rien. Réglage retenu : 1 tour, 32 mondes, soit
quelques secondes par coup, seulement en fin de partie.

**4. Bluffer et semer le doute.** Pas mesuré, mais une conséquence est sûre : **on ne peut
pas bluffer le greedy**, qui compte un dos pour zéro. Le bluff ne peut s'apprendre qu'en
auto-jeu, contre des adversaires qui réagissent aux Espions. C'est une raison de plus de
garder l'auto-jeu dans la ligue.

## 6. Rejouer

Tout est dans `experiences/`, sans rien modifier au moteur ni à `agents/`. torch doit être
dans le venv (`uv pip install torch`, ou mieux, un groupe de dépendances).

```bash
uv run python -m experiences.arene "experiences.pimc:greedy_rollout" --donnes 400
uv run python -m experiences.arene "experiences.pimc:pimc:nb_mondes=8" --donnes 200
uv run python -m experiences.arene "experiences.valeur:agent_ppo_phase3" --donnes 400 --depart 5200000
uv run python -m experiences.donnees --parties 40000 --eps 0.1 --sortie v_greedy.npz
uv run python -m experiences.valeur v1.pt v_greedy.npz --epoques 3
uv run python -m experiences.arene "experiences.valeur:agent_valeur:chemin='v1.pt'" --donnes 400 --depart 5200000
uv run python -m experiences.arene "experiences.valeur:pimc_valeur:chemin='experiences/modeles/v1b.pt',nb_mondes=8" --donnes 200 --depart 5500000
uv run python -m experiences.ciblage_aveugle
uv run python -m experiences.fuite_terminal
uv run python -m experiences.fuite_apres_coup experiences/modeles/v1b.pt
uv run python -m experiences.fuite_apres_coup experiences/modeles/v1b.pt temoin
COURTISANS_INSTANCE=complete uv run python -m experiences.arene "experiences.valeur:agent_valeur:chemin='experiences/modeles/c1.pt'" --donnes 300
```

Les modèles entraînés sont dans `experiences/modeles/` : v1, v1b et v2 pour l'instance
réduite, c1 et c1b pour le jeu complet. Les données (plusieurs Go) ne sont pas gardées ;
elles se régénèrent à l'identique par `experiences.donnees`.

Chaque exécution de l'arène ajoute une ligne à `experiences/resultats/arene.jsonl`.

| Fichier | Contenu |
|---|---|
| `experiences/arene.py` | arène parallèle, sièges permutés, bootstrap par donne |
| `experiences/pimc.py` | détermination aveugle et agent PIMC |
| `experiences/donnees.py` | génération des données de valeur, chaque nœud vu par chaque siège |
| `experiences/valeur.py` | réseau V, entraînement GPU, agent d'après-coup, adaptateur du PPO de la phase 3 |
| `experiences/ciblage_aveugle.py` | la mesure du §3.4 a |
| `experiences/fuite_terminal.py` | le contrôle d'absence de fuite, avec son témoin positif |
| `experiences/fuite_apres_coup.py` | la fuite du ciblage : preuve du correctif et témoin positif |
| `experiences/config.py` | le choix de l'instance : réduite par défaut, `complete` pour le vrai jeu |
