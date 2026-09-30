# Courtisans — moteur de règles

Le moteur de règles du jeu de cartes Courtisans, et rien d'autre : pas d'IA, pas
d'interface, pas d'entraînement. Les règles, et les tests qui prouvent qu'elles sont
respectées.

Les règles font autorité dans [documentations/01_regles.md](documentations/01_regles.md).
Le point d'entrée du corpus est [documentations/00_index.md](documentations/00_index.md).

---

## Installer et jouer la suite

```bash
uv sync
```

```bash
uv run pytest -q
```

## Les trois moteurs — la même suite, trois fois

Les tests de conformité ne sont **jamais** réécrits pour l'adaptateur. Le moteur sur
lequel ils tournent est choisi par une variable d'environnement.

| Commande | Ce qui est exercé |
|---|---|
| `uv run pytest tests/conformite -q` | le cœur nu, pioche fixée par un seed |
| `COURTISANS_MOTEUR=openspiel uv run pytest tests/conformite -q` | l'adaptateur pyspiel, pioche fixée |
| `COURTISANS_MOTEUR=openspiel-hasard uv run pytest tests/conformite -q` | l'adaptateur, arbre à nœuds de chance |

```bash
COURTISANS_MOTEUR=openspiel uv run pytest tests/conformite -q
```

```bash
COURTISANS_MOTEUR=openspiel-hasard uv run pytest tests/conformite -q
```

Le mode `openspiel-hasard` est réservé à la suite de conformité : la règle R-a compare
les deux chemins de `reset`, qui ne peuvent pas coïncider quand l'un passe par le hasard
et l'autre non.

## Couverture

```bash
uv run pytest -q --cov=courtisans --cov-report=term-missing
```

## Test de mutation — vérifier que la suite sait échouer

**18 fautes plausibles** sont injectées une à une dans le moteur — le cœur, ou l'adaptateur
— et chacune doit faire tomber des tests. Une mutation qui survit désigne un trou.

Les huit dernières ont été ajoutées le 17/08, **une par défaut trouvé par l'audit** de la
phase 0 : un correctif dont la mutation survit n'est tenu par aucun test, et il repartira au
prochain refactoring. Toute correction de défaut arrive donc avec sa mutation.

```bash
uv run python outillage/mutation.py
```

L'outil refuse de tourner sur un dépôt qui a des modifications non commitées — il
restaure les fichiers par `git checkout`.

---

## Les agents qui jouent — `experiences/`

**Une seule branche : `main`.** Depuis le 27/09/2026, l'IA se construit dans `experiences/`, en
régime exploratoire ; le moteur et la suite ci-dessus en restent la référence. **Point
d'entrée : [experiences/README.md](experiences/README.md)** (état, carte du dossier,
commandes pour tout reproduire, comment lire un chiffre). Le journal des décisions est
[documentations/06_journal_decisions.md](documentations/06_journal_decisions.md), les sources
[documentations/10_sources.md](documentations/10_sources.md), les pistes
[experiences/PISTES.md](experiences/PISTES.md).

État au 30/09/2026 (soir) : la meilleure IA (réseau à cible auxiliaire « statut final des familles »,
entraîné avec permutation des familles) bat 2 greedys de **+0,50 à +0,56** de gain moyen et
**bat la meilleure IA précédente (`meilleur.pt`) en duel de +0,05 à +0,09**, sur 5 graines.
Reprise : [experiences/README.md](experiences/README.md), section « Où l'on reprend ».

`uv sync` installe aussi le groupe `ia` (torch, numpy). Mesurer un agent sur le jeu complet,
contre deux greedys, sièges permutés :

```bash
COURTISANS_INSTANCE=complete uv run python -m experiences.arene "experiences.statuts:agent_statuts:chemin='experiences/modeles/graines/aug108_1.pt',poids_statuts=1,poids_valeur=10" --donnes 300
```

Les garde-fous de ces agents (aveuglement, tenseur rapide identique à l'officiel, données bien
formées) :

```bash
uv run pytest tests/experiences -q
```

L'historique des anciennes branches (travail CFR, ancien projet RL, audits de la phase 3,
phase 4) est conservé dans les tags `archive/*` : `git tag -l 'archive/*'`, détail dans
[documentations/09_reprise.md](documentations/09_reprise.md) §0.

---

## Ce qu'il y a dans le dépôt

| Chemin | Contenu |
|---|---|
| `courtisans/cards.py` | cartes, rôles, zones, valeur, visibilité |
| `courtisans/config.py` | `GameConfig` — le paramétrage, validé à la construction |
| `courtisans/rules.py` | les règles en fonctions pures |
| `courtisans/engine.py` | la machine à états |
| `courtisans/infoset.py` | la vue d'un joueur : chaîne et tenseur |
| `courtisans/openspiel_adapter.py` | l'enveloppe pyspiel — le seul fichier qui importe OpenSpiel |
| `tests/conformite/` | les 18 contrôles du §9 des règles, C1 à C18 |
| `tests/invariants/` | les 11 invariants du §5 de la spécification, I1 à I11 |
| `tests/moteur/`, `tests/regles/`, `tests/config/`, `tests/infoset/` | contrats et fonctions pures |
| `tests/adaptateur/` | validité du jeu OpenSpiel, et critère A4 |
| `tests/acceptation/` | les critères A1, A2, A3 et A6 |
| `outillage/mutation.py` | la batterie de mutation |

**Le cœur n'importe ni OpenSpiel, ni PyTorch, ni NumPy.** Un test le vérifie dans un
sous-processus, avec un témoin positif pour qu'il ne passe pas simplement parce que rien
n'est installé.

---

## Dette connue, assumée

| # | Point | Pourquoi c'est laissé tel quel |
|---|---|---|
| 1 | **La canonicalisation par permutation des familles n'est pas implémentée** | Canonicaliser l'observation sans traduire aussi l'espace d'actions produit un agent qui croit poser une carte et en pose une autre. La traduction demande une API que la spécification ne définit pas. Elle sera une étape à part entière, tests d'abord. |
| 2 | **L'encodage par cible de la phase de ciblage n'est pas écrit** | Il n'a de sens que quand un réseau le consomme, et sa forme exacte dépend de lui. L'écrire sans test reproduirait ce qui a fait retirer `canonicalisation` de `GameConfig`. |
| 3 | `max_game_length` est une borne large — `7 × joueurs × tours` | Légal au sens d'OpenSpiel. La resserrer sans mesure du coût réel serait de l'optimisation à l'aveugle. |
| 4 | `information_state_tensor_shape()` mesure au lieu de calculer | Juste et robuste au changement de disposition, mais pas gratuit si OpenSpiel l'appelle souvent. Même raison. |

---

## Conventions

Python 3.12, `uv`, `ruff` en `line-length = 100` avec les règles `E, F, W, I, UP, B`.
Français pour les noms de domaine et les docstrings. Détail et justification de chaque
règle : [documentations/04_conventions_code.md](documentations/04_conventions_code.md).
