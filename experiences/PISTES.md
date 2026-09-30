# Pistes pour faire monter le score — 27/09/2026 au soir

Ce document part de **ce qui a été mesuré** le 27/09 ([REVUE_CRITIQUE.md](REVUE_CRITIQUE.md)
§5), et non d'intuitions libres. Chaque piste dit pourquoi elle devrait marcher, comment la
mesurer, ce qu'elle coûte, et ce qui l'infirmerait. Elles sont classées par rapport
gain espéré / coût.

## Point de départ : ce que les mesures disent

| Constat mesuré | Ce qu'il implique |
|---|---|
| La meilleure IA fait **+0,289** contre 2 greedys ; 48,8 % de victoires seules | la marge existe, elle n'est pas écrasante |
| **60 %** de son avance vient du départage des égalités du greedy, **40 %** de ses écarts volontaires en milieu de partie | le « sens stratégique » propre à l'IA est encore mince |
| La valeur apprise prédit mal : R² ≈ 0,05 à 0,09 ; un réseau plus gros n'aide pas | **la cible (gagné / perdu) est trop bruitée** ; c'est la limite n° 1 |
| TD(λ) a débloqué le plateau | tout ce qui réduit le bruit de la cible paie |
| Calcul de fin de partie : **+0,088** (32 mondes), sature au-delà | l'exactitude en fin de partie paie, mais seulement sur le dernier tour |
| Recherche courte en milieu de partie : rien de mesurable | chercher sur une valeur bruitée ne sert à rien |
| Le moteur Python plafonne à ~55 parties/s | tout ce qui marche demande plus de parties |

**Le fil rouge : la qualité du signal d'apprentissage, puis la quantité de parties.**

---

## 1. Le « greedy probabiliste » — apprendre le **statut final des familles**

> **FAIT le 30/09** (cycles 1 et 3 du journal). Le calcul du greedy probabiliste seul est moins bon que prévu (R² −0,08), mais la tête de statuts comme **cible auxiliaire** fait passer la valeur de +0,178 à +0,288, et jusqu'à +0,455 avec 108 000 parties. Voir `experiences/statuts.py`.

*La piste la plus alignée avec la lecture du jeu par son auteur, et celle que je mettrais en
premier.*

**L'idée.** Le greedy compte ses points avec le statut **actuel** des familles, comme si la
partie s'arrêtait là. Le bon joueur, lui, raisonne sur leur statut **final** : « A est à +1,
mais il y a deux dos en Disgrâce, donc elle est peut-être nulle » ; « B est à −3, elle est
perdue, inutile de la défendre ». Or le score final se calcule exactement à partir de deux
choses : le statut final de chaque famille, et les cartes posées dans chaque domaine.

On apprend donc au réseau à prédire, pour chaque famille, **la probabilité qu'elle finisse
en Lumière, Indifférente ou Obscurité**. Le score espéré de chaque joueur s'en déduit **par
calcul**, sans l'apprendre :

```
E[score du joueur j] = Σ_familles  valeur des cartes de f dans le domaine de j
                                    × ( P(Lumière_f) − P(Obscurité_f) )
```

C'est littéralement **le greedy, mais avec des signes probabilistes au lieu des signes
actuels**. On peut l'utiliser exactement comme le greedy (maximiser l'écart espéré),
départager ses égalités, et le brancher dans le calcul de fin de partie.

**Pourquoi ça devrait marcher.** C'est la réponse directe à la limite n° 1. Une partie donne
**une** issue gagné / perdu, mais **six** statuts de famille (quatre dans l'instance
réduite) : six fois plus de signal, et un signal **beaucoup moins bruité**, parce que le
statut d'une famille dépend de peu de cartes alors que la victoire dépend de tout. Et c'est
interprétable : on peut afficher « l'IA pense que B est perdue à 85 % ».

**Comment le mesurer.**
1. Ajouter aux données, pour chaque vue, le statut final des familles (trois classes par
   famille). Coût nul, c'est déjà dans l'état terminal.
2. Mesurer la précision de la prédiction de statut par tour restant. On attend une très
   bonne précision en fin de partie, correcte au milieu.
3. Agent « greedy probabiliste » contre 2 greedys et contre `meilleur.pt`, sur les donnes
   appariées habituelles.
4. Variante : la tête de statuts comme **tête auxiliaire** du réseau de valeur, dont elle
   régularise l'apprentissage.

**Ce qui l'infirmerait.** Si les statuts finaux sont aussi imprévisibles en milieu de partie
que la victoire, le gain se limiterait à la fin de partie, déjà couverte par le §3.

**Coût.** Une journée. Aucune dépendance au moteur rapide.

---

## 2. La fin de partie exacte **dans l'entraînement** — propager la certitude vers le début

**L'idée.** Aujourd'hui, le calcul de fin de partie ne sert qu'au moment de jouer (+0,088).
Avec TD(λ), la valeur d'une position apprend de la valeur de la position suivante. Si les
**dernières positions** des données d'entraînement portent des valeurs quasi exactes,
calculées par simulation sur 32 mondes, cette exactitude **remonte** tour après tour vers le
milieu de partie. C'est l'intuition « partir de la fin, là où l'on sait calculer »,
appliquée à l'apprentissage.

**Comment.** Pour chaque partie d'auto-jeu, remplacer la cible TD des positions du dernier
tour par la moyenne de leurs 32 simulations, qui sont déjà calculées quand l'hybride joue.

