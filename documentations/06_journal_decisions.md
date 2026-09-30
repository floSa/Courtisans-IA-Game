# Journal des décisions

**Une entrée par tour de boucle d'investigation. Antichronologique — le plus récent en haut.**

Format et règles : [05_protocole_experimental.md](05_protocole_experimental.md) §0.

```
[date] Phase X.Y — <titre>
Hypothèse   : énoncé falsifiable, écrit AVANT l'expérience
Instrument  : métrique, seuil chiffré, durée à laquelle elle devient décisive
Résultat    : ce qu'on a mesuré
Audit       : le chiffre mesure-t-il ce qu'on croit ? sur quel support ? comparable ?
Décision    : go / pivot / abandon — avec justification
Impact plan : phases invalidées ou modifiées
```

---

## [2026-09-30] Cycle 2 — Auto-jeu avec la tête de statuts : l'agent progresse-t-il sur ses propres parties ?

*Exploratoire, seuils écrits avant mesure. Suite du cycle 1 : l'agent à statuts égale
`meilleur.pt` en duel (−0,009 [−0,050 ; +0,036]) en n'ayant vu que des parties de greedy.*

**Hypothèse H2.** Réentraîner le réseau à statuts (depuis zéro, 2 époques) sur les données
d'une **ligue** jouée par l'agent lui-même (auto-jeu 35 %, contre greedy 25 %, contre
`meilleur.pt` 20 %, contre la génération précédente 20 %), ajoutées aux parties de greedy,
produit un agent qui **bat l'agent du cycle 1 en duel**, et que la progression se poursuit sur
3 générations.

**Instrument.** `experiences/cycle.py`. 12 000 parties par génération (ε = 0,05), plafond
6 M de vues (les plus anciennes sous-échantillonnées par partie). Jugement, donnes fixes :
contre 2 greedys (450 donnes, 6 000 000+) et en duel contre l'agent du cycle 1 (450 donnes,
6 100 000+). Final : duel contre `meilleur.pt` sur donnes neuves (6 200 000+, 600 donnes).

**Seuils.**

| | Confirmée si | Infirmée si |
|---|---|---|
| H2 | après 3 générations, duel contre l'agent du cycle 1 > 0 avec borne basse IC 99 % > 0, et ≥ +0,40 contre 2 greedys | duel ≤ 0 (borne haute ≤ 0 : régression) ou aucun progrès sur les 3 générations (gains dans le bruit, ±0,05) |

**Résultat.** 3 générations de 12 000 parties de ligue (≈ 5 min par génération, `experiences/resultats/cycle2.jsonl`).
Donnes de jugement fixes ; 1 350 parties par ligne.

| Génération | Contre 2 greedys | Duel contre l'agent du cycle 1 |
|---|---|---|
| (cycle 1, rappel) | +0,377 [+0,330 ; +0,425] | — |
| 1 | +0,277 [+0,228 ; +0,323] | +0,033 [−0,014 ; +0,076] |
| 2 | +0,264 [+0,219 ; +0,308] | +0,021 [−0,019 ; +0,062] |
| 3 | +0,304 [+0,260 ; +0,348] | +0,011 [−0,029 ; +0,051] |

**Décision : H2 INFIRMÉE.** Aucun duel n'a sa borne basse au-dessus de 0, aucune génération
n'atteint +0,40 contre les greedys, et le gain contre les greedys est même **plus bas** que celui
du cycle 1 (plafond de 6 M vues : les parties de greedy sont sous-échantillonnées, et les
données de ligue ne compensent pas). Le réentraînement depuis zéro sur des parties de l'agent
ne fait pas progresser, en 3 générations.

**Ce que ça dit.** Le goulot n'est pas « d'où viennent les parties » (mêmes limites que la
boucle TD : plateau de la valeur autour de R² ≈ 0,09), et nous n'avons pas testé de variante à
gardien ni à TD(λ) ici : la conclusion vaut pour *cette* boucle simple. Hypothèse suivante,
la plus économique : le signal étiqueté manque (le cycle 1 passait de R² 0,079 à 0,091 en
triplant les données), donc plus de parties de greedy, bon marché à générer.

---

## [2026-09-30] Cycle 6 — Augmentation par permutation des familles

*Exploratoire, seuils écrits avant mesure. Motif : le goulot identifié au cycle 3 est le nombre de
parties **distinctes** (le réseau surapprend dès 2-3 époques), et la règle C18 dit que les familles
sont interchangeables. `iteration.py` faisait cette augmentation, `statuts.py` non.*

**Outil.** `statuts.indices_permutation` : permute les familles **directement sur les tenseurs
stockés** (8 blocs sur 18 sont indexés par famille), sans rejouer de partie ; une permutation
aléatoire par échantillon et par lot, sur GPU. Vérifié égal bit à bit au tenseur de l'état dont on
a renommé les familles (`permuter_familles`) : 588 tenseurs du jeu complet, plus un test dans
`tests/experiences/test_statuts.py` (avec témoin positif).

