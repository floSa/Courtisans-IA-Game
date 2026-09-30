# `experiences/` — l'IA qui joue, mode d'emploi

**À lire en premier si tu reprends l'IA** (toi, ou une autre IA). Le moteur de règles est à la
racine (`courtisans/`) et ne change pas ; tout ce qui apprend et joue vit ici. Mis à jour le
30/09/2026.

Ordre de lecture : ce fichier → l'entrée la plus récente de
[../documentations/06_journal_decisions.md](../documentations/06_journal_decisions.md) (une entrée
par cycle : hypothèse, seuils écrits *avant* la mesure, résultat, décision) →
[PISTES.md](PISTES.md) (ce qu'on teste ensuite) → [REVUE_CRITIQUE.md](REVUE_CRITIQUE.md) (le
diagnostic du 27/09 et les résultats antérieurs). Sources de la veille :
[../documentations/10_sources.md](../documentations/10_sources.md).

---

## 1. Où on en est (30/09/2026)

| | |
|---|---|
| Acquis solide | Une **cible auxiliaire dense** — le statut final des 6 familles — apprise en plus du gain. À données égales, elle fait passer l'agent de +0,171 à +0,297 contre 2 greedys (3 graines, écart-type entre graines 0,014 : l'effet fait ≈ 9 écarts-types) |
| Meilleur réseau | `modeles/statuts_s3_e2.pt` (108 000 parties de greedy, 2 époques) : **+0,455** contre 2 greedys ; **à égalité avec `modeles/meilleur.pt` en duel** (−0,009) |
| Agent jouable de référence | `fin_de_partie` sur ce réseau : +0,099 contre le réseau seul ; +0,470 contre 2 greedys ; **+0,046 [+0,001 ; +0,093] contre `meilleur.pt`** (limite : *non établi*, voir §5) |
| Ce qui a échoué | Auto-jeu en ligue avec la tête de statuts (cycle 2) : aucun progrès en 3 générations |
| Goulot identifié | Le **nombre de parties distinctes** (147 vues très corrélées par partie) : le réseau surapprend dès 2-3 époques |
| Prochaines marches | [PISTES.md](PISTES.md), section « Nouvelles pistes du 30/09 » |

Un agent = une fonction `f(rng, **options) → politique`, et une politique = `f(état) → action`.
Il se désigne par une chaîne `module:fonction:clé=valeur,clé=valeur` (voir `arene.fabrique`).

---

## 2. Carte du dossier

| Fichier | Rôle |
|---|---|
| `config.py` | Choix de l'instance : **`COURTISANS_INSTANCE=complete`** = le vrai jeu (90 cartes, 3 joueurs, 10 tours). Sans la variable : instance réduite (40 cartes), utilisée par les tests. **Tout ce qui est chiffré ici est en jeu complet.** |
| `arene.py` | **Le juge.** Un agent contre deux adversaires, sièges permutés, parallèle, bootstrap par donne → gain moyen, IC 99 %, victoires seules |
| `apparie.py` | Écart *apparié* entre deux mesures faites sur les mêmes donnes (retire la variance des donnes) |
| `rapide.py` | Tenseur et `appliquer` rapides, **égaux bit à bit** au tenseur officiel (`test_rapide.py`) |
| `valeur.py` | Réseau de valeur `V` (gain, écart), agent d'après-coup `agent_valeur`, `pimc_valeur` |
| **`statuts.py`** | **Réseau à têtes (gain, écart, 3 logits × 6 familles)**, génération des données, entraînement, évaluation de la prévisibilité, **`agent_statuts`** |
| `cycle.py` | Boucle d'auto-jeu en ligue avec la tête de statuts (cycle 2) |
| `fin_de_partie.py` | Agent hybride : réseau puis simulation jusqu'au bout au dernier tour (`statuts=True` pour le réseau à statuts) |
| `pimc.py` | Déterminisation aveugle des mondes, PIMC, `greedy_rollout` (le greedy, version rapide) |
| `iteration.py` | Boucle d'auto-jeu TD(λ) contre une ligue avec gardien (itérations 1-8), `permuter_familles` (règle C18) |
| `donnees.py` | Données de valeur des débuts (gain et écart seulement, sans statuts) |
| `suivi.py`, `tournoi.py`, `capacite.py`, `ressemblance.py`, `ciblage_aveugle.py`, `fuite_*.py` | Instruments de mesure et de contrôle du 27/09 (voir la revue) |
| `modeles/` | Checkpoints, voir §4 |
| `resultats/` | Journaux de mesure (`*.jsonl`, une ligne par mesure) et sorties, voir §4 |
| `donnees/` | **Ignoré par Git, ~14 Go**, régénérable (§3) |

