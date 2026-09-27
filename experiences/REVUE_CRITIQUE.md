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

## 4. La prochaine marche

Dans l'ordre. Chaque étape se mesure sur l'arène en quelques minutes.

### 4.1 Tout de suite : l'itération experte (« Expert Iteration » / AlphaZero pour cartes)

C'est la voie éprouvée, et chacun de ses morceaux marche déjà séparément :

```
recherche (PIMC ou ISMCTS)  ──joue──►  parties d'auto-jeu
        ▲                                      │
        │ évaluation des feuilles              │ cibles : gain final
        │ + politique de rollout               ▼   (+ visites de la recherche)
   réseau V(après-coup)  ◄──apprend──  données
```

1. **Dans la recherche, simuler les adversaires par l'agent de valeur, pas par le greedy.**
   C'est la leçon du tableau 2.2 : une recherche qui simule le greedy bat le greedy et fait
   jeu égal avec tout le reste. `experiences.valeur.pimc_valeur` est déjà tronquée à un tour
   et notée par V : il reste à y remplacer `greedy.choisir` par l'agent de valeur, **en
   regroupant les évaluations du réseau par lot** sur tous les mondes. En Python pur, une
   évaluation coûte ~10 ms ; il faudra la vectoriser pour tenir le budget.
2. **Apprendre V sur les parties jouées par la recherche**, et plus sur celles du greedy.
   C'est la boucle d'amélioration : la recherche améliore la politique, et le réseau
   distille la recherche. Juger chaque génération contre la **précédente** et contre le
   greedy, jamais contre le seul greedy.
3. **Ajouter une tête de politique sur les après-coups** : `score(état, action) = f(vue après
   l'action)`, et non 24 logits. Elle sert de prior à ISMCTS (façon PUCT) et remplace le
   greedy en rollout.

### 4.2 Ensuite : ce qui manque pour « digne de ce nom »

- **Inférence sur les Espions.** La détermination tire aujourd'hui les dos **uniformément**.
  Or un joueur pose un Espion là où il l'arrange. Pondérer les mondes par la vraisemblance
  des coups adverses sous le modèle de politique est le gain classique du PIMC au Skat et au
  Bridge.
- **Les données.** v1 a sur-appris dès la 3e époque avec 40 000 parties : les nœuds d'une
  même partie sont corrélés. Il faut plus de parties et moins d'époques. La génération est
  bon marché, environ 150 parties/s en greedy sur 11 cœurs.
- **La symétrie des familles** (dette n° 1). Avec l'après-coup, la canonicalisation devient
  simple : on ne traduit plus aucune action, on permute seulement la vue. C'est une
  augmentation de données gratuite, ×24 à 4 familles.
- **Le jeu complet** (90 cartes, 3 joueurs, 10 tours). L'agent de valeur y gagne déjà
  (§2.3), et les outils le prennent en charge (`COURTISANS_INSTANCE=complete`). Je suggère
  d'y **basculer tôt** : l'instance réduite n'a que 12 poses par partie, alors que le vrai
  jeu, celui où les alliances et les retournements longs existent, en a 30.
- **La vitesse du moteur.** `tenseur()` et `clone()` dominent le coût. Un moteur vectorisé
  (NumPy), ou un portage du cœur en Rust/C++ derrière la même suite de conformité, est ce
  qui permettra des millions de parties. La suite de 1 301 tests (tous verts le 27/09) est précisément ce qui
  rend ce portage sûr.

### 4.3 Et changer le juge, un peu

Garder le gain moyen contre deux greedys comme **plancher**. Y ajouter une **ligue** : PIMC-24,
les versions précédentes, et un classement de type Elo/TrueSkill à 3 joueurs. v2 bat v1
tout en faisant moins bien que v1 contre le greedy : à 3 joueurs, un seul adversaire ne
suffit pas à ordonner les agents.

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
| v3 | **un contexte par partie** : 30 % contre 2 greedys, 40 % auto-jeu pur, 30 % contre les anciennes versions | voir ci-dessous | `iteration3.jsonl` |

**La mesure qui explique l'échec de la v2.** Sur les parties entre agents appris, c1b a un R²
de **−0,12** : il y prédit moins bien qu'une constante. La valeur d'une position dépend
fortement de **qui sont les adversaires**. Tirée siège par siège, la ligue ne produisait le
contexte « 2 greedys en face » qu'une partie sur 16, alors que c'est celui du juge. Tirée par
partie, elle le produit trois fois sur dix.

RESULTATS_ITERATION3

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
