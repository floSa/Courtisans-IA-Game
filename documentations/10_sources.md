# Sources — la veille bibliographique

**Ce qui a été lu pour orienter les pistes d'`experiences/PISTES.md`, avec ce qu'on en retient et
ce qu'on n'a pas pu vérifier.** Veille du 30/09/2026, faite par recherche web. Règle : une source
n'est ici que si elle a changé ou peut changer une décision du projet.

**Noms d'auteurs : volontairement omis** (non vérifiés dans les résultats de recherche ; seuls titres, lieux de publication et liens sont repris).

**Niveau de lecture.** *Résumé* = seul l'abstract ou une synthèse de moteur de recherche a été lu.
*Illisible* = le document a été récupéré mais l'outil n'a pas pu en extraire le texte (PDF
compressé) : **aucun chiffre de ces articles n'est repris ici**. Les ablations détaillées de
Suphx et les résultats chiffrés de l'article sur Skat restent à lire.

---

## Ce qui a orienté des pistes

| Source | Idée | Niveau de lecture | Piste du projet |
|---|---|---|---|
| [*Suphx: Mastering Mahjong with Deep Reinforcement Learning*](https://arxiv.org/abs/2003.13590) (Microsoft Research, 2020) | **Prédiction de récompense globale** ; **oracle guiding** : un agent qui voit l'information cachée (mains adverses, mur) sert de professeur, puis on retire progressivement ces entrées ; adaptation en ligne de la politique | Résumé (abstract) ; PDF illisible | La tête de statuts du cycle 1 est un proche cousin de la prédiction de récompense globale (cible dense apprise à côté du gain). L'oracle guiding = piste 6 |
| Suphx, [page de projet](https://www.microsoft.com/en-us/research/project/suphx-mastering-mahjong-with-deep-reinforcement-learning/) | Même contenu, version courte | Résumé | — |
| [*Improving State Evaluation, Inference, and Search in Trick-Based Card Games*](https://webdocs.cs.ualberta.ca/~nathanst/papers/skat.pdf) (Skat) | Un réseau prédit **où sont les cartes cachées** ; ces prédictions servent à **échantillonner des mondes vraisemblables** dans PIMC, avec un gain de force de jeu substantiel | Synthèse de moteur de recherche ; PDF illisible (chiffres non repris) | Pistes 5 et 8 : tête de croyance sur l'identité des Espions, puis mondes pondérés dans `fin_de_partie` (aujourd'hui tirés uniformément) |
| [*Perfect Information Monte Carlo with Postponing Reasoning*](https://arxiv.org/abs/2408.02380) (EPIMC, IEEE CoG 2024) | **Repousser la résolution en information parfaite** atténue la *strategy fusion* de PIMC ; meilleurs résultats là où elle pèse | Résumé | Piste 10 : fin de partie à deux tours. Note : dans `fin_de_partie`, les adversaires simulés jouent avec *leur* information, pas celle du monde, donc la fusion est déjà limitée ; à mesurer avant d'investir |
| [*Student of Games*](https://arxiv.org/pdf/2112.03178) | Recherche guidée + apprentissage + raisonnement théorie des jeux, valable en information parfaite et imparfaite | Résumé | Horizon long (recherche, pistes 9-11) |
| [*Information Set Monte Carlo Tree Search*](https://www.researchgate.net/publication/254060888_Information_Set_Monte_Carlo_Tree_Search) | ISMCTS réduit la *strategy fusion* par rapport à la déterminisation seule et alloue mieux le calcul | Résumé | Horizon long (piste 6 de l'ancien classement : recherche profonde) |
| Danihelka et al., [*Planning and Policy Improvement* (Gumbel AlphaZero), thèse](https://discovery.ucl.ac.uk/10167022/2/ivo_danihelka_thesis.pdf) | Garantie d'amélioration de politique avec très peu de simulations (Gumbel top-k + demi-séquentielle) | Résumé | Pertinent si l'agent reçoit un jour une tête de politique ; aujourd'hui l'agent n'a qu'une valeur d'après-coup |
| [*PerfectDou: Dominating DouDizhu with Perfect Information Distillation*](https://lacuna.tiptreesystems.com/work/perfectdou-dominating-doudizhu-with-perfect-information-distillation/wrk_506ffe04a6d926cb06164aff0df629b2) | Entraînement « information parfaite, exécution en information imparfaite » (distillation depuis un agent qui voit tout) | Résumé (fiche) | Piste 6 (enseignant privilégié) |

## Trouvé mais non lu

| Source | Pourquoi ce n'est pas exploité |
|---|---|
| [*Scalable decision-making for games of imperfect information*](https://www.nature.com/articles/s41586-026-11036-y) (Nature, 2026) | Derrière un accès payant ; **seul le titre est connu**. Aucune affirmation n'en est tirée. À lire si l'accès est possible : elle peut concerner directement la recherche en information imparfaite |
| [*To Distill or Decide? Understanding the Algorithmic Trade-off in Partially Observable RL*](https://arxiv.org/pdf/2510.03207) | Non ouverte. Titre pertinent pour choisir entre distiller un enseignant privilégié et apprendre directement |
| [*Informed Asymmetric Actor-Critic: Leveraging Privileged Signals Beyond Full-State Access*](https://icml.cc/virtual/2026/poster/66074) (ICML 2026) | Non ouverte ; pertinente pour la piste 6 : le signal privilégié n'a pas besoin d'être l'état complet (par exemple les statuts finaux) |

## Ce que ces lectures ne prouvent pas

- Aucune n'a été **reproduite** ici. Elles disent *où chercher*, pas *ce qui marchera sur
  Courtisans*. Chaque idée retenue passe par le même protocole que les autres : hypothèse et
  seuils écrits avant la mesure, journal, contrôle des graines.
- Les gains annoncés dans ces articles concernent des jeux (Mahjong, Skat, DouDizhu, poker)
  dont l'information cachée et la structure diffèrent : ici, seuls les **Espions** sont cachés
  (un cinquième des rôles), ce qui plaide pour que l'inférence sur les mondes pèse moins que
  dans Skat.

## Comment compléter cette liste

Ajouter une ligne dans le tableau avec : référence et lien, l'idée en une phrase, **le niveau de
lecture**, et la piste concernée. Si une source change une décision, l'écrire aussi dans
l'entrée de journal correspondante.