Tests de garde-fous : `uv run pytest tests/experiences -q` (tenseur rapide identique à
l'officiel, déterminisation aveugle, agents aveugles au ciblage avec témoin positif, statuts
certains = décompte du tenseur, données bien formées).

---

## 3. Reproduire

Tout se lance depuis la racine du dépôt, avec `uv` (jamais `pip` direct). Installer :
`uv sync` (le groupe `ia` apporte torch et numpy). GPU : RTX 4060 Ti utilisée pour
l'entraînement. Prévoir ~14 Go de disque pour les données.

```bash
export COURTISANS_INSTANCE=complete

# Données : parties de greedy (ε = 0,1), ~147 vues par partie, 12 000 parties ≈ 3 min sur 11 processus
uv run python -m experiences.statuts generer --parties 12000 --sortie experiences/donnees/statuts/greedy_12k.npz
uv run python -m experiences.statuts generer --parties 24000 --depart 9012000 --sortie experiences/donnees/statuts/greedy_24k.npz

# Entraînement : 2 époques (le test est affiché à chaque époque ; au-delà, surapprentissage)
uv run python -m experiences.statuts entrainer experiences/modeles/statuts_s2.pt \
    experiences/donnees/statuts/greedy_12k.npz experiences/donnees/statuts/greedy_24k.npz --epoques 2
#   --sans-statuts  → le réseau témoin (mêmes données, sans tête de statuts)

# Prévisibilité du statut final par tour restant, contre « le statut actuel restera »
uv run python -m experiences.statuts evaluer experiences/modeles/statuts_s2.pt \
    experiences/donnees/statuts/greedy_24k.npz --temoin experiences/modeles/statuts_temoin2.pt

# Jouer : l'agent à statuts contre 2 greedys (900 parties)
uv run python -m experiences.arene \
  "experiences.statuts:agent_statuts:chemin='experiences/modeles/statuts_s3_e2.pt',poids_statuts=1,poids_valeur=10" \
  --donnes 300 --depart 6000000

# L'agent hybride (fin de partie, ~20 s par donne) contre `meilleur.pt`
uv run python -m experiences.arene \
  "experiences.fin_de_partie:fin_de_partie:chemin='experiences/modeles/statuts_s3_e2.pt',statuts=True,tours_fin=1,nb_mondes=32,rollout='valeur'" \
  --adv "experiences.valeur:agent_valeur:chemin='experiences/modeles/meilleur.pt'" --donnes 450 --depart 6200000

# La boucle du cycle 2 (auto-jeu en ligue ; ≈ 5 min par génération)
uv run python -m experiences.cycle --generations 3
```

Pondération de l'agent : score d'une action = `poids_statuts × écart espéré via les statuts +
poids_valeur × (gain + poids_ecart × écart)`, évalué sur la vue **d'après-coup** (on joue le coup
sur un clone et on note la vue qui en résulte). Retenu : statuts ×1, valeur ×10.

### Plages de donnes (les graines des parties) — à ne pas réutiliser pour autre chose

| Plage | Usage |
|---|---|
| 5 000 000+ | arène standard (contre 2 greedys), cycles 1 à 3 d'exploration |
| 5 700 000 ; 5 800 000+ | ancre `c1b` ; juge contre la courante (itérations) |
| 6 000 000+ | **jugement contre 2 greedys** (cycles 2 à 4) |
| 6 100 000+ / 6 200 000+ / 6 300 000+ | duel contre le cycle 1 / contre `meilleur.pt` / hybride contre le réseau seul |
| 6 400 000+ | contrôle des graines |
| 8 000 000+ | `donnees.py` (anciennes données de valeur) |
| 9 000 000 → 9 035 999 | `greedy_12k` et `greedy_24k` (entraînement) |
| 9 100 000+ (par pas de 100 000) | générations du cycle 2 |
| 9 500 000 → 9 571 999 | `greedy_b0..b2` (cycle 3) |
| 9 600 000+ | tests |