**Hypothèse H6.** À données égales (36 000 parties de greedy), entraîner **avec** augmentation
(6 époques, la perte n'étant plus un surapprentissage à 2) donne un meilleur agent que sans.
Référence : les 3 réseaux « avec statuts » du contrôle des graines, agent statuts ×1 + valeur ×10,
contre 2 greedys sur les donnes 6 400 000+ (450 donnes) : **moyenne +0,359**, écart-type entre
graines 0,015. Test : 3 graines avec augmentation, **mêmes donnes**, mêmes options.

| | Confirmée si | Infirmée si |
|---|---|---|
| H6 | moyenne des 3 graines ≥ +0,03 au-dessus de +0,359 (soit > 2 écarts-types de la moyenne de 3) **et** R² du gain sur le test supérieur à celui du cycle 1 (0,099) | moyenne < +0,379 ou R² du gain ≤ 0,099 |

**Suite conditionnelle (non engagée).** Si confirmée : refaire avec les 108 000 parties.

**Résultat.** *(à venir)*

---

## [2026-09-30] Cycle 5 — Deux réglages gratuits : l'ensemble des graines, le poids de l'écart

*Exploratoire, seuils écrits avant mesure. Travail sur `main` (plus de branche).*

**Hypothèse H5a (ensemble).** Moyenner les sorties des 3 réseaux « avec statuts » du contrôle des
graines (`experiences/modeles/graines/avec_1..3.pt`, 36 000 parties) bat en moyenne un réseau seul.
Mesure : l'ensemble contre 2 greedys et chacun des 3 réseaux seuls, **sur les mêmes donnes neuves**
(450 donnes, 6 500 000+), écart apparié. **Confirmée** si l'ensemble dépasse la moyenne des 3
seuls d'au moins +0,02 avec borne basse de l'écart apparié à 99 % > 0 ; **infirmée** si l'écart
est < +0,01.

**Hypothèse H5b (poids de l'écart).** Le poids `poids_ecart` de la tête d'écart dans le score de
l'agent (0,05 depuis les débuts, hérité de `V`, jamais réglé pour le réseau à statuts) n'est pas
optimal. Balayage {0 ; 0,05 ; 0,2 ; 0,5 ; 1} pour `statuts_s3_e2` (statuts ×1 + valeur ×10),
**exploration sur 6 500 000+, confirmation du meilleur réglage sur 6 600 000+** (450 donnes,
appariée au réglage par défaut). **Retenu** si l'écart apparié de confirmation est ≥ +0,03 avec
borne basse > 0 ; sinon le réglage reste à 0,05.

**Résultat.** Donnes 6 500 000+, 450 donnes (1 350 parties) par ligne ;
`experiences/resultats/cycle5_arene.jsonl`.

| Agent (statuts ×1 + valeur ×10) | Gain contre 2 greedys | IC 99 % |
|---|---:|---|
| graine 1 (36 000 parties) | +0,389 | [+0,343 ; +0,435] |
| graine 2 | +0,355 | [+0,312 ; +0,400] |
| graine 3 | +0,374 | [+0,329 ; +0,416] |
| **ensemble des 3** | **+0,397** | [+0,353 ; +0,439] |
| `statuts_s3_e2`, `poids_ecart` = 0 | +0,456 | [+0,411 ; +0,500] |
| `statuts_s3_e2`, 0,05 (défaut) | +0,458 | [+0,411 ; +0,504] |
| `statuts_s3_e2`, 0,2 | +0,449 | [+0,402 ; +0,497] |
| `statuts_s3_e2`, 0,5 | +0,450 | [+0,405 ; +0,494] |
| `statuts_s3_e2`, 1 | +0,456 | [+0,410 ; +0,502] |

- **H5a : NON TRANCHÉE, tendance positive.** Ensemble moins moyenne des 3 seuls :
  **+0,025 [−0,022 ; +0,071]** (apparié par donne). Le seuil de +0,02 est dépassé par l'estimation,
  mais la borne basse est négative : ni confirmée, ni infirmée (le seuil d'infirmation, < +0,01, n'est
  pas atteint non plus). Par graine : +0,008, +0,042, +0,024. Cohérent avec l'attente
  (+0,02 à +0,04), mais il faudrait ~1 500 donnes pour le trancher.
- **H5b : INFIRMÉE.** Aucun réglage de `poids_ecart` ne se distingue du défaut (écarts appariés
  de −0,009 à −0,002, tous IC à cheval sur 0). L'agent y est insensible : le réglage reste à
  0,05. Le balayage n'a pas été confirmé sur 6 600 000+ puisque aucun candidat n'a franchi l'exploration.
- Contrôle de cohérence : `statuts_s3_e2` fait +0,458 sur les donnes 6 500 000+ contre +0,455 sur
  6 000 000+ (cycle 3) ; les 3 graines de 36 000 parties font +0,373 en moyenne contre +0,359
  sur 6 400 000+ : le bruit de plage de donnes est d'environ ±0,015.

**Décision.** Aucun gain *établi* ici. L'ensemble reste une piste peu coûteuse (+0,025 attendu)
mais il multiplie par 3 le coût de chaque décision ; on ne le retient pas tant qu'il n'est pas
tranché, et il faut de toute façon 3 réseaux entraînés à chaque fois.

**Incident.** Ces mesures ont saturé le processeur de l'auteur (99 %, machine inutilisable). Correctif
le même jour : tous les calculs parallèles utilisent désormais la moitié des cœurs en priorité
minimale (`arene.WORKERS_DEFAUT`, `nice 19` dans chaque processus de calcul), vérifié : 6 processus
à `nice 19`. Noté dans `experiences/README.md` §6.


---

## [2026-09-30] Ménage du dépôt — une seule branche, rien de perdu

**Décision de l'auteur :** « je veux un `main` avec tout documenté, pas de branche à la fin ».

**Fait.**
1. Worktree `Courtisans_pilote` supprimé (instantané de `main` du 24/08, lien `.git` cassé depuis
   le renommage du dépôt ; état propre, contenu déjà dans `main`).
2. Sauvegarde complète des fichiers non suivis (checkpoints des itérations 1 à 8, journaux,
   réseaux du contrôle des graines) : commit `0c180e3`.
3. **8 tags d'archive** posés et poussés avant toute suppression : `archive/main-24-08`,
   `archive/phase-4-tete-de-valeur`, `archive/audit-phase-3` (+ `-tour-2`, `-tour-3`),
   `archive/phase-3-premier-agent`, `archive/cfr-pivot`, `archive/old_version`.
4. `reprise-iteration-experte` fusionnée dans `main` (fusion sans conflit ; les prompts 21 et 22,
   qui n'existaient que sur `main`, sont conservés). 1 308 tests verts après la fusion, 1 312 avec
   les 4 tests ajoutés pour `statuts.py` (aveuglement au ciblage avec témoin, statuts certains =
   décompte du tenseur, données bien formées, parties légales).
5. Documentation remise à jour : `experiences/README.md` (nouveau : état, carte, commandes,
   plages de donnes, lecture des chiffres, pièges), `documentations/10_sources.md` (nouveau :
   veille bibliographique, niveau de lecture de chaque source), `09_reprise.md` §0,
   bandeau de `00_index.md`, `PILOTE.md`, `README.md`.
6. Branches locales et distantes supprimées après la fusion et le push de `main`.

**Ce qui reste hors Git, volontairement** : `experiences/donnees/` (~14 Go, régénérable :
commandes dans `experiences/README.md` §3), et les dossiers ignorés de l'ancienne campagne
(`cfr/`, `models/`, `historique_ancien/`), conservés sur disque.

---

## [2026-09-30] Contrôle de robustesse — la variation d'un entraînement à l'autre

*Question de l'auteur : les runs sont-ils assez longs pour que les résultats soient significatifs ?
Constat préalable : tous les IC 99 % affichés mesurent le hasard des **parties** ; aucun ne
mesurait celui de l'**entraînement** (un seul réseau par variante, aucune graine répétée).*

**Hypothèse.** L'effet de la tête de statuts (cycle 1 : +0,178 → +0,288) dépasse la variation
d'un entraînement à l'autre. Infirmée si l'écart entre variantes est du même ordre que l'écart-type
entre graines.

**Instrument.** 3 graines × {avec tête de statuts, sans}, 36 000 parties, 2 époques, chaque réseau
joué contre 2 greedys sur 450 donnes neuves (6 400 000+).

| Variante | Graine 1 | Graine 2 | Graine 3 | Moyenne | Écart-type entre graines |
|---|---:|---:|---:|---:|---:|
| sans statuts, valeur seule | +0,180 | +0,176 | +0,156 | +0,171 | 0,013 |
| avec statuts, valeur seule | +0,312 | +0,296 | +0,284 | +0,297 | 0,014 |
| avec statuts, statuts ×1 + valeur ×10 | +0,365 | +0,371 | +0,342 | +0,359 | 0,015 |

**Résultat : confirmé.** L'écart avec / sans statuts (+0,126) fait environ 9 écarts-types entre
graines ; aucune des trois graines « sans » n'atteint la plus basse des « avec ». Le mélange
(+0,359) tient aussi sur trois graines. **La découverte du cycle 1 est réelle, et non un tirage
favorable.**

**Ce que cela fixe pour lire tous les cycles.** L'incertitude de l'entraînement est d'environ
**±0,015** (1 écart-type, donc ≈ ±0,03 à 2 écarts-types) contre 2 greedys. Elle s'ajoute à celle
des parties (IC 99 % de ±0,04 à 450 donnes). Conséquences : (a) les différences de 0,02-0,04
entre deux réseaux entraînés une fois (cycle 3 contre cycle 1 en duel : +0,037 ; cycle 4
contre `meilleur.pt` : +0,046) **ne sont pas établies** ; (b) les écarts de 0,1 et plus (aide de
la tête de statuts, fin de partie contre le réseau seul : +0,099, mesure sur un même réseau donc
sans variation d'entraînement) **le sont**.

**Limites connues du protocole.** Un seul jeu de données par taille ; réglages de pondération
choisis sur des donnes d'exploration, puis confirmés sur des donnes neuves mais **les plages
6 000 000-6 300 000 ont resservi d'un cycle à l'autre** ; la variation d'entraînement n'est
mesurée que pour le cycle 1 (36 000 parties), pas pour les cycles 3 et 4 ; les adversaires
(greedy, `meilleur.pt`) ne sont pas un humain.

**Décision.** Protocole conservé, avec trois règles à partir de maintenant : (1) tout écart
annoncé en dessous de 0,05 est étiqueté « non établi » tant qu'il n'est pas répliqué sur au
moins 3 graines ; (2) la conclusion « bat `meilleur.pt` » attend ce contrôle sur le cycle 4 ;
(3) donnes de confirmation neuves à chaque conclusion.

---

## [2026-09-30] Cycle 4 — Le calcul de fin de partie sur le réseau à statuts

*Exploratoire, seuils écrits avant mesure. Le plateau du cycle 3 (égalité avec `meilleur.pt`
en duel, quels que soient la source et le nombre de parties) suggère qu'il faut de la
recherche, pas de la donnée. La fin de partie donnait +0,088 [+0,034 ; …] sur `meilleur.pt`.*

**Hypothèse H4.** L'agent hybride (`experiences/fin_de_partie.py`, désormais avec
`statuts=True`) : réseau `statuts_s3_e2` (statuts ×1 + valeur ×10) tant qu'il reste plus d'un
tour, puis simulation jusqu'au bout de chaque coup dans 32 mondes tirés à l'aveugle,
adversaires simulés par le même réseau (`rollout='valeur'`). Il **bat le réseau seul** en duel
d'au moins +0,05, et **bat `meilleur.pt`**.

**Instrument.** Arène habituelle, donnes neuves : duel hybride contre 2 × `statuts_s3_e2`
(450 donnes, 6 300 000+) ; duel contre 2 × `meilleur.pt` (450 donnes, 6 200 000+, à comparer au
−0,009 du réseau seul sur les mêmes donnes) ; contre 2 greedys (300 donnes, 6 000 000+).

| | Confirmée si | Infirmée si |
|---|---|---|
| H4 | duel contre le réseau seul ≥ +0,05, borne basse IC 99 % > 0 ; et duel contre `meilleur.pt` avec borne basse > 0 | duel contre le réseau seul ≤ +0,02 |

**Résultat.** Hybride = `statuts_s3_e2` + fin de partie (1 tour, 32 mondes, adversaires simulés par
le réseau). ~20 s par donne de 3 parties sur 11 processus ; `experiences/resultats/cycle4_arene.jsonl`.

| Adversaires | Donnes | Gain de l'hybride | IC 99 % | Victoires seules |
|---|---|---:|---|---:|
| 2 × `statuts_s3_e2` (le réseau seul) | 6 300 000+, 450 | **+0,099** | [+0,064 ; +0,135] | 35,0 % |
| 2 × `meilleur.pt` | 6 200 000+, 450 | **+0,046** | [+0,001 ; +0,093] | 32,1 % |
| 2 greedys | 6 000 000+, 300 | **+0,470** | [+0,420 ; +0,518] | 60,8 % |

Rappel : le réseau seul faisait −0,009 [−0,049 ; +0,030] contre `meilleur.pt` (mêmes donnes) et
+0,455 contre les greedys (donnes 6 000 000+, 600 donnes).

**Décision : H4 CONFIRMÉE, avec une réserve.** Contre le réseau seul, +0,099 est près du double du
seuil (+0,05), borne basse nettement positive. Contre `meilleur.pt`, la borne basse est positive
mais à +0,001 : le seuil est franchi à la limite, sur 450 donnes ; il faut un rejeu plus
large pour parler de « bat `meilleur.pt` » sans réserve. Le gain de la fin de partie est
plus fort ici (+0,099) que sur `meilleur.pt` (+0,088) alors que l'adversaire est plus fort.

**L'agent jouable à ce jour** : `experiences.fin_de_partie:fin_de_partie` avec
`chemin='experiences/modeles/statuts_s3_e2.pt', statuts=True, tours_fin=1, nb_mondes=32,
rollout='valeur'`. Quelques secondes par coup, uniquement au dernier tour.

**Impact plan.** Piste n° 1 (statuts) et n° 3 (agent jouable) de PISTES.md : faites. La suite
qui a du sens, dans l'ordre : (a) rejouer le duel contre `meilleur.pt` sur plus de donnes ;
(b) la fin de partie *dans l'entraînement* (n° 2), qui coûte trop cher en Python ; (c) le moteur
rapide (n° 4), toujours en attente d'accord, qui débloque (b) et la recherche profonde.


---

## [2026-09-30] Cycle 3 — Plus de données étiquetées : trois fois plus de parties de greedy

*Exploratoire, seuils écrits avant mesure.*

**Hypothèse H3.** Le réseau à statuts entraîné sur **108 000** parties de greedy (36 000 existantes
+ 72 000 nouvelles, donnes 9 500 000+), au lieu de 36 000, donne un agent meilleur : le
R² du gain sur le test monte au-dessus de 0,10 et l'agent bat l'agent du cycle 1 en duel.

**Instrument.** Même réseau, mêmes pondérations (statuts ×1, valeur ×10). Époques : 2 puis 3,
avec suivi du test. Jugement : duel contre l'agent du cycle 1 (600 donnes, 6 100 000+) et
contre 2 greedys (600 donnes, 6 000 000+).

| | Confirmée si | Infirmée si |
|---|---|---|
| H3 | duel ≥ +0,04 avec borne basse IC 99 % > 0, et R² du gain test ≥ 0,10 | duel ≤ +0,02 : les données ne sont plus le facteur limitant |

**Résultat.** 108 000 parties de greedy, 15,9 M de vues. Le surapprentissage revient dès la
3ᵉ époque (R² du gain sur le test : 0,110, 0,106, 0,092) ; on garde 1 et 2 époques
(`statuts_s3_e1.pt`, `statuts_s3_e2.pt`). Sur le **même** test (fin de `greedy_b2`, jamais vu par
les trois modèles) :

| Modèle | R² du gain | R² de la tête d'écart | Précision du statut |
|---|---:|---:|---:|
| cycle 1 (36 000 parties, 2 époques) | 0,099 | 0,136 | 0,567 |
| cycle 3, 1 époque | 0,116 | 0,158 | 0,573 |
| cycle 3, 2 époques | 0,114 | 0,159 | 0,573 |

Jeu (statuts ×1, valeur ×10, 600 donnes = 1 800 parties par ligne) :

| Modèle | Contre 2 greedys | Duel contre l'agent du cycle 1 | Duel contre 2 × `meilleur.pt` |
|---|---|---|---|
| cycle 1 (rappel, donnes 6 000 000+ / 450 donnes) | +0,377 [+0,330 ; +0,425] | — | −0,009 [−0,050 ; +0,036] |
| cycle 3, 1 époque | **+0,440** [+0,401 ; +0,480] | +0,037 [+0,000 ; +0,075] | — |
| cycle 3, 2 époques | **+0,455** [+0,417 ; +0,493] | +0,034 [−0,004 ; +0,071] | −0,009 [−0,049 ; +0,030] |

**Décision : H3 NON TRANCHÉE, tendance positive.** Le seuil de R² (≥ 0,10) est atteint ; le seuil
du duel (≥ +0,04, borne basse > 0) ne l'est pas strictement (+0,037 avec borne basse à 0,000 ;
+0,034 avec −0,004), sans tomber dans la zone d'infirmation (≤ +0,02). Les données aident : de
+0,377 à +0,44/+0,455 contre les greedys, la meilleure mesure obtenue contre lui à ce jour.

**Point d'attention : non-transitivité.** Contre `meilleur.pt`, le résultat est identique au cycle 1
(−0,009), alors que le gain contre les greedys a grimpé de 0,08. Battre mieux le greedy n'est pas
battre mieux `meilleur.pt` : les deux adversaires ne sont pas interchangeables, et les deux
mesures sont à suivre à chaque cycle. Il y a un plateau commun, autour de l'égalité avec
`meilleur.pt`, que ni la source des parties (cycle 2) ni leur nombre (cycle 3) ne fait bouger.

**Impact plan.** L'agent `statuts_s3_e2` devient la référence contre le greedy. Pour dépasser
`meilleur.pt` en duel, il faut autre chose que de la donnée : le calcul de fin de partie
(+0,088 mesuré sur `meilleur.pt`, jamais essayé sur ce réseau), puis la recherche.


---

## [2026-09-30] Cycle 1 — Le greedy probabiliste : prédire le statut final des familles

*Régime exploratoire (`experiences/`), seuils écrits avant toute mesure. Origine : piste n° 1 de
[PISTES.md](../experiences/PISTES.md). Ménage préalable : le worktree `Courtisans_pilote`
(instantané de `main` au 24/08, lien `.git` cassé depuis le renommage du dépôt) est supprimé ;
`main` est intact.*

**Hypothèses.**

- **H1a (prévisibilité).** Le statut final d'une famille se prédit *mieux* que « le statut actuel
  restera », dès qu'il reste au moins 4 tours à jouer. Mesure : précision du statut sur des
  parties de test jamais vues, par tour restant.
- **H1b (le signal est moins bruité).** L'écart de score final se reconstruit à partir des
  statuts prédits (par calcul) avec un R² **supérieur** à celui d'une tête « écart » apprise
  directement sur les mêmes données (R² du gain de V : 0,05 à 0,09).
- **H1c (jouer).** L'agent qui note chaque action par l'écart espéré via les statuts prédits bat
  2 greedys. C'est le test décisif.

**Instrument.** `experiences/statuts.py`. Données : parties du jeu complet (90 cartes),
greedy avec ε = 0,1, donnes 9 000 000+ (disjointes de l'arène et de `donnees.py`). Test :
8 % de parties de fin de fichier, coupe sur une frontière de partie. Témoin : même réseau
entraîné sans la tête de statuts. Arène habituelle (900 parties, donnes 5 000 000+).

**Seuils (fixés avant de mesurer).**

| | Confirmée si | Infirmée si |
|---|---|---|
| H1a | précision réseau ≥ précision « statut actuel » + 2 points pour 4 à 6 tours restants | écart < 1 point pour 4 à 6 tours restants |
| H1b | R² via statuts ≥ R² tête écart + 0,05 sur le test entier | inférieur ou égal |
| H1c | gain contre 2 greedys, borne basse de l'IC 99 % > 0 : « ça marche » ; > +0,289 (`meilleur.pt`) : « ça remplace » | borne basse ≤ 0 |

**Ce qu'on ne saura pas d'emblée.** Le test H1c se fait avec des données de greedy (hors
distribution d'un agent appris) : un échec de H1c seul n'infirme pas l'idée, il dirait que
les données ne suffisent pas. La suite logique, si H1a/H1b tiennent : la tête de statuts
comme cible auxiliaire dans `iteration.py`.

**Résultat.** Données : 36 000 parties de greedy (ε = 0,1), 5,3 M de vues ; test = parties de fin
de fichier, jamais vues. Détail : `experiences/resultats/cycle1_prevision.txt`,
`cycle1_confirmation.jsonl`, `arene.jsonl`.

*Incident d'entraînement, à retenir.* Avec 12 000 parties et 6 époques, tout est en surapprentissage
(R² du gain négatif, y compris pour le témoin) : le premier verdict de H1b (−0,107) ne
mesurait pas l'idée. Le suivi du test par époque (ajouté à `entrainer`) montre l'optimum à
1-2 époques ; les chiffres ci-dessous sont à 36 000 parties, 2 époques.

- **H1a : CONFIRMÉE.** Précision du statut final, réseau contre « le statut actuel restera » :
  4 tours restants 0,581 vs 0,535 ; 5 tours 0,563 vs 0,515 ; 6 tours 0,541 vs 0,486, soit +4,6 à
  +5,5 points (seuil : 2). Sur tout le test : 0,569 vs 0,504, perte de log 0,894 (constante :
  1,060). Dès le début de partie (10 tours restants) : 0,439 vs 0,251.
- **H1b : INFIRMÉE telle qu'énoncée.** R² de l'écart final via les statuts : −0,077, contre 0,135
  pour la tête d'écart apprise directement. Le calcul améliore pourtant nettement le
  décompte du greedy (−0,558), et cet écart n'est pas absurde : la formule ignore les cartes qui
  seront encore posées dans les domaines. Le R² absolu n'est pas ce qui compte pour un agent qui
  classe des actions ; c'est H1c qui tranche. (Seuil non modifié après coup : H1b reste infirmée.)
- **H1c : CONFIRMÉE au sens « ça marche », et au-delà.** Contre 2 greedys, 900 parties, donnes
  5 000 000+ :

| Agent | Gain | IC 99 % |
|---|---:|---|
| statuts seuls | +0,148 | [+0,092 ; +0,205] |
| témoin (réseau sans tête de statuts, valeur seule) | +0,178 | [+0,124 ; +0,233] |
| réseau à statuts, valeur seule (têtes de gain et d'écart) | +0,288 | [+0,232 ; +0,343] |
| **statuts ×1 + valeur ×10** | **+0,381** | [+0,321 ; +0,442] |
| `meilleur.pt` | +0,300 | [+0,241 ; +0,360] |

  **Découverte principale, non prévue par les hypothèses :** la tête de statuts, utilisée
  seulement pendant l'entraînement, fait passer la valeur seule de +0,178 à +0,288 (mêmes
  données, mêmes époques, IC presque disjoints). C'est la cible dense (6 étiquettes par vue au
  lieu d'une) qui régularise, et non seulement le calcul du greedy probabiliste.
  Le mélange (pondérations 10 puis 30, 100, 0,3/10, 0,1/10 : de +0,33 à +0,38) est un plateau.

- **Confirmation sur donnes neuves** (6 000 000+, 450 donnes, réglage gelé : statuts ×1, valeur
  ×10) : agent +0,377 [+0,330 ; +0,425] contre `meilleur.pt` +0,321 [+0,272 ; +0,371] ;
  écart apparié +0,056 [−0,009 ; +0,120] (non significatif). **Duel direct contre 2 × `meilleur.pt`
  (donnes 6 100 000+) : −0,009 [−0,050 ; +0,036] : égalité.**

**Audit.** Le réglage a été choisi sur les donnes d'exploration (biaisé vers le haut : +0,381) ;
la confirmation neuve (+0,377) le tient. Pas de fuite : l'agent note la vue d'après-coup du
siège qui décide, avec mondes tirés à l'aveugle au ciblage (comme `agent_valeur`) ; les valeurs
de domaine viennent de `vue_domaines`, qui ignore les dos adverses. Limite : un seul réseau, une
seule graine ; 5 configurations de pondération essayées (comparaisons multiples, d'où la
confirmation).

**Décision.** **Go.** L'idée « statuts finaux » vaut par la cible auxiliaire plus que par le
calcul. Un réseau entraîné en quelques minutes sur des parties de greedy égale `meilleur.pt`
(des heures de TD(λ)). Il n'est pas encore meilleur en duel.

**Impact plan.** Piste n° 1 de PISTES.md : faite, à cocher. Cycle 2 : les données jouées par ces
agents (et non par le greedy), boucle d'amélioration avec la tête de statuts.

---

## [2026-09-27] Reprise — revue critique, et changement de méthode : chercher, puis apprendre

**Statut, en premier parce qu'il conditionne la lecture.** Cette entrée rend compte d'une
séance **exploratoire** : rien n'y a été pré-inscrit ni audité par une conversation distincte.
Les chiffres sont mesurés sur une arène calibrée, se rejouent par une commande, et chaque
contrôle d'aveuglement porte son témoin positif. Mais aucun ne vaut verdict au sens du §0 du
protocole. Détail, commandes et limites : [experiences/REVUE_CRITIQUE.md](../experiences/REVUE_CRITIQUE.md).

**Hypothèse (a posteriori, et dite telle).** L'agent de la phase 3 n'est pas battu parce que
son critique est imprécis, mais parce que (1) sa tête d'action ne peut pas représenter une
partie des décisions, et (2) un apprentissage sans modèle, sur un gain ±1 épars, se prive du
simulateur parfait et de l'information majoritairement publique qui font la force du greedy.

**Instrument.** `experiences/arene.py` : gain moyen contre deux adversaires, sièges permutés,
IC 99 % bootstrap par donne, donnes 5 000 000+, données d'apprentissage 8 000 000+. Contrôle du
niveau nul : greedy contre greedy, +0,007, IC [−0,032 ; +0,046]. Concordance avec le dépôt : le
PPO de la phase 3 y rend −0,185, IC [−0,226 ; −0,144], contre −0,164 publié.

**Résultat.**

- **Le ciblage de l'Assassin est aveugle dans le tenseur.** Sur 14 368 nœuds de ciblage en jeu
  greedy, 9 246 (64 %) offrent au moins deux cibles d'identités différentes, et dans 100 % de
  ces cas, inverser l'ordre d'arrivée des cartes change la carte désignée par chaque indice
  sans changer le tenseur d'un bit. La dette n° 2 du README (« l'encodage par cible n'est pas
  écrit ») n'était pas une dette de confort : le réseau de la phase 3 choisissait sa victime
  sans la connaître. Un test de caractérisation le tient désormais
  (`tests/experiences/test_experiences.py`).
- **Une recherche sans aucun apprentissage bat le greedy.** PIMC (mondes tirés à l'aveugle,
  rollouts greedy) : +0,129 avec 8 mondes, +0,194 avec 24, instance réduite.
- **Une valeur de précision médiocre bat le greedy, si l'on note des conséquences et non des
  indices.** L'agent « d'après-coup » clone l'état, joue chaque action légale et note la vue
  qui en résulte par un réseau V. R² ≈ 0,18 — l'ordre de grandeur du critique jugé « mauvais »
  en phase 3 —, et il gagne +0,149, IC [+0,105 ; +0,194], instance réduite, après 12 min de
  données greedy et 1 min de GPU. **Sur le jeu complet à 90 cartes : +0,169, IC
  [+0,112 ; +0,227]**, 60 000 parties greedy. Le PPO avait consommé 1 486 336 parties.
- **Une recherche qui simule le greedy exploite le greedy.** Contre deux agents de valeur,
  PIMC fait −0,018 et recherche + valeur +0,013 : leur avance contre le greedy tenait en bonne
  partie à un modèle d'adversaire exact.
- **Non-transitivité.** v2, entraînée sur l'auto-jeu de v1, bat deux v1 (+0,114, IC
  [+0,071 ; +0,160]) et recule contre le greedy (+0,095 contre +0,120).

**Audit (interne, et un défaut trouvé dans le livrable même).** La première version de l'agent
d'après-coup **trichait au ciblage** : jouer « tuer le dos n° i » sur l'état réel révèle la
victime, la défausse étant publique. Correctif : noter chaque ciblage en moyenne sur des mondes
re-tirés à l'aveugle. 0 décision sur 2 988 ne dépend plus de l'identité réelle des dos ; le
témoin, l'ancienne version, en dépendait 514 fois. Les chiffres publiés sont ceux de la version
corrigée, et l'écart était faible (v1 : +0,128 → +0,120). **Un agent qui simule le futur sur
l'état réel est une porte que la preuve d'aveuglement du greedy ne couvrait pas** : elle
vérifie ce que l'agent *lit*, pas ce qu'il *simule*.

**Ce qui revient sur une conclusion antérieure.** L'entrée de la phase 3 écrivait « la valeur
n'est pas imprédictible dans ce jeu : **le critique est mauvais** », sur un plancher de 0,57
calculé sur l'état complet. La phase 4 a réfuté le remède sans l'entraîner, ce qui est à son
crédit. Mais le diagnostic lui-même était de trop : **à λ = 1, le critique ne sert qu'à réduire
la variance de l'avantage, dans la proportion de son R²**, et la mesure du 27/09 montre qu'une
valeur de même précision suffit à gagner quand elle sert à choisir.

**Décision. PIVOT D'ALGORITHME.** La ligne « PPO à tête d'indices d'action » est **abandonnée,
pas itérée** — l'itération 2 de la phase 4, tête auxiliaire, n'est pas lancée. La suite est
l'**itération experte** : une valeur d'après-coup apprise en auto-jeu contre une ligue, puis
une recherche qui simule ses adversaires par la politique apprise, distillée à son tour.
Le **jeu complet** devient l'instance de travail : la méthode y marche, et l'instance réduite
n'a que 12 poses par partie.

**Impact plan.**

1. Deux régimes : **exploratoire** (arène figée, essais en minutes, `experiences/`) et
   **confirmatoire** (pré-inscription et audit croisé), réservé à ce qu'on veut affirmer.
2. Le juge devient une **ligue** — greedy, ancre `c1b`, générations précédentes — et plus le
   seul greedy.
3. `torch` et `numpy` sont déclarés (groupe `ia` de `pyproject.toml`) : le PPO de la phase 3
   n'était plus reproductible depuis le lock.
4. `experiences/rapide.py` : tenseur 2,5× plus rapide, **égal bit à bit** à `infoset.tenseur`
   (52 181 comparaisons, quatre configurations). Le moteur reste la référence ; un portage plus
   rapide se ferait sous la même suite de conformité.

**Enseignements de méthode.**

- **Un défaut annoncé comme dette doit être confronté au livrable qui la traverse.** La dette
  n° 2 était écrite au README ; la phase 3 a entraîné sur elle.
- **Un juge unique exploitable se fait exploiter.** Toute recherche qui simule le greedy
  « bat » le greedy. Le contrôle est de la juger contre un adversaire qu'elle ne simule pas.
- **Avant de réparer un organe, calculer ce qu'il peut rapporter au mieux.** Le gain maximal
  d'un meilleur critique à λ = 1 se bornait sur papier.

**Addendum du soir — la boucle d'auto-jeu, jeu complet.** Détail : §5 de la revue.

- **Deux échecs, chacun mesuré et corrigé.** v1 dérive : chaque génération exploite la
  précédente (gen 2 perd contre gen 1, −0,053). v2 perd contre le greedy (−0,075), parce que la
  valeur dépend des adversaires (c1b : R² = −0,12 sur les parties entre agents appris) et que
  la ligue, tirée siège par siège, ne produisait « 2 greedys en face » qu'une partie sur 16.
  Correctif : **un contexte par partie**.
- **Le gardien avait deux défauts**, un cliquet (tolérance cumulée) puis une malédiction du
  gagnant (plancher = maximum de mesures bruitées). Le premier est corrigé, le second
  documenté.
- **Plateau en Monte-Carlo ; TD(λ = 0,7) le débloque.** Contre 2 greedys : +0,148 → +0,220 →
  +0,247 → +0,303 → +0,328. Un réseau plus gros n'aide pas (trois tailles plafonnent à
  R² ≈ 0,057), une recherche à un tour non plus (+0,038, IC [−0,053 ; +0,133]). **La limite
  est le bruit de la cible et le nombre de parties** ; le tenseur en une passe, égal bit à
  bit à l'officiel, double le débit.
- **Tournoi à 8, 20 160 parties : classement monotone avec l'entraînement.** La meilleure,
  `experiences/modeles/meilleur.pt` : +0,289 IC 99 % [+0,236 ; +0,341] contre 2 greedys,
  48,8 % de victoires seules (greedy à sa place : 28,5 %).

**Enseignement.** À trois joueurs, **la distribution des adversaires pendant l'apprentissage
est un hyperparamètre de premier ordre**, au même titre que l'algorithme : elle a fait passer
la même boucle d'une perte à un gain contre le greedy.

---

## [2026-08-24] Phase 4, itération 1 — La tête de valeur : hypothèse réfutée avant l'entraînement

**Hypothèse.** *Pré-inscrite dans `prompts/18_phase4_iteration_1.md`, avant tout code.* Le
critique de la phase 3 n'apprend pas — `perte_valeur` 0,3923 → 0,3908, `R² = +0,093` quand
**0,57** est calculé comme atteignable — et **ce n'est pas la faute du jeu** : à l'avant-dernière
décision le plancher irréductible vaut 0,0075 pendant que le critique fait 0,30, un facteur
quarante. Donc : **le critique est mal spécifié ou sous-entraîné, et le réparer est un levier**.

**Instrument.** Le seuil qui devait décider n'était pas le R² : c'était le gain moyen contre
**deux copies de l'agent de la phase 3**, sièges permutés, borne basse de l'IC 99 % bootstrap par
donne strictement positive. Le R² n'était qu'un seuil **intermédiaire, diagnostique**, et
`prompts/21` §1 l'a formulé comme un **écart apparié** contre le critique de la phase 3 sur le
même échantillon hors plage — jamais comme un niveau. Le piège était écrit dès la première ligne
du prompt : **on peut faire monter le R² sans que l'agent joue mieux.**

**Résultat. L'hypothèse est RÉFUTÉE, et elle l'est sans qu'un seul entraînement ait été lancé.**

- **Le critique de la phase 3 est à ~0,02 du plafond de ce qu'un observateur aveugle atteint dans
  ce jeu.** Un régresseur supervisé ordinaire, ajusté hors ligne sur `(info-set, retour)` avec
  accès libre aux mêmes données, ne le dépasse que de **+0,0205**.
- **Le critique, +0,1012** — sur le jeu de test **fixe** : 76 799 nœuds issus de 4 000 parties de
  self-play à trois copies de `models/phase3/final.pt` (SHA-256 `772a869f…f0217`), **hors plage
  d'entraînement**, seeds 7 400 000+. Mesuré aussi à +0,1008 sur 76 842 nœuds, seeds 7 000 000+,
  et +0,1033 sur un troisième bloc.
- **Le plafond, +0,1217** — même test fixe, régresseur à deux couches cachées de largeur 128,
  ajusté sur **1 536 135 nœuds** (80 000 parties, seeds 7 000 000+). **L'arrêt précoce est choisi
  SUR LE JEU DE TEST : c'est une borne haute optimiste**, délibérément, parce qu'une borne haute
  optimiste qui reste basse est un résultat plus fort qu'une mesure honnête qui reste basse.
- **La pente : +0,0079 de R² par DOUBLEMENT des données**, stable sur trois intervalles — +0,0082
  (76 842 → 307 273 nœuds), +0,0081 (→ 767 906), +0,0075 (→ 1 536 135).
- **Conséquence chiffrée : atteindre 0,545 demanderait 53 doublements, soit 1,8 × 10²² nœuds.**
  **Ce n'est pas une prédiction, c'est une réduction à l'absurde** — elle établit que 0,545 n'est
  pas une question de volume, pas que le nombre 53 signifie quoi que ce soit.

**Et voici ce que tout ce résultat porte, en toutes lettres. Le plancher de 0,545 est calculé sur
l'état COMPLET. L'écart entre +0,12 et 0,545 n'est ni un manque de données, ni un défaut de
modèle, ni une tête de valeur mal faite : c'est ce que le jeu CACHE à un joueur honnête.** Le
prompt de la phase l'avait écrit d'avance — « un critique qui voit l'état complet n'est pas
utilisable à l'inférence, et le plancher de 0,57 est calculé sur l'état complet précisément pour
cette raison ». La mesure lui donne raison et chiffre l'écart.

**Ce que la mesure INFIRME.** Le soupçon « la tête de valeur manque de capacité » est **faux dans
le sens attendu : plus de capacité EMPIRE la généralisation.** Largeur 256 sur 76 818 nœuds
descend à **−0,9161** en test pendant que son R² d'apprentissage monte à +0,4630. Chez le pilote,
qui a réimplémenté indépendamment, la largeur 128 fait moins bien que la largeur 32 **aux trois
volumes**. Le critique ne sous-ajuste pas : il est au bord du sur-ajustement.

**Ce qui garde son diagnostic et perd son remède.** Le soupçon « la cible terminale vue depuis
n'importe quelle profondeur » reste juste sur le constat — le critique est presque nul tôt,
`R² = +0,0086` au rang 0. Mais **les nœuds tardifs, ceux du facteur quarante, pèsent 8,2 % de la
perte** (76 842 nœuds, seeds 7 000 000+), et la marge `MSE − plancher` pondérée par la population
est **répartie** : les rangs 0–3 en portent 53 %. **Pondérer la perte vers la profondeur viserait
8 % du problème.** Au passage, la pondération évidente par `1/plancher` donne **93 % de la masse**
au rang 8, qui est mesuré sur **un seul état**.

**Corroboration indépendante du 0,57.** Le plancher par rang, mesuré à la méthode de l'auditeur —
300 états × 24 replicats, 7 200 parties — recombiné avec la population donne
`E[plancher] = 0,193` pour `Var(R) = 0,4239`, soit **0,545 atteignable**. L'auditeur publiait
**0,57** par une autre méthode et un autre découpage.

**Audit. Le pilote a refait la mesure avec sa propre implémentation, et elle tient.** Régresseur,
séparation des seeds, arrêt précoce et R² écrits par lui sans lire `mesure/phase4.py` ; seeds
d'apprentissage 500 000+, de test 900 000+, disjoints et tous deux hors plage. Critique à
**+0,0958** chez lui contre +0,1012 chez moi ; pente **+0,0078 à +0,0091** contre +0,0079 ; et
**extrapolée depuis son point à 461 k nœuds, sa pente prédit +0,121 à 1,54 M quand ma mesure
donne +0,1217**. Deux implémentations indépendantes sur la même courbe, à la troisième décimale.

**L'audit croisé de la phase 4 — conversation n° 9 — reste à faire, et son travail sera de refaire
ce plafond sans lire une ligne de `mesure/phase4.py`.** Un résultat qui **ferme une direction**
mérite d'être établi deux fois.

**Décision. L'ITÉRATION 1 EST CLOSE SUR LE CONSTAT. Le run de 2 h ne se lance pas.** Le
raisonnement, pour qu'il soit auditable : le seuil intermédiaire **est franchissable**, la marge
existe et vaut ~+0,02 ; mais **le seuil intermédiaire ne décide rien**, et rien n'établit qu'une
précision de 0,12 fasse gagner là où 0,10 fait perdre. Lancer le run reviendrait à payer 2 h pour
déplacer une grandeur intermédiaire dont on ignore si elle commande le résultat. C'est le piège de
la phase sous une forme plus fine : non plus « faire monter le R² sans jouer mieux », mais **faire
monter le R² de deux centièmes en espérant que ça compte**.

**Ce que la phase 4 itération 1 produit n'est donc pas un agent, c'est un résultat négatif
solide** — et `prompts/18` le désignait d'avance comme publiable : *« un critique réparé qui ne
fait pas gagner établirait que le critique n'était pas la limite »*. La mesure fait mieux : elle
établit **qu'il n'y avait presque rien à réparer**.

**Ce que ce constat N'ÉTABLIT PAS.**

1. **Qu'un R² plus élevé ferait gagner.** Rien ici ne mesure le jeu. Le lien entre la précision du
   critique et le gain de l'agent n'est ni mesuré ni supposé — il est **inconnu**, et c'est
   exactement pourquoi le seuil décisif est le gain et pas le R².
2. **Que l'architecture testée soit la meilleure possible.** Un perceptron à deux couches cachées
   sous Adam, trois largeurs, jusqu'à 1,5 M nœuds. Une autre classe de modèle, une autre
   représentation ou un objectif auxiliaire pourraient faire mieux — et la tête auxiliaire est
   explicitement l'itération 2.
3. **Que la pente reste linéaire au-delà de 1,5 M nœuds.** Trois intervalles ne font pas une loi.
4. **Que `E[Var(R | info-set)]` ait été mesuré.** Le plancher de 0,193 est conditionné à l'état
   **complet**. Le vrai plafond d'un critique aveugle est **estimé par ajustement**, ce qui en
   fait une borne **basse** : un meilleur modèle ferait mieux.
5. **Que la tête de valeur soit sans défaut.** Elle est près de son plafond d'information ; ce
   n'est pas la même chose qu'être bien faite.

**Impact plan.**

1. **La direction « réparer le critique » est FERMÉE pour cet agent et cette observation.** Elle
   ne se rouvre que par un changement de ce que l'agent VOIT — donc par le paragraphe 4.2 de la
   spécification, qui est un arbitrage de périmètre et non une itération.
2. **L'itération 2 — tête auxiliaire, régression sur l'écart de score final — n'est pas invalidée
   par ce constat**, parce qu'elle ne prédit pas la même quantité. Mais elle hérite de la
   question : *ce qu'elle prédirait est-il visible depuis un info-set ?* **Elle se mesure avant de
   se pré-inscrire.**
3. **Le budget d'entraînement n'est toujours pas désigné**, et ce constat ne le désigne pas
   davantage.
4. **`mesure/phase4.py` et ses 11 cas restent** : ils servent au constat et serviront à l'audit.
   Ils portent l'empreinte SHA-256 de l'adversaire du seuil décisif, sa recette, et l'égalité
   d'échelle de l'avantage.

**Ce que l'étape 0 de la phase a produit, et qui vaut au-delà d'elle.** Le périmètre des mutations
est passé de **20 à 57** motifs, `agents/` et `mesure/` compris, `agents/greedy.py` excepté :
**45 détectées, 11 survivantes, 1 expirée**, relevé reproduit à l'identique par deux campagnes
valides. **Les onze sont aujourd'hui toutes tombées**, et `EXPIRE` a disparu — la suite a
désormais un délai de garde **par test**, 58,8 s = 4 × 14,70 s mesurées sur trois passes. Les
**trois réserves de la phase 3** sont levées, chacune avec sa parade. Cinq jeux de campagne ont
été payés, **quatre pour des défauts de l'instrument** et un seul du premier coup.

**Quatre enseignements de méthode.**

- **Quand une phase repose sur une marge supposée, la marge se mesure AVANT de se pré-inscrire.**
  Le plan disait : pré-inscrire, puis entraîner. En mesurant le plafond d'abord, la marge est
  apparue à ~+0,02 au lieu du ~+0,45 que le 0,57 laissait croire. **En suivant le plan, on aurait
  pré-inscrit un seuil sur une marge crue large, payé 2 h d'entraînement, et découvert la marge
  ensuite.** L'ordre du plan n'était pas faux : il était incomplet d'une étape.
- **Un invariant se tient à TOUS ses sites, pas à un site.** Deux mutations ont survécu au cas
  écrit pour elles, pour la même raison les deux fois : `agents/politique_reseau.py` a **trois**
  sites et le cas n'en visitait qu'un ; l'intitulé du garde-fou demandait **deux parades qui ne se
  remplacent pas** — l'une contre les collisions, l'autre contre un nom qui ne dit rien. Écrire un
  test depuis l'invariant et non depuis la mutation est nécessaire, et **ne suffit pas**.
- **Un prédicat ne se teste pas sur les seules données qui le rendent vrai.** Les quatre cas du
  taux dégénéré étaient testés — tous avec des données **séparables** du côté à un seul dégénéré.
  Un calcul qui aurait rendu « disjoints » quoi qu'il arrive passait les quatre.
- **Une conclusion tirée trop tôt porte la même faute qu'un chiffre sans population.** À 307 000
  nœuds la marge a été annoncée à +0,005 ; à 1,5 M elle vaut +0,0205, quatre fois plus. Le chiffre
  était exact **sur sa population**, et la phrase qui l'annonçait ne la nommait pas.

---

## [2026-08-21] Phase 3 — Le premier agent entraîné

**Hypothèse.** *Écrite et commitée avant tout entraînement,
`mesure/phase3_hypothese_et_instrument.md`.* Un agent entraîné en self-play avec un pool
d'adversaires figés, sur `entrainement-3j`, obtient contre **deux greedys**, sièges permutés, un
**gain moyen strictement positif, borne basse de son IC 99 % bootstrap par donne comprise**.

**Instrument.** PPO à masque d'actions, réseau unique partagé par les trois sièges, tête de
valeur, `γ = 1`, `λ = 1`. Ni le greedy ni l'aléatoire n'entrent dans le pool d'entraînement —
arbitrage du pilote, pour que « bat le greedy » reste un test **hors distribution**. Juge : le
gain moyen, niveau nul **exactement 0,0000**. Budget **dimensionné sur sa propre composition et
jamais emprunté** : σ = 0,6494 et ρ = −0,1400 mesurés sur « un greedy contre deux greedys »,
2 000 donnes, seeds 20000–21999, d'où **6 000 parties** et un écart détectable de +0,0243.
Garde-fou : 1 800 parties par checkpoint, seeds 40000–40599. Rapport régénérable par
`uv run python -m mesure.phase3_mesure`.

**Résultat. L'agent apprend, et il est battu par le greedy. Les deux sont établis, et le second
plus étroitement que le premier livrable ne l'écrivait.**

- **H est INFIRMÉE.** Gain moyen **−0,1643**, IC 99 % **[−0,1824 ; −0,1462]** sur 6 000 parties :
  la borne **haute** est négative. Part de victoire fractionnée **22,38 %** contre 33,3333 % au
  neutre exact. **Trois implémentations indépendantes concordent** — constructeur −0,1643 sur
  2 000 donnes, pilote −0,1719 sur **400 donnes**, auditeur −0,1734 sur 2 000 donnes ; chaque
  intervalle contient les deux autres estimations.
- **L'instrument est calibré sur les seeds exactes du verdict** : le greedy mis à la place de
  l'agent rend +0,0062 IC [−0,0124 ; +0,0255] chez le constructeur, +0,0152 IC
  [−0,0036 ; +0,0338] chez l'auditeur. Les deux contiennent 0.
- **L'agent apprend entre son premier et son dernier checkpoint, et cela seul est établi.**
  Écart apparié ckpt 1 → 8 : **+12,80 pt, IC 99 % [+8,33 ; +17,40]** avec Bonferroni pour
  8 regards. Les intervalles des deux niveaux sont disjoints.
- **« Monotone sans exception » et « encore en progression au dernier » ne sont PAS établis, et
  c'est le défaut bloquant de la phase.** Les sept pas valent +0,86 à +2,50 pt pour une barre
  appariée de **3,56 à 4,06 pt** ; **les huit intervalles se recouvrent 7 fois sur 7** —
  recalculé par le pilote sur le journal brut du run. La remesure de l'auditeur, **mêmes donnes**
  et autre aléa de tirage, porte **deux inversions** et un dernier pas **négatif**, −0,53 pt.
  La monotonie n'était pas une propriété de l'agent, c'était une propriété de son tirage.
- **Le critique n'apprend pas, et c'est le fait le plus actionnable de la phase.** `perte_valeur`
  0,3923 au premier checkpoint, 0,3908 au huitième, sans amélioration entre les deux. Le pilote a
  reconstruit l'**unité avant la valeur** — `mse_loss` sur les retours **bruts**, ni GAE ni
  actualisés — puis mesuré la variance de ces retours : **0,4275**. L'auditeur l'a confirmée hors
  plage d'entraînement (0,4190) et a mesuré ce que le pilote n'avait pas fait, le **plancher
  irréductible** `E[Var(R | état)] = 0,1815`, soit **43 %**. `R² = +0,093` quand **0,57** est
  atteignable. Et le plancher **s'effondre avec la profondeur** — 0,32 à 0,0075 à l'avant-dernière
  décision — alors que la MSE du critique **reste plate**, 0,36 à 0,30. **La valeur n'est pas
  imprédictible dans ce jeu : le critique est mauvais, y compris là où la partie est déjà
  écrite.**
- **σ a bougé de −12,1 %** (0,5710 contre 0,6494) mais la règle pré-inscrite portait sur la
  **demi-largeur**, qui n'a bougé que de −1,1 % : le déclencheur n'était pas franchi. La règle
  était **aveugle au mouvement qu'elle prétendait détecter**, σ et l'effet de plan ayant bougé en
  sens contraire et se compensant dans le produit surveillé.
- **Comportements**, ligne de base **régénérée** « trois greedys, un seul siège compté » :
  `B1-motif` 42,48 % contre 45,83 % — l'agent manifeste le motif **moins** que le greedy ;
  `B4-brut` 31,93 % contre 15,93 % ; `B4-contre-nature` 35,87 % contre 0,00 % (0/1967). Le
  constructeur **refuse** d'y lire une planification, et il a raison : deux hypothèses produisent
  ce compteur — l'agent voit plus loin, ou l'agent joue moins bien — et le juge dit qu'il est
  battu.

**Audit. VERDICT FINAL : ACCEPTÉ SOUS RÉSERVE**, au troisième tour. **REJETÉ** aux deux
premiers.

*Tour 1 — livrable `9c96f65`, verdict **REJETÉ**.* Deux bloquants, quatre majeurs, huit mineurs,
**97 contrôles hostiles**, plan d'audit **pré-inscrit et commité avant d'ouvrir un fichier du
constructeur**. Confirmé par du code indépendant : le verdict, la calibration du niveau nul,
l'aveuglement complet du réseau par **88 contrôles** — tenseur et logits invariants **bit à bit**,
zéro appel privilégié compté pendant la décision, brouilleur prouvé capable d'attraper une fuite
d'**une seule** composante —, et la disjonction des populations **au niveau des donnes** :
0 collision de pioche entre 14 600 donnes de mesure et **1 486 336** donnes d'entraînement
balayées en entier.

*Tours 2 et 3.* Douze des quatorze défauts levés au tour 2, puis **deux bloquants neufs, nés dans
les corrections** : une phrase « aucune ligne ne change de statut » devenue fausse sur les deux
lignes portant un zéro absolu, et **un cas de test qui écartait son propre contre-exemple en
falsifiant son entrée** — il écrivait `1` là où la mesure disait `0`. Levés au tour 3 par le
calcul de la borne exacte de Clopper-Pearson que la docstring prescrivait sans qu'aucun code ne
l'exerce : **0/1967 → 0,2338 %**, **0/10382 → 0,0443 %**, bornes **unilatérales** à 99 %,
reconstruites au quatrième décimal par le pilote et par l'auditeur.

**L'audit croisé a perdu son indépendance pendant un tour entier, par une faute du pilote.** Le
prompt de corrections, adressé à la conversation de construction, a été collé dans celle d'audit.
**L'auditeur a donc corrigé les défauts qu'il avait lui-même trouvés**, et il l'a signalé deux
fois — le pilote a lu la première et a continué. Les rôles ont été échangés pour la suite : la
conversation d'audit est devenue constructeur de ses corrections, celle de construction en est
devenue l'auditeur. C'est ce croisement inversé qui a trouvé les deux bloquants du tour 2.

**Trois réserves restent ouvertes**, aucune ne falsifiant un chiffre publié :

1. **Un intitulé « 99 % » qui couvre deux risques.** Les deux bornes exactes sont
   **unilatérales** ; tout le reste du rapport publie des intervalles **bilatéraux** à 99 %. Les
   bilatérales vaudraient 0,2690 % et 0,0510 % — la conclusion ne bouge pas, le libellé est
   faux. `mesure/resultats/phase3.md` écrit **quatre fois** « borne haute à 99 % » sans
   qualificatif, cinquante lignes sous un « 99 % bilatéral ». *La présente entrée écrit le
   qualificatif ; le rapport, non.*
2. **Le rendu du verdict exact n'est écrit que pour un des quatre cas que la règle couvre** — un
   zéro côté agent est annoncé « de la ligne de base », un cent est annoncé « le zéro », deux
   zéros font parler d'un intervalle qui n'existe pas. **Aucun de ces trois cas n'est atteignable
   sur les données de cette phase.**
3. **La parade des intitulés ne couvre qu'une écriture d'appel.** `from agents import campagne as
   X` puis `X.intitule_du_garde_fou()` passe au travers, et c'est l'écriture du dépôt. R2 attrape
   toujours le doublon : un filet, pas deux.

**Décision. PIVOT DE DIAGNOSTIC, et le levier n'est pas le budget.** La phase 3 est close ; son
hypothèse est infirmée. La table go/no-go dit « diagnostiquer avant d'insister », et la mesure
désigne la **tête de valeur** — ce que le §7.1 de la pré-inscription avait écrit d'avance comme
réponse prévue. **Le budget n'est pas *écarté*, il est *non désigné* :** la courbe ne montre pas
qu'elle montait encore, et rallonger un run dont l'avantage de PPO est dominé par le bruit du
retour rallonge le bruit.

**Impact plan.**

1. **Le premier travail de la phase 4 est d'étendre le périmètre des mutations à `mesure/` et au
   reste de `agents/`**, `agents/greedy.py` excepté. Les 20 motifs ne couvrent que `courtisans/` :
   « 20 mutations, toutes détectées » ne dit rien des ~2 500 lignes neuves. Le défaut le plus
   instructif de la phase 2 vivait dans le **générateur**, pas dans le moteur.
2. **Le premier levier est la tête de valeur, pas le budget**, et il se pré-inscrit avec un seuil
   falsifiable sur `R²` avant d'être implémenté. Une variable à la fois.
3. **Les trois réserves ci-dessus sont à traiter au début de la phase 4.**
4. La ligne de base **« trois greedys, un seul siège compté »** existe et est régénérable ; toute
   phase mesurant un agent contre deux adversaires la cite plutôt que la colonne à trois sièges de
   la phase 2 — en disant que ses donnes sont celles de la phase 2, pas celles de l'agent.

**Cinq enseignements de méthode.**

- **Un garde-fou doit tester la phrase qu'il écrit, à un budget qui lui permette de la tester.**
  Celui de la phase 3 a porté **cinq** défauts successifs : il se déclenchait quand le run était
  fini ; puis au premier checkpoint ; puis sur une prémisse fausse — « n'atteint pas le greedy »
  confondu avec « n'apprend pas » ; puis à une portée d'un checkpoint, où le progrès cherché est
  **par construction** sous le seuil de détection ; puis aveugle à un effondrement, un écart
  établi **négatif** satisfaisant sa condition. **Quatre des cinq sont nés dans le texte qui
  corrigeait le précédent, et deux sont du pilote.**
- **Une courbe d'apprentissage se publie avec l'intervalle de ses ÉCARTS, pas de ses niveaux.**
  C'est un écart qui décide ; les écarts appariés ne coûtent pas une partie de plus. Huit
  intervalles publiés sur huit niveaux, aucun sur les sept écarts, et la phrase qui portait toute
  la décision ne tenait sur aucun d'eux.
- **Un contrôle qui ne peut pas échouer ne se compte pas parmi les contrôles concluants**, et
  **un cas dont on choisit les données pour qu'il passe ne teste rien.** Les deux sont sortis dans
  la même phase : deux contrôles passant un `True` littéral, et un cas écrivant `1` là où la
  mesure disait `0` pour écarter son propre contre-exemple.
- **Une parade doit vérifier qu'elle a inspecté quelque chose.** Un balayage `range(2900, 3101,
  20)` ne visitait qu'une des deux branches de l'équivalence qu'il annonçait : vert depuis un tour
  entier sans avoir jamais éprouvé la moitié de son énoncé. Même famille qu'une parade AST aveugle
  à une écriture syntaxique, et qu'une injection dont l'ancre n'existe pas — l'auditeur a commis
  la troisième en cherchant la première.
- **Un niveau de confiance porte sa latéralité.** Deux grandeurs sous le même « 99 % » n'ont pas
  le même risque si l'une est unilatérale.

---

## [2026-08-19] Phase 2 — Mesurer le jeu avant d'y jouer

**Hypothèse.** *Écrite et commitée avant toute mesure, `mesure/phase2_hypothese_et_instrument.md`.*
La position de départ n'avantage aucun siège de façon décisive. Seuil du protocole : un siège
au-delà de 38 % des parties rend l'avantage structurel et impose la permutation systématique.

**Instrument.** Trois campagnes sur `entrainement-3j`, 10 002 parties chacune. A : trois
aléatoires, 1 667 donnes × 6 réplicats, seeds 0–1666, `Random(2000000 + 6×donne + réplicat)`.
A contrôle : seeds 10000–11666. B : 1 greedy contre 2 aléatoires, 3 334 donnes × 3 sièges,
`Random(3000000 + 3×donne + siège)`. Bootstrap **par donne**, 10 000 réchantillons,
`Random(2500000)`. Une quatrième population ajoutée après l'audit : trois greedys, décalage
`6000000`, pour la seule ligne de base collective. Rapport régénérable par
`uv run python -m mesure.phase2`.

**Résultat. Les quatre mesures sont établies, et le seuil n'est pas franchi.**

- **M1.** Siège le plus favorisé à **33,50 %** de part de victoire fractionnée, +0,35 σ de
  l'attendu ; gains moyens à ±0,004 de zéro. Le seuil de 38 % n'est pas franchi, et il
  n'aurait rien testé : il est à **9,9 σ** de la valeur nulle à n = 10 002, et ne devient un
  test à 5 % qu'à n = 392. Trois niveaux neutres coexistent — 0,0000 pour le gain, 33,33 %
  pour la part fractionnée, `(1 − P(ex æquo))/3` pour la part stricte, qui **ne peut donc pas
  servir de seuil**.
- **M2.** σ(score) = **4,412**, σ(gain) = **0,6652**. Corrélation intra-donne mesurée à
  **ρ = 0,0066** sous jeu aléatoire, soit un facteur de gain de 1,01 contre les « cinq à dix »
  qu'annonce le §1 du protocole — affirmation qui reste **non appuyée**. À 1 000 parties
  appariées, l'écart de gain détectable est **+0,1013**.
- **M3.** Greedy contre deux aléatoires : gain moyen **+0,7978**, part de victoire fractionnée
  **86,52 %** — à comparer à 33,33 %, pas à 50 %. Et un résultat que M1 seul ne pouvait pas
  donner : **l'avantage de siège est négligeable sous jeu aléatoire et massif sous jeu
  greedy**, contraste apparié entre sièges extrêmes **+0,1890** IC 99 % [+0,1588 ; +0,2196].
  La permutation systématique était donc la bonne décision, pour une autre raison que celle
  qui la motivait.
- **M4.** Dix-sept compteurs, chacun avec son dénominateur, son grain et sa vue. `B1-motif`
  **47,93 %**, `B4-brut` **23,65 %**, `B7-gaspillage` **0,15 %**. Chaque ligne porte l'écart
  détectable au budget de la phase 3 ; **19 lignes sur 34 sont hors budget**.

**Audit.** **Trois tours**, par une conversation distincte qui a réimplémenté depuis le texte
des règles sa propre vue légale, son greedy, ses sept compteurs et son intervalle de confiance,
sans réutiliser une ligne du constructeur, et écrit **75 contrôles hostiles et de
re-vérification**. Code : `audit/phase2/` et `tests/audit_phase2/`. Verdicts dans
`audit/verdict_phase_2.md`, `audit/verdict_phase_2_tour_2.md` et
`audit/verdict_phase_2_tour_3.md`.

*Tour 1 — livrable `02ae24b`, verdict **REJETÉ**.*

Ce que l'audit a **confirmé**, par du code indépendant : σ(gain) 0,6671 contre 0,6652 ; gains
de siège du greedy 0,714 / 0,815 / 0,895 contre 0,697 / 0,812 / 0,886, donc le résultat central
de M3 ; taux de refus B4 23,81 % IC 99 % [22,53 ; 25,12] contre 23,65 % ; **395 lignes sur 395
du rapport régénérées à l'identique** ; et que **B7 est aveugle par le bas** — écart détectable
0,12 % pour un taux de 0,10 %, un agent à zéro exact n'en est pas séparable. Deux lectures
indépendantes du §2.2 ont convergé sur l'Indifférence comme seuil de B1, comme elles avaient
convergé sur R2 en phase 1.

**Le greedy ne triche pas**, et c'était la cible numéro un. Sa preuve est à trois niveaux —
statique, `vue_privilegiee` piégée pour lever pendant la décision, brouillage différentiel des
Espions adverses, de la pioche et des mains — chacun assorti d'un test que **le piège mord** et
que **le brouilleur change vraiment la vérité**. L'auditeur l'a refaite par cinq contrôles
distincts, dont un balayage de 60 parties permutant l'identité de chaque dos à chaque nœud.

Ce que l'audit a **trouvé** : un défaut **bloquant** — cinq lignes du §6 publiaient sous
l'intitulé « écart greedy-hasard observé » une différence entre **deux grains**, greedy sur un
siège contre hasard sur trois agrégés, avec **inversion de signe** sur B1 (−23,97 pt au lieu de
+11,82 pt) et un coût en parties qui la présentait comme un effet réel. Le §5 portait
l'avertissement, le §6 non — et c'était la réserve laissée ouverte au tour 2 de la phase 1, au
même endroit. Deux **majeurs** : la clause d'Indifférence de B1 n'était tenue par aucun test —
la faute du tour 1 de la phase 1, réinjectée, passait 913 tests et déplaçait le chiffre publié
de 9,27 points, plus que les 7,64 points détectables au budget de la phase 3 ; et le greedy
évaluait sa pose sous une résolution conjointe des Assassins que son ciblage, myope, ne
poursuit pas — 7,33 % des nœuds à Assassin en attente ont un argmax différent. Quatre mineurs.

*Tour 2 — corrections `72630a1`, verdict **ACCEPTÉ SOUS RÉSERVE**.*

Les quatre défauts sont corrigés, et **trois le sont avec la parade qui empêche la correction
de se défaire** : une exception `GrainsIncomparables` levée par `ecart_de_taux` **et**
`cumuler` plutôt que des cellules réécrites, un grain qui porte le nombre de sièges agrégés
là où les deux libellés étaient auparavant identiques, un invariant asserté dans
`observations_par_partie`, et une fonction unique `budget_d_un_compteur` là où trois sites
déduisaient chacun leur dénominateur. Le greedy n'est pas corrigé mais **caractérisé** — §4 bis,
`mesure/coherence_greedy.py`, un test de caractérisation — et c'est le bon choix : la ligne de
base des phases suivantes est celle de *cet* agent, et déplacer l'étalon après publication est
le mode de défaut du projet. La pré-inscription n'est pas amendée, vérifié par `git diff`.

**Un cinquième défaut a été trouvé après le verdict, par relecture humaine, et il est le plus
instructif de la phase.** Le générateur divisait les budgets par un facteur trois qui n'avait
pas lieu d'être : un compteur `-par-partie` rend **un** booléen par partie quel que soit le
nombre de sièges, l'agrégation étant dans son numérateur. Six budgets étaient gonflés d'un
facteur exactement trois. Il a été validé deux fois avant d'être vu, par une vérification qui
reproduisait le nombre en recevant **le même dénominateur erroné** — deux implémentations qui
partagent la même hypothèse fausse concordent parfaitement. Les six valeurs corrigées, 745,
1 295, 299, 239, 10 400, 280, ont été reconstruites par l'auditeur avec ses propres quantiles
et son propre dénominateur par partie, dérivé du **texte de l'unité avant tout calcul** :
**6 sur 6 à l'unité près**.

Deux réserves, de la même famille — **un compte à la place de noms**. Le §4 bis écrit « trois
compteurs de B4 sont jugés par cette même évaluation myope » là où le code en concerne
**quatre**, et n'en nomme aucun ; l'omis est `B4-meurtre-couteux`, l'un des deux zéros absolus
du rapport. Et l'inclusion `B1-collectif ≥ B1-motif`, dont la chute a déjà révélé un compteur
faux, est vérifiée sur les deux anciennes colonnes et pas sur la troisième population — celle
qui existe précisément pour `B1-collectif`. L'auditeur l'a vérifiée lui-même : 3 916 ≥ 2 528 au
même grain, elle tient.

*Tour 3 — corrections `479a57e`, verdict **ACCEPTÉ**.*

Les deux réserves sont levées et le test que l'auditeur avait laissé rouge revient par son nom,
vert : `test_p3_les_compteurs_juges_par_l_evaluation_myope_sont_QUATRE_et_nommes`. Le §4 bis
écrit désormais **quatre** compteurs, les nomme, et ajoute que **les deux zéros absolus sont
dans ce lot** — aucune occurrence de « trois compteurs de B4 » ne survit dans le dépôt, y
compris dans `agents/greedy.py`, la spécification de l'agent, où la phrase était la même.
`verifier_inclusion_b1` **lève** et le rapport l'appelle sur les **trois** populations avant
d'écrire, aux **deux** grains — extension au grain `-par-partie` qui n'était contrôlé nulle
part. L'auditeur a éprouvé les deux branches aux deux grains, y compris le cas d'égalité, qui
est licite. **977 tests verts, 0 rouge.**

Une **quatrième occurrence de la même faute** est sortie dans ce tour, trouvée par le
constructeur dans la dernière phrase qu'il venait d'écrire : sa ligne de durées machine annonçait
« −26 % à +16 % » sur « les cinq campagnes » alors que le −26 % venait de `B, 3 greedys`, qui
n'existe que dans les passes 3 à 5 et que la phrase excluait. Deux chiffres exacts sur une
population que la phrase ne nommait pas. Corrigé en « −23,3 % à +15,5 % », refait par l'auditeur.

Quatre mineurs du tour 1 restent ouverts, hors du périmètre re-vérifié : l'encodage cp1252 du
rapport généré quand les quatre autres documents sont en UTF-8 ; `vue_du_joueur`, rendue
publique par cette phase, qui ne valide pas son argument et rend une vue n'appartenant à aucun
siège — réouverture du défaut 2 de la phase 0 sur une entrée neuve ; deux des douze directions
annoncées comptées comme tenues alors que la pré-inscription les déclare nulles **par
construction** ; et une cellule « voir `B4-departage` » dans une table dont le texte dit
qu'elle ne se lit qu'en juxtaposant deux nombres.

**Le seul point resté ouvert au tour 1 est clos, et il appartenait à l'auditeur.** Son 7,33 %
et le 4,23 % du constructeur mesurent la même chose sur **deux populations différentes** :
trois greedys donne 287/4 145 = 6,92 % IC 99 % [5,95 ; 8,00], un greedy contre deux uniformes
donne 204/4 145 = 4,92 % IC 99 % [4,10 ; 5,85], et 0,4064 contre 0,4062 nœud par **siège-partie
mesuré** établit que la définition du dénominateur est identique. Les deux populations comptent
10 200 sièges-parties pour 3 400 et 10 200 parties jouées : c'est l'égalité des sièges-parties,
non celle des parties, qui rend les deux taux comparables. Et leur dénominateur commun de
4 145 nœuds est **structurel** — chaque joueur vide sa main à chaque tour et la recomplète
depuis une pioche fixée par la donne, donc la main d'un siège, et le nombre d'Assassins qu'il
pose, ne dépendent pas de la politique ; MESURÉ identique sur 40 donnes et trois compositions.
Les deux nombres étaient justes ; celui de l'auditeur était publié sans nommer sa population —
la faute qu'il reprochait ailleurs.

Une **troisième réserve** a été relevée après le verdict, dans le harnais de l'auditeur
lui-même : son compteur s'appelait `parties` et comptait des itérations, si bien que sa phrase
« nœud par partie » nommait une unité qui n'était pas celle du calcul. Aucun taux, aucune borne
et aucune conclusion ne changent. Corrigée, et tenue par deux tests — l'un sur l'égalité des
sièges-parties, l'autre sur l'indépendance de la main à la politique.

**Décision. Go.** Verdict final **ACCEPTÉ** au tour 3. La phase 2 est close. Les quatre lignes de base sont établies et citables par
les phases suivantes, à trois conditions écrites dans le rapport lui-même : B1 et B3 mesurent
chez le greedy la fréquence à laquelle le **motif** apparaît par coïncidence, jamais une
planification ; B1 est plafonné par les 7,40 % de parties portant une perte d'acquis qu'aucun
siège ne pouvait voir, mesurés en phase 1 ; et **19 des 34 lignes de M4 sont hors du budget de
la phase 3**, B7 n'y pouvant rien séparer du tout.

**Impact plan.** La phase 3 s'ouvre sans modification, avec quatre contraintes qui en viennent.
La permutation des sièges est **obligatoire et inconditionnelle** — non parce que M1 l'exige,
il ne la déclenche pas, mais parce que l'avantage de siège sous jeu greedy est massif. Le seuil
« > 55 % contre le greedy sur 1 000 parties appariées » doit être relu contre l'écart de gain
détectable mesuré, **+0,1013** à ce budget. Les comparaisons de comportement doivent citer les
lignes **au même grain**, la garde levant désormais si elles ne le sont pas. Et la ligne de base
collective de `B1-collectif` est celle des **trois greedys**, pas celle d'un greedy contre deux
hasards.

**Défauts du protocole, à corriger dans
[05_protocole_experimental.md](../documentations/05_protocole_experimental.md).** Cinq trous, dont
quatre déjà relevés en phase 1 et un nouveau. Le seuil de 38 % de M1 ne dit pas ce qu'est
« gagner » quand les égalités sont conservées, et les trois lectures possibles n'ont pas la même
valeur nulle — sous la lecture la plus littérale, « être au score maximum, ex æquo compris »,
les **trois** sièges valent 38,5 % et le seuil se franchit avec un avantage nul. « La variance
du score final » ne nomme pas son unité, et celle qui dimensionne une comparaison est la
variance du **gain**, pas du score. « Si le greedy est à 60 % » ne dit pas contre quoi, ni que
le point de comparaison à trois joueurs est 33,33 %. L'affirmation que l'appariement « divise
par cinq à dix » le nombre de parties nécessaires est **publiée sans mesure** et infirmée pour
les deux politiques mesurées ici — ρ = 0,0066. Enfin la phase 2 est annoncée comme ne pouvant
pas échouer : c'est vrai de son go/no-go et faux de tout le reste, puisqu'elle produit les
lignes de base que toutes les phases suivantes citeront sans les rejouer.

**Six enseignements de méthode.**

- **Un chiffre qui se reconstruit n'est pas un chiffre juste.** Le facteur trois a survécu à
  deux vérifications A7 réussies, parce que la formule de contrôle recevait le même
  dénominateur erroné que le générateur. **L'unité se reconstruit avant la valeur, et
  séparément.** C'est le contrôle qui manquait, et il ne se confond pas avec A7.
- **Une correction arrive avec ce qui l'empêche de se défaire.** Trois des quatre corrections
  de ce tour sont des levées d'exception ou des invariants assertés, pas des cellules
  réécrites — et la seule qui ait été trouvée deux fois au même endroit, le grain du §6, est
  précisément celle qu'un tour antérieur avait corrigée sans parade.
- **Un compte n'est pas une liste de noms.** « Trois compteurs de B4 » en concerne quatre ;
  « vérifiée sur les deux colonnes » n'en couvre plus deux depuis qu'il y en a trois. Les deux
  réserves de ce tour sont la même faute, et elle se referme en écrivant les noms.
- **Un agent de référence se documente, il ne se corrige pas après publication.** L'incohérence
  d'horizon du greedy est réelle et mesurée ; la corriger aurait déplacé l'étalon de toutes les
  phases suivantes. Le test qui l'interdisait a été requalifié en test qui la caractérise, par
  l'auditeur et sur son propre code.
- **La correction est le lieu du défaut suivant, et il faut donc relire ce qui a été écrit en
  dernier, pas ce qui a été mesuré en premier.** Quatre fois de suite dans cette phase : le
  défaut 3 corrigé puis laissé à moitié puis complété, le défaut 5 né dans la table qui
  corrigeait le défaut 1, la réserve 3 née dans le harnais de l'auditeur, et la clause des
  durées née dans le commit qui consignait la leçon. **La même faute — un chiffre exact sur une
  population que sa phrase ne nomme pas — est sortie sous quatre formes dans une seule phase**,
  chez le constructeur comme chez l'auditeur, et chaque fois dans le texte le plus récent.
- **Un contrôle de non-régression n'établit pas la justesse d'une unité, seulement la neutralité
  d'un refactor.** Si une ligne portait un dénominateur faux depuis le début, le contrôle
  passerait à l'identique. C'est le piège du `2 234` appliqué à un contrôle au lieu d'un nombre,
  et c'est le constructeur qui l'a écrit à côté de son propre instrument.

**Et une cinquième occurrence, dans cette entrée même.** La proposition de l'auditeur
annonçait « quatre enseignements de méthode » et en listait **six** — un compte à la place
d'une liste de noms, dans le texte qui nomme cette faute quatre fois. Corrigé au report par
le pilote. La leçon tient donc sur elle-même : **relire ce qui a été écrit en dernier**,
y compris quand c'est la leçon.

---

## [2026-08-18] Phase 1 — L'instance d'entraînement, et audit croisé de sa mesure

**Hypothèse.** *Écrite et commitée avant toute mesure, `mesure/hypothese_et_instrument.md`.*
L'instance `entrainement-3j` — 4 familles, 5 rôles, 2 exemplaires, 3 joueurs, 40 cartes,
4 tours — conserve la substance du jeu : sous jeu uniformément aléatoire, sur 1 000 parties,
les trois joueurs jouent le même nombre de tours (H1), la distribution des scores n'est pas
dégénérée (H2), et au moins un retournement survient dans au moins 33,3 % des parties (H3).

**Instrument.** 1 000 parties, donne `Engine.reset(seed)` seeds 0–999, politique uniforme sur
`legal_actions()` avec `Random(1_000_000 + seed)`. Seuil H3 : `p ≥ 1/3`, intervalle exact de
Clopper-Pearson à 99 %, bande d'indécision [0,295 ; 0,372] fixée d'avance. La mesure tranche
dès N = 30 si `p̂ ≥ 0,80`. Le protocole ne définissant pas « retournement », quatre définitions
ont été pré-inscrites ; le go/no-go porte sur **R2, perte d'acquis** — `∃t : s_{t−1} ≠
Indifférente et s_t ≠ s_{t−1}` — parce que l'encadré du §2.2 des règles tranche déjà que le
seuil qui compte est l'Indifférence et non l'Obscurité.

**Résultat.** Hypothèse **vérifiée sur les trois énoncés.** H1 : 1 000/1 000, vecteur de poses
`(4, 4, 4)`. H2 : 10/10 critères, écart-type 4,4 par siège, 25 à 26 valeurs de score
distinctes, mode à 9 %, trois ex æquo dans 1,5 % des parties. H3 : **96,00 % (960/1 000),
IC99 [94,12 % ; 97,42 %]**, soit 2,88 fois le seuil — borne basse à 94,12 %. 2,075 familles
retournées par partie sur 4. Une partie se joue en 1,6 ms, 19,2 décisions. 82,53 % des
7 206 nœuds de ciblage offrent au moins une cible, donc un refus qui est un choix et non un
constat.

**Audit.** Deux tours, par une conversation distincte qui a réimplémenté le calcul de statut,
le compteur de retournements, l'intervalle de confiance et la campagne depuis le texte des
règles, sans réutiliser une ligne du constructeur, et écrit seize contrôles hostiles.
Code de l'audit : `audit/` et `tests/audit/`, verdict détaillé dans
`audit/verdict_phase_1.md`.

*Tour 1 — livrable `3f5b75d`, verdict **REJETÉ**.*

Ce que l'audit a **confirmé** : les trois critères de go/no-go, remesurés indépendamment —
`(4, 4, 4)` dans 5 000 parties sur 5 000, retournements à 94,0–95,5 % selon le bloc de seeds,
étendue de 1,5 point ; l'accord des deux calculs de statut sur **11 000 comparaisons,
0 désaccord** ; l'exactitude de l'intervalle sur **820 couples (k, n, α), écart maximum
2,5 × 10⁻¹²**, par quatre calculs indépendants ; l'estimation « ~8 cartes par domaine » qui
fondait le seuil D2, mesurée à **6,99** ; et la **convergence de trois lectures indépendantes
du §2.2** sur la définition R2, l'auditeur ayant écrit la sienne avant de lire celle du
constructeur. Le constructeur ne surinterprète pas non plus son chiffre : sa pré-inscription
écrit, avant la mesure, que l'aléatoire n'établit pas qu'un agent saura planifier un
retournement.

Ce que l'audit a **trouvé, et que le constructeur avait manqué** : l'affirmation « **0 sur
1 000 retournements R2 invisibles des trois joueurs** » était **fausse**. Le calcul agrégeait
les quatre familles en un booléen de partie avant de comparer les vues, puis les trois sièges
par un `any` ; il comptait « une partie où la vérité a un R2 et où aucun siège n'en a sur
aucune famille », conjonction quasi impossible entre deux grandeurs valant 96 % et ~93 %. Le
même invisible, mêmes seeds, sous le décalage de politique du constructeur, **grain tour** :

| Niveau d'agrégation | seeds 0–999 | seeds 1000–1999 |
|---|---|---|
| partie, familles confondues — *le chiffre publié* | 0 | 0 |
| famille — invisibles / familles en R2 | 5 / 2 075 = **0,241 %** | 11 / 2 026 = **0,543 %** |
| famille — invisibles / emplacements famille × partie | 5 / 4 000 = 0,125 % | 11 / 4 000 = 0,275 % |
| événement — invisibles / pertes d'acquis | 79 / 2 665 = **2,96 %** | 56 / 2 531 = 2,21 % |
| événement — parties touchées | 74 / 1 000 = **7,40 %** | 56 / 1 000 = 5,60 % |

**Le dénominateur retenu au niveau famille est 2 075, les familles qui ont effectivement perdu
un acquis** : la question posée est « parmi les retournements qui ont eu lieu, lesquels
n'étaient visibles de personne ». Rapporter les mêmes 5 aux 4 000 emplacements famille × partie
répond à une autre question — quelle part du plateau porte un retournement invisible — et
divise le taux par deux. Les deux lectures sont justes ; les deux sont écrites ci-dessus
précisément parce qu'un taux sans son dénominateur n'est pas auditable.

Cinq témoins nommés au premier bloc : seeds 308, 453, 496, 539, 933. Le cas se construit à la
main en quatre poses — deux Espions de même famille posés par deux joueurs différents — et
touche **une partie sur treize à dix-huit** (74/1 000 = 1 sur 13,5 ; 56/1 000 = 1 sur 17,9 ;
au grain fin, 75 et 57 pour 1 000, soit 1 sur 13,3 et 1 sur 17,5). **Son propre test le
démontrait déjà** : `tests/mesure/test_parties_construites.py` assertait exactement ce cas, sa
docstring écrivant « un retournement que personne ne pouvait planifier ». Le test et le rapport
se contredisaient dans le même livrable.

Cinq défauts mineurs par ailleurs : une assertion tautologique, l'instance définie trois fois,
quatre littéraux en dur dans les décompositions du rapport, un seuil D2 franchi dès 12 parties
donc sans pouvoir discriminant, et un intervalle qui ne validait pas `n > 0`.

*Tour 2 — correction `d7398bd`, verdict **ACCEPTÉ SOUS RÉSERVE**.*

Les six défauts sont corrigés. Le comptage de l'invisible ne compare plus que des grandeurs
non agrégées et publie les deux niveaux avec leurs dénominateurs ; **l'implémentation
indépendante de l'auditeur rend exactement le même nombre au même grain** — 81 événements
invisibles sur 2 735 dans 75 parties au grain fin, contre 79 sur 2 665 dans 74 parties au
grain tour, celui que le rapport publie. Deux défauts sont corrigés mieux que demandé : le
pouvoir discriminant est mesuré pour les **quatre** critères, et non le seul D2 relevé par
l'audit — D1 et D3 sont satisfaits dès 3 parties, D4 dès 1 —, et le §5.3 de la pré-inscription
porte un erratum qui **conserve** la phrase fausse plutôt que de l'effacer. L'auditeur a
re-vérifié la correction en y ré-introduisant la faute exacte : un test rouge, sur une partie
construite à la main. Les trois chiffres du go/no-go sont inchangés. 648 tests verts chez le
constructeur, les 16 contrôles hostiles de l'auditeur verts contre le code corrigé.

Deux réserves : rien ne relie la définition unique de l'instance dans `mesure/instance.py` à
la description indépendante de `tests/outils.py` — l'indépendance de l'oracle est justifiée,
l'absence de garde-fou contre la dérive ne l'est pas ; et la section 6 du rapport ne répète pas
le grain sur ses deux blocs de comptage, si bien qu'un lecteur reconstruisant 2 078 familles au
grain fin au lieu de 2 075 au grain tour ne peut pas savoir laquelle des deux lectures est la
sienne.

**Décision.** **Go.** La phase 1 est close. `entrainement-3j` est l'instance des phases 2 et 3.

**Impact plan.** La phase 2 s'ouvre sans modification. Une mesure s'ajoute à sa liste : la
fréquence des retournements qu'**aucun** siège ne voit est un **plafond de ce que B1 peut
mesurer**. Une ligne de base d'agent qui ne planifie jamais un retournement doit être lue en
retranchant les ~7 % de parties portant une perte d'acquis qu'aucune politique, aussi bonne
soit-elle, ne pouvait voir venir.

**Défauts du protocole, à corriger dans [05_protocole_experimental.md](05_protocole_experimental.md).**
Trois termes du go/no-go de la phase 1 ne sont définis nulle part, et les trois sont chiffrés :
« retournement », « distribution non dégénérée », et « situations où refuser de tuer est
possible » — dont la lecture littérale est **vide**, refuser étant toujours légal (§4.1,
arbitrage R2), si bien que la fréquence vaudrait 100 % par construction. Les définitions
proposées par le constructeur ont tenu deux tours d'audit et doivent remonter dans le document.
Le §3 présente en outre « 20 cartes ou 40 cartes » comme un arbitrage à trancher en phase 1 :
il n'en est pas un, la variante à 20 cartes étant refusée à la construction par le plancher
`tours ≥ 3` du §8 des règles.

**Trois enseignements de méthode.**

- **Un taux dont le sujet grammatical n'est pas l'unité comptée doit publier son
  dénominateur.** L'erreur de ce tour n'est ni un calcul faux ni un DÉDUIT présenté comme un
  MESURÉ : c'est un chiffre juste, reproductible au bit près, dont la phrase parlait de
  retournements quand le calcul parlait de parties. Aucun contrôle existant ne cherchait cette
  faute-là.
- **Un zéro absolu doit être confronté à un cas construit à la main avant d'être écrit.**
  Celui-ci était contredit par un test du même livrable.
- **Un chiffre doit porter son échantillon — grain et dénominateur compris.** L'auditeur a
  commis deux fois la faute qu'il reprochait : d'abord en juxtaposant deux comptes justes,
  70 et 81 événements sur les mêmes seeds, sans dire que le décalage de politique différait —
  cause racine, une valeur en dur invisible dans les chiffres qu'elle produisait, devenue un
  paramètre nommé ; ensuite en écrivant « 5 familles sur 4 000 » sans dire que « 5 sur 2 075 »
  existait et disait autre chose. Les deux corrections sont dans cette entrée.

---

## [2026-08-17] Phase 0 — Audit croisé du moteur conforme

**Hypothèse.** Le moteur construit par la conversation de l'action 3 implémente les règles de
`01_regles.md`, et ses 502 tests verts l'établissent.

**Instrument.** Protocole d'audit croisé, `07_protocole_audit_croise.md`. Contrôles A1 à A7
par une conversation distincte, qui rejoue tous les chiffres elle-même et écrit ses propres
tests hostiles contre le **texte des règles**, sans appeler une seule fonction du moteur pour
calculer un attendu. Seuil de rejet fixé d'avance : un critère non satisfait, un test hostile
rouge, ou une affirmation fausse dans le compte rendu.

**Résultat.** Hypothèse **partiellement rejetée**. Aucun défaut de conformité aux règles —
61 cas hostiles, dont une construction de fuite d'information à pioches jumelles et une
traduction complète de l'espace d'actions sous permutation des familles, n'en ont produit
aucun. Mais **neuf défauts** dans l'adaptateur, la stratégie de test et la documentation, en
trois tours :

| Tour | Défauts | Les deux qui comptent |
|---|---|---|
| Audit initial | 6 (2 majeurs, 4 mineurs) | `make_py_observer` absent → le harnais de validité d'OpenSpiel ne pouvait pas tourner ; l'observation d'un identifiant réservé rendait une vue **n'appartenant à aucun joueur**, sans lever |
| Correction 1 | +1 trouvé par le correctif | libellés d'action dupliqués — trouvé par `random_sim_test` en une exécution, que 502 tests maison n'avaient pas vu |
| Re-vérification | +2 | régression sur le motif d'appel d'OpenSpiel (34 sites, dont `deep_cfr` et `best_response`) ; le jeu ne survivait pas à un aller-retour par sa propre chaîne de paramètres |

État final, **remesuré par l'auditeur** sur `b90f714` : 576 tests verts, 127/127/127 sur les
trois moteurs, 143 invariants, 8/8 critères, **618 instructions et 0 manquante**, **18
mutations sur 18 détectées**, `ruff` propre.

**La réserve unique de cet audit est levée le 17/08.** Elle portait sur
`_action_to_string`, qui nommait la famille et le rôle de la carte ciblée par un Assassin —
`tuer la cible 1 : f0-ESPION` — y compris lorsque cette carte était un Espion posé face
cachée par un adversaire, dont le joueur qui choisit ignore l'identité. Rien n'en fuitait :
ces libellés n'étaient lus que par du débogage. Mais **rien ne l'aurait signalé non plus**,
l'invariant I7 ne surveillant qu'`information_state_string`. Un dos est désormais dit dos,
situé dans sa zone et numéroté par son rang parmi les cartes de même apparence encore en jeu
— le rang étant ce qui empêche de rouvrir le défaut 7 en anonymisant. Mesures sur `7eabe3b` :
**596 tests verts, 127/127/127, 143 invariants, 8/8 critères, 643 instructions et 0
manquante, 19 mutations sur 19 détectées**, `ruff` propre. **Le nouveau verdict appartient à
l'auditeur** : ce paragraphe constate la correction, il ne la valide pas.

**Audit du résultat.** Deux mesures méritent d'être distinguées de tout le reste :

1. **Deux des neuf défauts vivaient à 100 % de couverture d'instructions.** Le défaut 2 était
   une branche exécutée à chaque appel mais jamais avec l'argument omis ; la régression du
   tour 2 était un refus exécuté mais jamais dans le cas où il devait rendre une valeur. La
   couverture d'instructions **ne peut pas** les voir. La couverture de **branches** est le
   seul changement d'instrument qui les aurait signalés.
2. **La preuve que les phases 2 et 3 sont débloquées a été faite, pas déduite.** L'auditeur a
   fait tourner de vrais consommateurs OpenSpiel de bout en bout sur `rapide-2j` :
   `mcts.MCTSBot` — partie entière, 38 coups, gains [1.0, −1.0] — et
   `rl_environment.Environment` — 14 pas, rewards [1.0, −1.0].

**Décision.** **Go.** Verdict **ACCEPTÉ SOUS RÉSERVE**. La phase 0 est close.

~~Une réserve reste ouverte et demande un arbitrage : `action_to_string` nomme la famille et
le rôle d'un **Espion caché**.~~ **Arbitrée et corrigée le 17/08, avant la phase 1** plutôt
qu'avant la phase 3 : l'invariant I7 ne couvrant qu'`information_state_string`, aucun test
n'aurait signalé le jour où une interface ou une trace d'entraînement se serait mise à lire
ces libellés. Détail au paragraphe « la réserve unique est levée » ci-dessus. **I7 n'a pas été
étendu à `action_to_string`** — ce serait modifier la spécification, et c'est un arbitrage
distinct, resté ouvert.

**Impact plan.** Aucun. La phase 1 s'ouvre sans modification. Trois enseignements de méthode
sont à reporter dans les phases suivantes :

- **La section « Incertain » d'un compte rendu désigne le défaut suivant.** Le constructeur
  avait écrit « SUPPOSÉ que la sérialisation passerait » ; c'était faux, et c'est devenu le
  défaut 9. Un `SUPPOSÉ` dans un compte rendu est un test qui manque.
- **Un arbitrage mal formulé produit une régression.** La consigne disait « la substitution
  disparaît » là où elle aurait dû dire « la substitution est validée » — d'où le défaut R1.
  Un arbitrage doit énoncer ce qui doit **continuer de marcher**, pas seulement ce qui doit
  échouer.
- **Le harnais standard de l'écosystème trouve ce que la suite maison ne cherche pas.**
  Débloquer `random_sim_test` a produit un défaut réel à la première exécution.

---

## [2026-08-15] Pré-phase 0 — Conformité des instances aux règles

**Hypothèse.** Les instances CFR implémentent les règles de Courtisans.

**Instrument.** Lecture croisée instances / `regles.md` / `app/jeu.py`, puis 20 000 playouts
pour quantifier l'impact des écarts trouvés.

**Résultat.**

- **N1** — le meurtre de l'Assassin est obligatoire alors qu'il est facultatif :
  **20.0 %** des résolutions où refuser serait strictement meilleur, perte moyenne
  **1.34 point**, **38.1 %** d'auto-mutilations forcées.
- **N3** — tours inégaux : P0 joue 2 tours (6 cartes), P1 un seul (3 cartes). Idem en 2.1d.
- **N2** — `app/jeu.py::is_done` teste la fin de partie joueur par joueur : à 4 joueurs, les
  deux premiers de l'ordre jouent un tour de plus.

**Audit.** L'ordre de pose intra-tour, suspecté, a été vérifié **sans effet** (0 cas sur 24) :
ce n'était pas un écart. Les mesures d'impact sont myopes (score si la partie s'arrêtait là),
donc indicatives et non exactes — mais l'ordre de grandeur suffit à conclure.

**Décision.** Hypothèse **rejetée**. L'oracle à 0.001783 est l'équilibre exact d'un jeu qui
n'est pas Courtisans.

**Impact plan.** La phase 0 devient bloquante pour tout le reste. Les verdicts des briques
2.1c et 2.1e sont suspendus jusqu'à mesure de la fréquence du passe à l'équilibre (P2.5).

---

## [2026-08-15] Pré-phase 0 — Que mesure le plafond à 0.190 ?

**Hypothèse.** Le chiffre 0.190 mesure la qualité de Deep CFR sur l'instance 2.1e.

**Instrument.** Lecture de `deep_cfr_mini.py`, puis simulation de la collecte de
strategy-memories (sémantique OpenSpiel `_traverse_game_tree`) au budget exact du run
(20 itérations × 2000 traversées).

**Résultat.** `DCFR_MEASURE_NET` vaut 0 par défaut : la métrique est
`buffer_exploitability`, qui **retourne la politique uniforme** pour tout info-set absent du
buffer. Couverture au budget du run : **295 176 / 455 092 = 64.9 %**. Au moins **35 %** des
info-sets jouent au hasard dans la stratégie notée 0.190.

**Audit.** La simulation utilise une politique uniforme, qui **maximise** l'exploration : le
chiffre réel est plus bas, pas plus haut. C'est donc une borne supérieure, à confirmer par
lecture du log réel (P3.0, dix secondes). Aux briques 1 à 2.1d la couverture était totale
(236/236, 12 484/12 484) — la métrique y était honnête, et c'est ce qui rend le 0.190 non
comparable.

**Décision.** Hypothèse **rejetée**. Le 0.190 n'est pas comparable aux chiffres des briques
précédentes.

**Impact plan.** La conclusion « mur de variance à 455k info-sets → ESCHER/DREAM » du
`rapport_expert.md` §34 est **suspendue**. Le diagnostic est rouvert en phase 3, avant toute
phase 4.

---

## [2026-08-15] Pré-phase 0 — L'encodage perd-il de l'information ?

**Hypothèse.** La représentation d'un info-set n'est pas injective : deux info-sets
distincts au sens des règles produisent le même tenseur, ce qui plafonnerait
l'exploitabilité quel que soit l'algorithme.

**Instrument.** Traversée exhaustive des **8 250 001** états de l'instance combo. Trois
contrôles : collisions tenseur → string, non-déterminisme string → tenseur, et cohérence des
actions légales au sein d'un info-set.

**Résultat.**

```
info-sets (strings distinctes) : 475 000   (P0 455 092 + P1 19 908)
tenseurs distincts             : 475 000
2 info-sets → 1 tenseur                       : 0
1 info-set → 2 tenseurs                       : 0
actions légales incohérentes dans un info-set : 0
```

**Audit.** Le harnais a d'abord été validé sur l'instance 2.1c (123 921 états), dont le
résultat correspond à la documentation existante, avant d'être appliqué à 2.1e. Le troisième
contrôle est nouveau — `check_combo.py` ne le faisait pas — et c'était le risque réel, la
string ne codant que la zone-clé de l'assassin en phase de ciblage.

**Décision.** Hypothèse **rejetée**. L'encodage n'est pas la cause du plafond.

**Impact plan.** Réoriente l'investigation vers la métrique et la conformité aux règles.
Les tests d'injectivité deviennent C13 et C14 de la suite de conformité, à exécuter
automatiquement.
