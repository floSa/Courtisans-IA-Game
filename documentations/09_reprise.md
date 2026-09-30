# Reprise — à lire en premier sur une machine ou un compte neuf

Ce document existe pour une raison précise : le 19/08/2026, le travail a changé de machine et
de compte. Tout le reste du projet est dans le dépôt et se relit. **Ce fichier contient
uniquement ce qui n'existait nulle part ailleurs** — dans la mémoire d'un assistant, dans des
conversations, dans la tête de quelqu'un.

Si tu reprends le pilotage : lis ce document, puis
[00_index.md](00_index.md), puis [06_journal_decisions.md](06_journal_decisions.md).

---

## 0. État au 30/09/2026 — à lire avant tout le reste de ce document

**Il n'y a plus qu'une branche : `main`.** Le 30/09/2026, `reprise-iteration-experte` a été
fusionnée dans `main` (1 312 tests verts après fusion), et toutes les anciennes branches ont été
**archivées sous forme de tags** puis supprimées. Rien n'est perdu : chaque tag pointe vers le
dernier commit de sa branche.

| Tag (`git show archive/<nom>`) | Ce que c'était |
|---|---|
| `archive/main-24-08` | `main` avant la fusion (phase pilote, 24/08) |
| `archive/phase-4-tete-de-valeur` | phase 4, tête de valeur (27 commits, dernier le 26/09) ; hypothèse réfutée avant entraînement, voir le journal du 24/08 |
| `archive/audit-phase-3`, `archive/audit-phase-3-tour-2`, `archive/audit-phase-3-tour-3` | les trois tours d'audit croisé de la phase 3 |
| `archive/phase-3-premier-agent` | le premier agent entraîné (PPO), déjà dans l'historique de `main` |
| `archive/cfr-pivot` | l'ancien travail CFR (53 commits) : source du plafond à 0,190 et de l'oracle combo cités par le journal |
| `archive/old_version` | l'ancien projet RL (38 commits, AlphaZero/MCTS) |

Pour relire une ancienne branche : `git checkout archive/cfr-pivot` (sans créer de branche), ou
`git log archive/cfr-pivot`.

**Le projet a changé de nature depuis le 27/09.** Les phases 0 à 4 (moteur conforme, protocole
pilote/audit croisé) ont produit le moteur et les mesures de référence ; l'IA se construit
désormais dans `experiences/`, en régime exploratoire (essais courts, seuils écrits avant la
mesure, une entrée de journal par cycle). **Point d'entrée : [../experiences/README.md](../experiences/README.md).**
Les sections 1 à 8 ci-dessous décrivent le protocole pilote d'août (conversations de
construction et d'audit) : elles restent vraies pour le **moteur** et pour tout ce qu'on
voudrait affirmer de façon confirmatoire, mais ne sont plus le mode de travail courant.

**Ordre de lecture pour reprendre aujourd'hui :**
1. [../experiences/README.md](../experiences/README.md) : état, carte du dossier, commandes, comment lire un chiffre ;
2. les entrées du 30/09 en tête de [06_journal_decisions.md](06_journal_decisions.md) (cycles 1 à 4 et contrôle des graines) ;
3. [../experiences/PISTES.md](../experiences/PISTES.md) : ce qu'on teste ensuite ;
4. [10_sources.md](10_sources.md) : la veille bibliographique ;
5. seulement ensuite, le reste de ce document et [00_index.md](00_index.md).