---

## 4. Modèles et résultats

| Checkpoint | Ce que c'est |
|---|---|
| `meilleur.pt` | Meilleur de la boucle TD(λ) (= `iteration6/gen_06`) : +0,289 contre 2 greedys. **L'adversaire de référence des duels.** |
| `c1.pt`, `c1b.pt`, `v1.pt`, `v1b.pt`, `v2.pt` | Premiers réseaux de valeur (instance réduite pour v1/v1b/v2 ; jeu complet pour c1/c1b). `c1b` = ancre |
| `iteration*/gen_NN.pt` | Toutes les générations des itérations 1 à 8 (TD(λ), ligue) |
| `statuts_s1.pt`, `statuts_temoin.pt` | Premier essai du cycle 1 : 12 000 parties, **6 époques → surapprentissage**. Conservés comme contre-exemple. Ne pas utiliser |
| `statuts_s2.pt`, `statuts_temoin2.pt` | Cycle 1 : 36 000 parties, 2 époques, avec / sans tête de statuts |
| `statuts_s3_e1.pt`, `statuts_s3_e2.pt` | Cycle 3 : 108 000 parties, 1 et 2 époques. **`statuts_s3_e2` = référence** |
| `cycle2_gen_01..03.pt` | Cycle 2 (auto-jeu en ligue) : n'ont pas progressé |
| `graines/avec_N.pt`, `graines/sans_N.pt` | Contrôle des graines : 3 réseaux avec, 3 sans tête de statuts (36 000 parties, 2 époques) |

`resultats/` : `arene.jsonl` (mesures d'exploration), `cycle1_*` (prévisibilité + confirmation),
`cycle2*.jsonl`, `cycle3_arene.jsonl`, `cycle4_arene.jsonl` (hybride), `graines.jsonl`
(+ `graines_etiquettes.jsonl` : **même ordre ligne à ligne**, une étiquette par mesure),
`iteration1..8.*` (boucle TD(λ) ; `uv run python -m experiences.suivi <fichier>.jsonl` en donne un
résumé lisible). Chaque ligne d'`arene.jsonl`-style contient `par_donne` : c'est ce qui permet
l'écart apparié (`apparie.py`).

---

## 5. Comment lire un chiffre ici

- **Deux incertitudes, pas une.** L'IC 99 % affiché par l'arène ne couvre que le hasard des
  *parties* (≈ ± 0,04 à 450 donnes pour un gain contre 2 greedys). Le hasard de
  l'*entraînement* est d'environ **± 0,015 (1 écart-type)**, mesuré sur 3 graines (cycle 1
  seulement). Règle du dépôt : **tout écart inférieur à 0,05 est « non établi »** tant qu'il n'est pas
  répliqué sur au moins 3 graines. Sont établis : l'apport de la tête de statuts (+0,126), la fin
  de partie contre le réseau seul (+0,099). Ne sont **pas** établis : cycle 3 contre cycle 1
  (+0,037), hybride contre `meilleur.pt` (+0,046).
- **Non-transitivité.** Mieux battre le greedy ne veut pas dire mieux battre `meilleur.pt`
  (cycle 3 : +0,08 contre le greedy, 0,00 contre `meilleur.pt`). Toujours mesurer les deux.
- **Jamais de paramètre choisi et confirmé sur les mêmes donnes.** Explorer sur une plage,
  confirmer sur une plage neuve (§3).
- **Surapprentissage.** Regarder le test à chaque époque ; 1-2 époques suffisent.
- Pas d'« amélioration » annoncée sans seuil écrit avant la mesure : c'est le format des
  entrées du journal.

## 6. Pièges rencontrés

- `pgrep -f "motif"` se reconnaît lui-même dans un `sh -c` et ne rend jamais « fini » ; tester
  avec `ps aux | grep "python.*motif" | grep -v grep`.
- Un `nohup … &` dans un outil rend la main tout de suite : la notification de fin concerne le
  lanceur, pas le travail.
- La moyenne d'un agent contre deux greedys varie de ±0,03 d'une plage de donnes à l'autre :
  comparer *sur la même plage*, de préférence en apparié.
- Ne pas entraîner sur les données de test : `_coupe` coupe sur une frontière de partie, les 8 %
  de fin sont le test.
