# Courtisans — document racine

**Point d'entrée du projet. Où on en est, ce qui est vrai, ce qu'on fait ensuite, et dans quel document c'est écrit.**

Mis à jour le 30/09/2026 (bandeau ci-dessous) ; le reste du document décrit l'état du 21/08/2026.

> **État au 30/09/2026.** Une seule branche, `main` ; les anciennes sont archivées en tags
> `archive/*` (voir [09_reprise.md](09_reprise.md) §0). L'IA se construit dans `experiences/`
> : **[../experiences/README.md](../experiences/README.md)** est le point d'entrée côté IA,
> avec l'état, les commandes et la lecture des chiffres. Acquis : une cible auxiliaire
> « statut final des familles » **plus l'augmentation par permutation des familles** : un réseau
> qui bat `meilleur.pt` en duel (+0,05 à +0,09, 5 graines) et 2 greedys de +0,50 à +0,56. Le journal du 30/09 en tête de [06](06_journal_decisions.md) détaille
> les cycles 1 à 4 ; les sources consultées sont dans [10_sources.md](10_sources.md).
> Les sections 1 à 5 ci-dessous sont l'état d'**août** (phases 0 à 3) et gardent leur valeur
> historique : elles ne disent plus « ce qu'on fait maintenant ».

> **Tu reprends le projet sur une autre machine ou un autre compte ?** Lis
> **[09_reprise.md](09_reprise.md)** avant ce document. Il contient ce qui n'est écrit nulle
> part ailleurs : comment travailler avec l'humain, l'état exact des six branches, ce qui
> attend un feu vert, et les cinq erreurs déjà commises par le pilote.

---

## 1. Le projet en une page

Courtisans est un jeu de cartes à information imparfaite. L'objectif est une **IA forte,
jouable dans l'interface, d'abord à 3 joueurs**, puis 2, puis 4.

| | |
|---|---|
| Jeu | 6 familles × 5 rôles × 3 exemplaires = 90 cartes |
| Moteur | `courtisans/` — **réécrit et conforme**, 2 à 4 joueurs, adaptateur OpenSpiel. L'ancien `app/jeu.py` n'est pas dans ce dépôt |
| Interface | Streamlit, adversaire par défaut = greedy PIMC |
| Approche IA | famille CFR à 2 joueurs ; méthode de population au-delà |
| Vérité-terrain | exploitabilité à 2 joueurs ; Elo contre pool au-delà |

**Historique en une phrase.** Une première approche AlphaZero/MCTS a été abandonnée sur
résultat négatif documenté — la valeur d'un état d'information n'est pas un scalaire bien
défini en information imparfaite. Le pivot vers CFR/Deep CFR a validé cinq briques
successives, puis a buté sur un plafond d'exploitabilité à 2.1e.

**État au 15/08/2026 : campagne CFR suspendue.** L'audit a établi que le plafond invoqué
repose sur une métrique faussée, et surtout que **les instances d'entraînement
n'implémentent pas les règles du jeu**. Le projet reprend par une phase de mise en
conformité.

---

## 2. Les documents, dans l'ordre de lecture

```mermaid
flowchart TD
  I[00_index<br/>ce document] --> R[01_specification_regles<br/>ce que le jeu EST]
  R --> A[02_audit_conformite<br/>ce que le code FAIT<br/>et pourquoi on reecrit]
  A --> M[03_specification_moteur<br/>QUOI construire]
  M --> C[04_conventions_code<br/>COMMENT construire]
  C --> PR[prompts/01_moteur_construction<br/>le prompt a coller]
  PR --> AU[prompts/02_moteur_audit<br/>conversation DISTINCTE]
  AU --> AC[07_protocole_audit_croise<br/>+ 08_modele_compte_rendu]
  M --> P[05_protocole_experimental<br/>comment on AVANCE ensuite]
  P --> J[06_journal_decisions<br/>ce qu on a DECIDE]
  I --> H[rapport_expert<br/>l historique complet]
```

> **Ce document n'est pas le point d'entrée de Florian.** Le document qui dit quoi faire,
> quel prompt coller et dans quelle conversation, c'est **[../PILOTE.md](../PILOTE.md)**.
> Celui-ci est l'index du corpus de référence, consultable par toi et par les agents.