**Règles de travail en vigueur** (données par l'auteur, à respecter) : français ; critique franche ;
carte blanche sur les essais ; commits réguliers **sans mention de Claude comme co-auteur** ;
synthèse courte à chaque résultat marquant ; dépôt toujours propre et documenté (« que
n'importe qui, IA ou humain, puisse reprendre »). Toute opération difficile à défaire
(pousser sur `main`, supprimer des branches distantes) se confirme d'abord.

**Ce qui attend l'accord de l'auteur :** le port du moteur en Rust (`rustup`, second langage dans
le dépôt) ; il débloquerait la fin de partie dans l'entraînement et la recherche profonde.

---

## 1. Comment travailler avec l'humain

**C'est le point le plus important de ce document, et il n'est écrit dans aucun autre fichier.**

Il s'est fâché deux fois pour la même raison : le manque de clarté.

- **Une idée par phrase, des mots parlants, pas de jargon.** « Rien n'attend de toi côté
  code » ne veut rien dire. « Le code est poussé sur ton GitHub » veut dire quelque chose.
- **Quand il demande une réponse courte, la donner.** Deux lignes, pas un bilan.
- **Numéroter toujours la conversation destinataire** d'un bloc à coller. Il travaille avec
  plusieurs conversations en parallèle et s'y perd sinon.
- **Ne jamais lui demander d'assembler des instructions.** Quand il faut coller quelque
  chose, lui envoyer **un seul** fichier, prêt à Ctrl+A / Ctrl+C.
- **S'il faut ajouter une phrase à un document, la modifier soi-même.** Ne jamais lui dire
  « ajoute cette phrase » — c'est le travail du pilote, pas le sien.
- **Ne pas lui donner un prompt qu'il n'a pas demandé**, et ne pas anticiper l'étape
  suivante avant que la réponse de l'agent soit arrivée.
- **Aucun trailer d'attribution dans les commits ni les PR.** Pas de `Co-Authored-By`, pas de
  mention de l'assistant. Quatre commits de juin en portent un ; ils sont sur
  `origin/cfr-pivot` uniquement, hors lignée.
- **Une preuve différée revient nommée, pas agrégée en un compte.** Si on annonce « tel test
  tombera », il faut dire *lequel*, pas « trois tests sont tombés ».
- **Tout ce qu'il doit donner à un agent porte un numéro ET un nom.** Exemple : « conversation
  n° 6 — Construction de la phase 3 ».
- **Petit message : écrit en entier dans la conversation, dans un bloc de code.** Gros document :
  dans `prompts/`, sous un nouveau numéro, et on lui donne le chemin. **L'un ou l'autre, jamais
  les deux à moitié.** Il n'a pas le temps de chercher dans le dépôt quel morceau copier.
- **Un seul bloc, à la fin, quand tout est vérifié.** Pas de commentaire d'avancement, pas de
  « je te reviens quand ». Le bloc final dit, pour **chaque** conversation ouverte, ce qu'elle
  doit recevoir — ou explicitement qu'elle n'attend rien. Il se termine par **TÂCHE FINIE** ou
  par la consigne suivante. Un message qui n'est ni l'un ni l'autre le laisse sans rien à faire.
- **Quand un agent dit qu'il fait un travail qu'on ne lui a pas donné, s'arrêter immédiatement.**
  Le 21/08, la conversation d'audit a ouvert son compte rendu par « le §5 de `07` compte un
  défaut corrigé par l'auditeur comme disqualifiant ; vous avez tranché et je corrige ». Le
  prompt de corrections lui avait été collé par erreur à la place de la conversation de
  construction. **Le pilote a lu la phrase et a continué**, et l'audit croisé a perdu son
  indépendance pour tout un tour. Une phrase d'agent qui décrit un rôle qu'on ne lui a pas
  attribué est une alerte, pas une formalité.
- **Tout bloc final porte une ESTIMATION, elle regarde DEVANT, et elle se donne en HEURE DE
  MONTRE.** Exigé par Florian les 24/08/2026. Première formulation le matin : « c'est
  insupportable de partir pour dix heures sachant qu'à chaque fois on te dit deux heures ».
  Correction le soir, et elle annule la moitié de la règle : **« Je m'en fous des durées qui
  sont passées. Ce qui m'intéresse, c'est les durées à venir, pouvoir estimer parce que j'ai
  envie d'éteindre mon PC de temps en temps. »**

  Le besoin n'est pas un bilan, c'est une **décision** : peut-il éteindre sa machine, et à
  quelle heure. Une durée l'oblige à faire l'addition lui-même ; une heure de montre, non.

  Une estimation conforme porte donc :
  1. **L'heure à laquelle il pourra éteindre**, en clair, sur la première ligne. Pas une durée.
  2. **Le prochain point d'arrêt, nommé** — l'endroit du plan où le travail s'interrompt pour
     de bon et non entre deux passes. C'est là qu'il éteint, pas au milieu d'une campagne.
  3. **Ce qui tourne et ce qui est décidé**, chacun avec son heure de fin prévue et le coût
     unitaire mesuré qui la fonde (« 57 passes × 3,03 min mesurées »).
  4. **Ce qui n'est pas couvert**, nommé, et **chiffré en retard sur l'heure annoncée** : « si
     un test sort rouge sur du code sain, tout s'arrête et l'heure ne tient plus » ; « une
     campagne à refaire repousse de 2 h 55, donc à telle heure ».

  **Le temps écoulé ne se donne pas**, sauf s'il le demande. Il ne s'en sert pas, et il occupe
  la place de ce qui l'intéresse.

  La règle vaut pour le pilote **et pour toute conversation d'agent** ; elle s'écrit dans chaque
  prompt.

- **Le pilote travaille dans SON PROPRE répertoire de travail, jamais dans celui de l'agent.**
  `/home/florian/mes_projets/Courtisans_pilote`, créé par `git worktree add`, sur `main`. Le
  répertoire `Courtisans_Game` appartient à la conversation d'agent en cours.

  Le 24/08/2026 les deux partageaient un seul répertoire, et ça a coûté deux fautes le même
  jour. Le pilote avait fait `git checkout main` ; l'agent a ensuite basculé le répertoire sur
  sa branche, et le commit suivant du pilote a atterri **sur la branche de l'agent**. Son
  `git push origin main` n'a donc rien poussé — et **pousser une branche inchangée réussit**,
  donc le `&& echo pousse` a affiché « poussé » et le pilote l'a annoncé à Florian. Une règle
  de documentation a été annoncée sur `main` alors qu'elle n'y était pas.

  Deux répertoires ne se marchent pas dessus : c'est une parade, pas une discipline.

- **Ne jamais faire `git add -A` ni `git commit -a`. Nommer les fichiers, un par un.**
  Le 24/08/2026 à 08:11, un `git add -A` du pilote a ramassé `courtisans/infoset.py` **pendant
  qu'une campagne de mutation tournait** et que le fichier portait la mutation
  `espions-adverses-visibles`. Le cassage est entré dans le commit ; `_restaurer` faisait alors
  `git checkout -- <fichier>`, qui restaure **vers HEAD**, donc vers la version mutée. La
  mutation est devenue permanente, l'invariant I7 a sauté, la suite est tombée à 1 169/79 sur
  arbre propre, et les 56 mutations suivantes ont toutes tourné sur un moteur cassé : **zéro
  survivante, campagne entière à jeter, 2 h 32 de machine.**

  `git status` avant chaque `git add`, et les fichiers nommés. Un commit du pilote ne contient
  que ce que son message annonce.

- **Ne rien commiter pendant qu'une campagne de mutation tourne.** `outillage/mutation.py`
  s'arrête désormais si `HEAD` bouge, et il restaure depuis un SHA figé au démarrage — mais il
  perd la campagne en cours. Vérifier avec `ps aux | grep mutation.py` avant de commiter.

- **Le dépôt se pousse sous ses identifiants perso.** `floSa <florian.horellou@gmail.com>`, via
  le remote `git@github.com-perso:floSa/Courtisans_Game.git`. Vérifier avant de pousser, pas
  après.

## 2. Le rôle du pilote

Le pilote **n'écrit pas le code des phases**. Il :

1. recalcule les chiffres des agents avec sa propre implémentation avant de les accepter, et
   dit quand ça tombe juste aussi clairement que quand ça ne tombe pas ;
2. tranche les arbitrages que les agents lui remontent ;
3. écrit les prompts de phase ;
4. garde le dépôt fusionné et poussé ;
5. rend à l'humain des blocs prêts à coller, numérotés par conversation destinataire.

**Deux règles de vérification apprises à leurs frais.**

- Après tout changement dans `courtisans/`, revérifier que les **20 motifs** de
  `outillage/mutation.py` s'appliquent encore. Une mutation qui cesse de s'appliquer ne
  mesure plus rien, et rien ne le signale.
- **Vérifier qu'une branche d'agent est poussée avant de la croire sauvée.** C'est arrivé
  deux fois : en phase 1 le travail de l'audit était non commité, et en phase 2 la branche
  d'audit `claude/courtisans-phase2-baseline-c5159e` n'avait **aucun upstream** alors qu'elle
  portait le verdict entier et 36 contrôles hostiles. Les agents créent leur worktree sur une
  branche locale et ne poussent pas spontanément.

**Un agent peut avoir raison contre le pilote, et c'est arrivé plusieurs fois.** Voir §7.

## 3. La numérotation des conversations

| N° | Rôle | État |
|---|---|---|
| **1** | Pilote | active — c'est celle qu'on reprend |
| **2** | Mesure de la phase 1 | close (elle a produit les 96 % de retournement) |
| **3** | Audit de la phase 1 | clos (il a écrit REJETÉ) |
| **4** | Mesure de la phase 2, constructeur | **terminée** |
| **5** | Audit de la phase 2 | **clos — ACCEPTÉ au tour 3** |

## 4. État du dépôt, vérifié le 19/08/2026 (HISTORIQUE — voir le §0 pour l'état actuel)

`github.com/floSa/Courtisans_Game`. **Tout est poussé.**

| Branche | Contenu |
|---|---|
| **`main`** | **la branche de travail** — tout le projet Courtisans, phases 0 à 2 closes |
| `old_version` | l'ancien projet RL, 38 commits, gardé pour mémoire |
| `cfr-pivot` | l'ancien travail CFR, 53 commits que `old_version` n'a pas — c'est la source du plafond à 0,190 et de l'oracle combo que le journal cite |

**Le 19/08/2026, `moteur-conforme` a pris la place de `main`.** L'ancien `main` est devenu
`old_version`, et les cinq branches d'agents des phases 1 et 2 ont été supprimées après
fusion — leurs commits sont tous dans `main`, rien n'est perdu.

Les prompts déjà utilisés (`prompts/03`, `prompts/08`, `prompts/09`) parlent encore de
`moteur-conforme`. **C'est volontaire** : ce sont des documents historiques, et les réécrire
falsifierait le compte rendu de ce qui a été fait. C'est la même branche, sous son ancien nom.

`old_version` et `cfr-pivot` sont l'ancien projet RL, hors sujet du jeu Courtisans.

**`uv` exige `UV_LINK_MODE=copy` sur ce dépôt** — OneDrive refuse les liens durs (os error 396).

**Le piège de la base.** Les cinq agents lancés jusqu'ici ont **tous** créé leur worktree sur
l'ancien `main`, où le paquet `courtisans/` n'existait pas. Le contrôle est dans les prompts depuis la
phase 2 : `git merge-base --is-ancestor 68a5c16 HEAD` doit réussir.

## 5. La phase 2 est close, et ce qui reste ouvert

**VERDICT FINAL : ACCEPTÉ**, au troisième tour d'audit. L'entrée est au journal, à la date du
19/08/2026 — **lis-la, tout y est**. Les deux branches sont fusionnées dans `main`.

Trois tours, 75 contrôles hostiles, cinq défauts trouvés dont un bloquant, 977 tests verts.

**La même faute est sortie cinq fois dans cette seule phase** : un chiffre exact sur une
population que sa phrase ne nomme pas. Chez le constructeur, chez l'auditeur, chez le pilote, et
la cinquième fois dans l'entrée de journal qui nommait la faute quatre fois. D'où la règle :
**relire ce qui a été écrit en dernier, pas ce qui a été mesuré en premier.**

**Quatre mineurs du tour 1 restent ouverts**, hors du périmètre re-vérifié, et ils sont à
traiter au début de la phase 3 :

1. le rapport généré est en cp1252 quand les **cinq** autres documents de `mesure/` sont en
   UTF-8 — le relevé de la phase 2 écrivait « quatre » ; **corrigé en phase 3** ;
2. **`vue_du_joueur`, rendue publique par cette phase, ne valide pas son argument** et rend une
   vue n'appartenant à aucun siège — c'est la réouverture du défaut 2 de la phase 0 sur une
   entrée neuve, et c'est le plus sérieux des quatre puisque tout agent en dépend ;
3. deux des douze directions annoncées sont comptées comme tenues alors que la pré-inscription
   les déclare nulles **par construction** ;
4. une cellule « voir `B4-departage` » dans une table dont le texte dit qu'elle ne se lit qu'en
   juxtaposant deux nombres.

~~**Cinq trous du protocole expérimental** sont nommés dans l'entrée de journal et **ne sont pas
corrigés**.~~ **Corrigés le 20/08/2026 par le pilote.**
[05_protocole_experimental.md](05_protocole_experimental.md) porte désormais :

- un **§0 normatif** — le format d'une entrée de journal, et les **règles d'écriture d'un chiffre**
  tirées des fautes réelles des phases 0 à 2. Le journal renvoyait à ce §0 depuis le début ; **il
  n'existait pas**. C'était un sixième trou, celui-là non recensé ;
- un **erratum sur la phase 1** qui définit enfin ses trois termes chiffrés — « retournement » =
  R2, « distribution non dégénérée » = D1 à D4, « refuser de tuer est possible » = les nœuds de
  ciblage à `len(legal_actions()) ≥ 2` — et qui ajoute que **D1 à D4 ne discriminent presque
  rien** : D2 est franchi dès 12 parties, D1 et D3 dès 3, D4 dès 1 ;
- un **erratum sur la phase 2** qui nomme les cinq défauts de son propre texte, dont le seuil de
  38 % que **les trois sièges franchissent à la fois** sous sa lecture littérale — 38,47 %,
  38,16 % et 38,90 % chez l'auditeur — avec un avantage de siège nul ;
- la correction du §1, où l'affirmation « l'appariement divise par cinq à dix le nombre de
  parties » est remplacée par ce qui est mesuré, **ρ = +0,0066 sous jeu aléatoire, moyenné sur trois sièges, facteur 1,01**,
  et par l'interdiction d'emprunter un facteur de gain non mesuré sur sa propre population ;
- les **seuils des phases 3, 4 et 5 réécrits**, le « > 55 % » étant une intuition de jeu à deux
  joueurs alors qu'à trois la valeur nulle est 33,33 %.

### Phase 3 — pas de prompt

C'est le prochain travail de fond du pilote. Le seuil est désormais écrit au protocole, et
**l'ancien « > 55 % » ne doit pas être recollé dans le prompt** : le juge est le gain moyen, borne
basse de l'IC 99 % strictement positive, sur une composition nommée — un agent contre deux
greedys. Trois choses doivent y figurer, décidées en phase 2 :

- **Aucune durée citée sur un seul chronométrage.** Sur cette machine, cinq passes du même
  code donnent un rapport max/min de **2,93 à 3,00** par campagne, de façon **non monotone**.
  Le temps mural mesure l'état de la machine, pas le coût du code. Toute durée se cite sur au
  moins trois passes, avec son étendue.
- **`agents/greedy.py` devient la ligne de base de toutes les phases suivantes et ne porte
  aucune mutation.** `outillage/mutation.py` ne cible que `courtisans/` — vérifié. À inscrire
  au programme de la phase 3.
- **`B4-tout-dos` et `B5-renfort` ne sont pas comparables entre compositions.** Leurs taux
  publiés (3,89 % et 20,41 %) bougeront sous trois agents entraînés pour une raison qui n'est
  pas l'habileté de l'agent. La phase 3 les mesure sur une population de même composition que
  la sienne, ou ne les compare pas.

### Machine

La phase 2 n'utilise aucun GPU. La phase 3 doit tourner sur le PC fixe — Ryzen 9600X,
RTX 4060, 64 Go de RAM.

## 6. Les sept points que l'audit de la phase 2 re-vérifie

Le verdict était **REJETÉ** : 1 bloquant, 2 majeurs, 4 mineurs. Le constructeur a corrigé.
La liste, telle qu'elle a été transmise à la conversation 5 :

1. **Défaut 1, bloquant.** Les cinq lignes `-par-partie` du §6 publiaient un écart entre deux
   grains — greedy sur 1 siège moins hasard sur 3 sièges agrégés. Sur `B1-motif` le signe
   s'inversait : −23,97 pt au lieu de +11,82 pt. Le grain porte désormais le **nombre de
   sièges** — indispensable, les deux colonnes portaient auparavant un libellé identique, donc
   une parade comparant les libellés n'aurait rien levé. `ecart_de_taux` et `cumuler` **lèvent**
   quand les grains diffèrent. Les cellules portent « non comparable : grains différents ».
2. **Défaut 2, majeur.** La clause « Indifférente ou en Obscurité » de B1 — le seuil du §2.2 —
   n'était tenue par aucun test : la faute réinjectée donnait 913 verts, zéro rouge. La
   régression aurait valu 9,27 points quand le détectable de la phase 3 est de 7,64.
3. **Défaut 3, majeur.** Le greedy ne fait pas ce que dit sa spécification : la pose est
   évaluée Assassins résolus conjointement, le ciblage se décide un nœud à la fois sans les
   Assassins en attente. Corrigé **par la description, pas par le code** — une ligne de base
   n'a pas besoin d'être forte, elle a besoin d'être exactement décrite. Le biais est
   déterminé pour M3 (plancher) et **ne l'est pas pour M4**, parce que les compteurs B4 sont
   jugés par l'évaluation myope elle-même : le zéro de `B4-contre-nature` est tautologique.
4. **Défaut 4, mineur.** « Aveugle par le bas » est devenu un critère **calculé** : un compteur
   dont l'écart détectable dépasse son propre taux. Deux lignes le portent, `B7-gaspillage`
   (0,30 % contre 0,15 %) et `B7-gaspillage-vraie` (0,35 % contre 0,2050 %).
5. **La garde de campagne, scindée.** Elle refusait trois greedys en disant « la mesure n'a
   plus d'objet » : vrai de M3, faux de M4. Elle confondait une mesure avec une phase.
6. **La troisième population, trois greedys.** Autorisée par le pilote, auditée par personne,
   à traiter comme une première livraison. Raison : la phase 3 fera jouer les trois sièges par
   des agents entraînés, donc une ligne de base collective mesurée sur un agent contre deux
   hasards n'est pas la bonne. **Le critère de périmètre se décide sur le texte : la définition
   nomme-t-elle un autre joueur ?** `B1-collectif` oui, `B4-tout-dos` et `B5-renfort` non.
7. **Défaut 5, trouvé par le pilote après le verdict.** Le générateur divisait par un facteur
   trois indu : un compteur `-par-partie` rend **un** booléen par partie quel que soit le
   nombre de sièges, parce que l'agrégation est dans son numérateur. **Six budgets étaient
   faux** ; les justes sont 745, 1 295, 299, 239, 10 400, 280. Il y avait **trois** sites de
   calcul du budget, il n'y en a plus qu'un.

**`B1-strict-par-partie` reste**, malgré ses 10 400 parties. Retirer une ligne parce que sa
valeur s'est révélée décevante, c'est décider un périmètre **après** avoir vu les valeurs —
la liberté que la pré-inscription existe pour supprimer. Son inutilité est l'avertissement.

## 7. Les erreurs du pilote, pour qu'elles ne se refassent pas

Elles sont ici parce qu'un pilote qui ne les connaît pas les répétera.

1. **Une formule de taille d'échantillon anti-conservatrice**, aussi fausse que celle de
   l'agent. L'arbitrage binomial exact a donné 1531 et 11629.
2. **Une estimation de 100 000 parties pour B7** contre les 320 163 de l'agent. L'agent avait
   raison.
3. **Un prompt d'audit qui demandait un 0 % sur un dénominateur vide** : « une instance sans
   Assassin, la fréquence de B4 doit valoir exactement 0 ». Faux — sans Assassin il n'y a
   aucun nœud de ciblage, donc **0/0 n'est pas 0 %**. Le contrôle utile est l'inverse :
   vérifier que le dénominateur vaut 0 et que le code **refuse** de publier un taux.
4. **Un « ralentissement uniforme » endossé** comme signature d'une cause machine. La cause
   machine tenait ; le mot « ralentissement » non. Cinq passes montrent une **étendue** non
   monotone, pas une dérive.
5. **Le `2 234` de `B1-collectif` validé alors qu'il était trois fois trop grand.** La formule
   du pilote le reproduisait — parce qu'elle avait reçu le dénominateur par partie du
   générateur, 1,0, au lieu de le dériver du grain, 3,0. C'est le constructeur qui l'a trouvé.

**L'enseignement (g), qui vient de la cinquième.** *Reproduire un nombre ne le valide pas : il
faut reproduire son unité d'abord, et le nombre ensuite.* Deux implémentations qui partagent la
même hypothèse fausse concordent parfaitement. **Le contrôle A7 — « les chiffres se
reconstruisent » — ne remplace pas le contrôle 1 — « le calcul est celui que la phrase
décrit ».** Vrai entre constructeur et auditeur, et vrai de la phase 3 qui citera ces chiffres
sans les recalculer.

## 8. Les trous de protocole trouvés en phase 2

Trois ont été mis dans le prompt par le pilote plutôt que laissés à découvrir : le greedy
n'existait pas dans le dépôt, B1–B7 n'étaient pas mesurables en l'état, le seuil de 38 % de M1
était à 9,9 erreurs-type de l'attendu donc ne discriminait rien.

L'agent en a trouvé deux de plus : « parties appariées » est vide à politiques identiques, et
« l'appariement divise par cinq à dix » implique un rho entre 0,8 et 0,9 sans mesure d'appui.

**C'est la bonne façon de faire** : nommer le trou dans le prompt coûte une phrase, le laisser
découvrir coûte un tour d'audit.