**Coût.** Élevé en Python : la fin de partie coûte ~25 fois une décision normale, soit une
génération 5 à 10 fois plus lente. **Devient naturel avec le moteur rapide (§4).**

---

## 3. L'IA jouable par défaut = `meilleur.pt` + fin de partie à 32 mondes

> **MIS À JOUR le 30/09** (cycle 4) : l'agent de référence est désormais `statuts_s3_e2.pt` + fin de partie (`statuts=True`) : +0,470 contre 2 greedys, +0,046 [+0,001 ; +0,093] contre `meilleur.pt`.

Déjà mesuré : +0,088 contre la meilleure IA seule, établi. C'est la meilleure IA **pour
jouer** aujourd'hui, pour quelques secondes par coup et seulement au dernier tour. À exposer
comme agent de référence pour l'interface que tu brancheras plus tard :
`experiences.fin_de_partie:fin_de_partie` avec `tours_fin=1, nb_mondes=32, rollout='valeur'`.

---

## 4. Le moteur rapide (Rust) — ce qui débloque 2, 5 et 6

**Pourquoi.** Toutes les pistes qui ont marché demandent plus de parties ; toutes celles qui
sont trop chères (fin de partie dans l'entraînement, recherche profonde) le sont à cause du
moteur. Un facteur 20 à 50 est réaliste.

**Comment, sans risque.** Porter règles et tenseur en Rust derrière `pyo3`, puis exiger :
(a) la suite de conformité C1–C18 rejouée sur le nouveau moteur — le dépôt sait déjà faire
tourner la même suite sur plusieurs moteurs (`COURTISANS_MOTEUR`) ; (b) l'égalité bit à bit
des tenseurs et des parties, comme `experiences/test_rapide.py` le fait déjà pour le tenseur
rapide. **En attente de ton accord** : installation de `rustup`, second langage dans le
dépôt.

---

## 5. Les Espions — inférence et bluff

**Inférence.** Quand l'IA simule des mondes, elle tire aujourd'hui les Espions adverses
**uniformément**. Or un joueur ne pose pas un Espion n'importe où : s'il a mis un dos en
Disgrâce, c'est plus probablement une famille qu'il veut faire baisser. Pondérer chaque
monde par la probabilité que l'adversaire ait joué ses coups passés avec ces cartes-là, sous
le modèle de politique appris, est le gain classique du PIMC au Bridge et au Skat. Cela sert
d'abord la fin de partie (§3), où l'identité des Espions est la dernière incertitude.

**Bluff.** Mesure à faire : l'IA pose-t-elle des Espions là où ils créent le doute ? Le
critère B5 des règles (« se méfier des Espions ») et son symétrique se mesurent en auto-jeu.
Rappel : **on ne peut pas bluffer le greedy**, qui compte un dos pour zéro. Le bluff ne
s'apprend que contre des adversaires qui voient les dos, d'où l'importance de l'auto-jeu
dans la ligue.

---

## 6. Recherche profonde (ISMCTS) et itération experte complète

La recherche courte n'a rien donné parce qu'elle s'arrête sur une valeur bruitée. Une
recherche qui va **jusqu'au bout** de la partie, guidée par la politique apprise (ISMCTS,
ou PIMC complet), n'a plus ce défaut, et la fin de partie montre que ça paie. Elle coûte
trop en Python aujourd'hui. Avec le moteur rapide : la recherche joue, le réseau distille
la recherche, on recommence. C'est la boucle d'AlphaZero, adaptée aux cartes cachées.

---

## 7. Le signal et les données — réglages à faible coût

- **Moins de vues par partie, plus de parties.** Les ~100 vues d'une partie partagent une
  seule issue : en garder une sur trois, tirée au hasard, coûte moins de calcul et
  décorrèle les données.
- **λ plus bas** (0,5 → 0,3) combiné au retrait des vieilles données Monte-Carlo. Le run
  `iteration8`, en cours, teste le second point.
- **Des cibles denses en plus du gain** : écart de score final, scores des trois joueurs,
  statuts des familles (§1). Plus il y a de signal par partie, mieux c'est.

---

## 8. Le juge

- **Plus de donnes par verdict.** Les gains entre générations proches (+0,02 à +0,05) sont
  sous le seuil de détection de 450 parties : le gardien accepte ou rejette parfois sur du
  bruit. Passer à 900 parties contre la courante.
- **Corriger la malédiction du gagnant** du gardien : remesurer la courante sur des donnes
  neuves au lieu de prendre son meilleur score passé comme plancher.
- **Un classement Elo / TrueSkill à trois joueurs** sur toute la ligue, mis à jour à chaque
  génération, plutôt que trois chiffres séparés.
- **L'humain.** Le vrai juge final : des parties contre toi, journalisées, pour voir où
  l'IA joue « bizarrement ».

---

## Ordre proposé

1. **Greedy probabiliste / statuts finaux (§1)** : le meilleur rapport gain / coût, aucune
   dépendance, et interprétable.
2. **Réglages du signal (§7)** et **juge plus fin (§8)** : quelques heures, en tâche de fond.
3. **Moteur rapide (§4)**, si tu donnes ton accord. Il débloque ensuite **§2, §5 et §6**,
   c'est-à-dire la fin de partie apprise, l'inférence des Espions et la recherche profonde.