| Document | Répond à | Statut |
|---|---|---|
| **[01_regles.md](01_regles.md)** | Quelles sont les règles exactes, à 2, 3 et 4 joueurs ? | **À valider** — arbitrage humain requis, §11 |
| **[02_audit_conformite.md](02_audit_conformite.md)** | Le code respecte-t-il ces règles ? Que garde-t-on ? | Établi |
| **[03_specification_moteur.md](03_specification_moteur.md)** | Quoi construire : architecture, API, invariants, critères d'acceptation | Établi |
| **[04_conventions_code.md](04_conventions_code.md)** | Comment construire, et pourquoi chaque règle | Établi |
| **[../prompts/01_moteur_construction.md](../prompts/01_moteur_construction.md)** | Le prompt à coller dans une conversation neuve | **Prêt** — après validation de 01 |
| **[../prompts/02_moteur_audit.md](../prompts/02_moteur_audit.md)** | Le prompt d'audit, pour une conversation distincte | **Prêt** |
| **[05_protocole_experimental.md](05_protocole_experimental.md)** | Comment on avance ensuite, avec quels critères d'arrêt | Établi |
| **[06_journal_decisions.md](06_journal_decisions.md)** | Qu'a-t-on testé, trouvé, décidé, et quand ? | Vivant |
| **[07_protocole_audit_croise.md](07_protocole_audit_croise.md)** | Comment un agent en audite un autre : contrôles A1-A7, verdicts | Établi |
| **[08_modele_compte_rendu.md](08_modele_compte_rendu.md)** | Le format imposé de tout compte rendu d'agent | Établi |
| [09_reprise.md](09_reprise.md) | Par où reprendre, état des branches et des tags, règles de travail | **À jour au 30/09** (§0) |
| [10_sources.md](10_sources.md) | Veille bibliographique : ce qui a été lu, niveau de lecture | Vivant |
| [../experiences/README.md](../experiences/README.md) | L'IA : carte du dossier, reproduction, lecture des chiffres | **À jour au 30/09** |
| `rapport_expert.md` | Historique complet, brique par brique (2 695 lignes) | Archive — dans le tag `archive/cfr-pivot` (`git show archive/cfr-pivot:rapport_expert.md`) |


> **(Historique, 15/08 — voir le bandeau du 30/09 pour l'état actuel.) Le dépôt est sur `main`, qui est figé au 26 mai.** Tout le travail CFR — `cfr/`,
> `rapport_expert.md`, `etat_des_lieux_et_roadmap.md` — est sur `origin/cfr-pivot`, qui
> contient l'intégralité de `main` plus 16 commits. Aucune divergence : le fast-forward est
> trivial. Il est bloqué par un `.git/index.lock` vide daté du 15/08 19h30 (point ouvert n° 5).

Les autres fichiers de `documentations/` (`architecture_technique`, `entrainement`,
`leviers_apprentissage`, `configuration`, `streamlit_app_spec`, `ameliorations`) sont des
archives de la période AlphaZero. Ils restent consultables mais ne font pas autorité.

---

## 3. Ce qui est établi, et avec quelle certitude

Trois niveaux, jamais confondus : **mesuré** (exécuté et lu), **déduit** (lu et raisonné,
non exécuté), **simulé** (reproduit indépendamment, pas observé sur le run réel).

| Fait | Niveau | Source |
|---|---|---|
| Le meurtre de l'Assassin est **obligatoire** dans les instances alors qu'il est facultatif | **Déduit** (lecture de `_legal_actions`) — impact **mesuré** : 20 % des résolutions, 1,34 pt, sur évaluation myope | [02](02_audit_conformite.md) §3 |
| Les tours sont **inégaux** dans les instances : P0 joue 2 tours, P1 un seul | **Mesuré** (exécution) | [02](02_audit_conformite.md) §4.1 |
| L'ordre de pose intra-tour est **sans effet** à 2 joueurs | **Mesuré** (0 cas sur 24) — non vérifié à 3 et 4 joueurs | [02](02_audit_conformite.md) §2.1 |
| La métrique d'exploitabilité joue **uniforme** sur les info-sets non couverts | **Déduit** (lecture de `buffer_exact_fn`) | [02](02_audit_conformite.md) §5 |
| La couverture du buffer plafonne à **64.9 %** au budget du run | **Simulé**, borne supérieure — la sémantique de traversée a été réimplémentée, pas observée. À confirmer par P3.0 (10 s) | [02](02_audit_conformite.md) §5 |
| Le goulot est **CPU mono-thread**, le GPU est inutilisé | **Mesuré** (débit) + **déduit** (`device="cpu"` en dur) | [02](02_audit_conformite.md) §6 |
| L'encodage info-set est **injectif** — 475 000 info-sets ↔ 475 000 tenseurs | **Mesuré** avec réserve — voir ci-dessous | [02](02_audit_conformite.md) §2.2 |
| La canonicalisation par symétrie des familles est **lossless** | Établi antérieurement, non revérifié | `rapport_expert.md` §31 |

**Réserve sur l'injectivité.** La traversée shardée utilisée sur l'instance combo emploie un
`setdefault` : une répétition du même info-set **à l'intérieur** d'un shard n'était pas
comparée. Seules les collisions **entre** shards étaient détectées. Le contrôle complet n'a
été exécuté que sur l'instance 2.1c (123 921 états, 0 collision). Sur 2.1e, l'absence de
collision inter-info-sets est solide ; la cohérence des actions légales au sein d'un info-set
est **partiellement vérifiée**. Ce contrôle devient l'invariant I9 du nouveau moteur, testé
automatiquement.

**Non vérifié.** Le comportement de `is_done` à 4 joueurs a été **déduit** d'une docstring,
présenté à tort comme mesuré, puis la vérification par exécution a produit un harnais faux
(`step()` ne lève pas sur assassin en attente, la partie s'arrêtait au premier tour). **Le
point reste ouvert** — sans conséquence, puisque le moteur est réécrit.

**Ce qui n'est plus établi.** La conclusion « mur de variance à 455k info-sets, donc
ESCHER/DREAM » du `rapport_expert.md` §34 est **suspendue** : elle repose sur un chiffre non
comparable aux briques précédentes. Le diagnostic est rouvert en phase 3.

---

## 4. Ce qu'on fait maintenant

Les durées ci-dessous sont des **temps d'exécution machine**, mesurés ou extrapolés de
mesures. Aucune estimation de temps de développement n'est donnée : elles ne seraient pas
fondées.

| Phase | Objet | Exécution | Bloquante |
|---|---|---:|---|
| **0** | ~~Moteur conforme réécrit~~ — **close le 17/08, audit croisé compris ; réserve unique levée le 17/08** : 596 tests verts, 8 critères d'acceptation atteints, 19 mutations sur 19 détectées, couverture 643/643. Verdict de l'auditeur : **ACCEPTÉ SOUS RÉSERVE**. | tests + couverture : 12 min 22 s | **oui** |
| **1** | ~~Instance d'entraînement~~ — **close le 18/08, audit croisé compris** : `entrainement-3j`, 4 familles, 5 rôles, 2 exemplaires, 3 joueurs, 40 cartes, **4 tours**. Les trois go/no-go tenus — 1 000/1 000 parties à `(4, 4, 4)` tours, 10/10 critères de non-dégénérescence, retournement R2 dans **96,00 % (960/1 000), IC99 [94,12 % ; 97,42 %]** contre un seuil de 33,3 %. 648 tests verts. Verdict de l'auditeur : **REJETÉ** puis **ACCEPTÉ SOUS RÉSERVE** — deux réserves mineures nommées au [journal](06_journal_decisions.md). | 1,6 ms/partie, 1,7 s pour 1 000 | **oui** |
| **2** | **Banc de test 2 joueurs** — instance symétrique + oracle CFR+ + métrique corrigée | oracle ~4 h | **oui** |
| **3** | **Diagnostic du plafond** — trancher entre les 3 hypothèses | P3.0 : 10 s · P3.1 : ~3 h · P3.2 : ~20 min GPU | **oui** |
| 4 | Algorithme — SD-CFR, puis ESCHER si besoin | run ~2 h | non |
| 5 | Passage à 3 joueurs — Elo contre pool | 1 000 parties appariées : ~1 h | non |
| 6 | 4 joueurs | idem | non |

**Aucun run individuel ne dépasse 4 h**, checkpoint toutes les 15 min. La phase 3 est la
plus rentable : elle commence par une lecture de log de dix secondes qui peut clore le
diagnostic.

Détail, hypothèses, critères go/no-go : [05_protocole_experimental.md](05_protocole_experimental.md).

### La première chose à faire

1. ~~Valider [01_regles.md](01_regles.md)~~ — **fait**, les quatre arbitrages du §11 sont
   tranchés les 15 et 16/08.
2. **Fast-forward de `main` sur `cfr-pivot`**, et tag `alphazero-final` — sur l'ancien dépôt.
3. ~~Coller [../prompts/01_moteur_construction.md](../prompts/01_moteur_construction.md)~~ —
   **fait, les huit étapes.** Puis l'audit croisé — action 4 — qui a rejeté une
   première fois, puis accepté sous réserve après deux tours de correction.
   **État final : 596 tests verts, les 8 critères d'acceptation atteints,
   19 mutations sur 19 détectées, couverture 643/643.** Neuf défauts trouvés et
   corrigés, plus la réserve unique de l'auditeur — le libellé qui nommait une carte
   cachée — levée le 17/08. Voir l'entrée du 17/08 au
   [journal](06_journal_decisions.md).
4. ~~Écrire les prompts de la phase 1~~ — **fait**, construction et audit. La phase 1
   est **close le 18/08** : l'instance `entrainement-3j` est validée, les trois
   go/no-go tenus, 648 tests verts. L'audit a **rejeté** au premier tour — un
   « 0 sur 1 000 » qui ne mesurait pas sa propre phrase, contredit par un test du
   même livrable — puis **accepté sous réserve** après correction. Voir l'entrée du
   18/08 au [journal](06_journal_decisions.md).
5. ~~Écrire les prompts de la phase 2~~ — **fait**,
   [../prompts/08_phase2_construction.md](../prompts/08_phase2_construction.md) et
   [../prompts/09_phase2_audit.md](../prompts/09_phase2_audit.md). La phase 2 mesure le
   terrain avant d'entraîner quoi que ce soit : avantage de siège, variance du score,
   winrate du greedy, et **ligne de base des comportements B1–B7**. Trois trous du
   protocole y sont signalés à l'agent plutôt que découverts par lui : **le greedy
   n'existe pas dans ce dépôt** — la version de `cfr-pivot` importe le moteur non
   conforme et un `_pick_target_heuristic` qui ne sait pas refuser de tuer, donc B4
   serait inmesurable ; **B1–B7 ne sont pas des définitions mesurables**, exactement le
   trou de « retournement » en phase 1 ; et le **seuil de 38 % de l'avantage de siège ne
   discrimine rien** — à 10 000 parties il est à 9,9 erreurs-type de l'attendu, si bien
   qu'un avantage de 35 %, statistiquement certain, passerait sans être signalé. Un point
   s'y ajoute, sorti de l'audit de la phase 1 : la fréquence des retournements
   qu'**aucun** siège ne voit — ~7 % des parties — est un **plafond de ce que B1 peut
   mesurer**, et la ligne de base doit être lue en la retranchant.

6. ~~Lancer la phase 2~~ — **fait. La phase 2 est close le 19/08, verdict ACCEPTÉ au
   troisième tour d'audit.** Trois tours, 75 contrôles hostiles, cinq défauts trouvés dont
   un bloquant, **977 tests verts, 0 rouge**. Les quatre lignes de base sont établies et
   citables par les phases suivantes, à trois conditions écrites dans le rapport lui-même.
   Voir l'entrée du 19/08 au [journal](06_journal_decisions.md).
7. ~~Boucher les trous du protocole~~ — **fait le 20/08.**
   [05_protocole_experimental.md](05_protocole_experimental.md) porte désormais un **§0
   normatif** — format d'une entrée de journal, et les règles d'écriture d'un chiffre tirées
   des fautes réelles des phases 0 à 2 —, un **erratum sur la phase 1** qui définit enfin
   « retournement », « distribution non dégénérée » et « refuser de tuer est possible », un
   **erratum sur la phase 2** qui nomme les cinq défauts de son propre texte, et des **seuils
   de phases 3, 4 et 5 réécrits** : le « > 55 % » était une intuition de jeu à deux joueurs,
   alors qu'à trois la valeur nulle est 33,33 %.
8. ~~Écrire les prompts de la phase 3, puis la lancer~~ — **fait. La phase 3 est close le
   21/08, verdict ACCEPTÉ SOUS RÉSERVE au troisième tour.** L'agent PPO est **battu par le
   greedy** et **il apprend** : les deux sont établis. Deux tours de REJET, 97 contrôles
   hostiles, 1 172 tests verts. Voir l'entrée du 21/08 au
   [journal](06_journal_decisions.md).
9. **Écrire les prompts de la phase 4.** Premier travail : étendre le périmètre des mutations
   à `mesure/` et au reste de `agents/`. Puis le premier levier, **la tête de valeur**.

---

## 5. Les décisions structurantes déjà prises

| Décision | Choix | Pourquoi |
|---|---|---|
| Repartir de zéro ? | **Le moteur est réécrit ; le dépôt et la documentation sont conservés** | Le moteur ne peut pas être certifié : seules ~30 % de ses 719 lignes ont été auditées, et chaque relecture a révélé un écart de plus (N1, N2, N3). Relire 719 lignes contre la spec coûte le même temps que les réécrire **tests en premier** — à coût égal, la réécriture donne un moteur certifié par construction. On garde la documentation (5 380 lignes), `greedy_bot.py` comme référence de comportement, et l'infra oracle. |
| 3 joueurs d'abord ? | **Oui, directement.** Le juge est le greedy PIMC en parties appariées, pas l'exploitabilité. | À 3 joueurs il n'y a pas d'équilibre de Nash unique : CFR perd ses garanties et l'exploitabilité cesse d'être une cible. Voir [05](05_protocole_experimental.md) §1. |
| Quel algorithme après le diagnostic ? | **SD-CFR avant ESCHER** | SD-CFR attaque exactement le composant diagnostiqué, à une variable près. [03](05_protocole_experimental.md) §4 |
| Que faire du code AlphaZero ? | **Tag `alphazero-final` puis suppression** | Le résultat négatif reste consultable, le dépôt redevient lisible. [02](02_audit_conformite.md) §7.2 |

---

## 6. La règle de conduite

Toute expérience passe par la boucle en huit étapes du protocole
([03](05_protocole_experimental.md) §0), dont quatre règles non négociables :

1. **L'hypothèse s'écrit avant l'expérience** — falsifiable, avec le résultat attendu dans les deux cas.
2. **Pas de tunnel** — on déclare à l'avance la durée à laquelle la métrique devient décisive ; si on ne sait pas le dire, on redessine l'expérience. Plafond : 4 h par run en phase exploratoire.
3. **Le résultat est audité avant d'être cru** — mesure-t-il ce qu'on croit ? sur quel support ? comparable au précédent ?
4. **Le plan est challengé à chaque tour** — un résultat peut rendre les phases suivantes caduques.

La règle 3 est celle qui manquait : le plafond à 0.190 jouait uniforme sur 35 % du jeu, et
personne ne l'a vu pendant toute une brique.

---

## 7. Points ouverts

| # | Question | Bloque |
|---|---|---|
| 3 | Instance 2 joueurs : symétrique **avec** pioche coûte 369 600 donnes contre 924 **sans**. Lequel des deux mécanismes sacrifie-t-on ? | Phase 2 |
| 5 | `.git/index.lock` bloque les commits depuis le 15/08 19h30 — **sur l'ancien dépôt** ; celui-ci n'est pas encore un dépôt git | Versionnement |
| 7 | `app/greedy_bot.py` et `cfr/solve_mini.py` ne sont pas dans ce dépôt — **normal**, ils n'appartiennent pas à la phase moteur et arriveront pour les phases 2 et 3 | Phases 2 et 3 |
| 8 | **La canonicalisation par permutation des familles n'est pas implémentée.** Elle exige une traduction de l'espace d'actions que le §4 de [03](03_specification_moteur.md) ne définit pas ; la moitié du mécanisme produirait un agent qui croit poser une carte et en pose une autre. Étape à part entière, spécification d'abord. | Phase 3 |
| 9 | **L'encodage par cible de la phase de ciblage n'est pas écrit.** Sa forme dépend du réseau qui le consomme. | Phase 3 |

**Fermés le 16/08 :**

| # | Question | Réponse |
|---|---|---|
| 1 | Validation de la spec de règles | Tranchée par l'auteur les 15 et 16/08, §11 de [01](01_regles.md) |
| 2 | À 3+ joueurs, peut-on poser deux cartes chez le même adversaire ? | **Non** — §3.2 et R1 de [01](01_regles.md) : structure fixe, une seule carte part chez un adversaire |
| 4 | Confrontation à la règle officielle du jeu de plateau | **Sans objet** — R7 : variante de l'auteur, sa validation fait autorité |
| — | Reproduction des instances historiques `mini`, `assassin`, `redeal`, `combo` | **Supprimée.** Elles violent les règles et sont non constructibles sous les planchers du §8. Remplacées par `entrainement-3j`, `complet-3j`, `complet-2j` — voir [03](03_specification_moteur.md) §3 |
| — | Nœuds de chance | **Explicites dans l'adaptateur OpenSpiel**, pas dans le cœur. `reset(seed)` reste le mécanisme de déterminisme — voir [03](03_specification_moteur.md) §4 |
