"""Cycle 2 : boucle d'amelioration du reseau a tete de statuts, sur ses propres parties.

Une generation :
1. JOUER  : une ligue -- auto-jeu 35 %, contre 2 greedys 25 %, contre 2 x meilleur.pt 20 %,
            contre 2 x generation precedente 20 % -- donnes fraiches, toutes les vues gardees ;
2. APPRENDRE : depuis zero, 2 epoques, sur les parties de greedy (12k + 24k) et toutes les
            generations (plafond de vues, anciennes sous-echantillonnees par partie) ;
3. JUGER  : contre 2 greedys et en duel contre l'agent du cycle 1 (donnes fixes).

    COURTISANS_INSTANCE=complete uv run python -m experiences.cycle --generations 3
Une ligne par generation dans experiences/resultats/cycle2.jsonl.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time

from experiences.statuts import entrainer, generer_contextes

DOSSIER = "experiences/donnees/statuts"
MODELES = "experiences/modeles"
GREEDY = "experiences.pimc:greedy_rollout"
MEILLEUR = "experiences.valeur:agent_valeur:chemin='experiences/modeles/meilleur.pt'"
POIDS = "poids_statuts=1,poids_valeur=10"


def agent(chemin):
    return f"experiences.statuts:agent_statuts:chemin='{chemin}',{POIDS}"


def juger(spec, adv, donnes, depart, etiquette):
    sortie = "experiences/resultats/cycle2_arene.jsonl"
    cmd = [sys.executable, "-m", "experiences.arene", spec, "--adv", adv, "--donnes", str(donnes),
           "--depart", str(depart), "--sortie", sortie]
    subprocess.run(cmd, check=True, capture_output=True)
    ligne = json.loads(open(sortie).readlines()[-1])
    return {"etiquette": etiquette, "gain": ligne["gain_moyen"], "ic99": ligne["ic99"],
            "parties": ligne["parties"], "donnes": [depart, depart + donnes - 1]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generations", type=int, default=3)
    ap.add_argument("--parties", type=int, default=12000)
    ap.add_argument("--plafond", type=int, default=6_000_000)
    ap.add_argument("--depart-generation", type=int, default=9_100_000)
    a = ap.parse_args()

    ref = f"{MODELES}/statuts_s2.pt"          # l'agent du cycle 1
    courant = ref                             # le modele qui joue les donnees de la generation
    precedent = ref
    fichiers = [f"{DOSSIER}/greedy_12k.npz", f"{DOSSIER}/greedy_24k.npz"]
    t0 = time.time()
    for k in range(1, a.generations + 1):
        t1 = time.time()
        A, P = agent(courant), agent(precedent)
        contextes = [(0.35, [A, A, A]), (0.25, [A, GREEDY, GREEDY]),
                     (0.20, [A, MEILLEUR, MEILLEUR]), (0.20, [A, P, P])]
        donnees = f"{DOSSIER}/gen_{k:02d}.npz"
        generer_contextes(contextes, a.parties, a.depart_generation + 100_000 * k, 0.05, 11, donnees)
        fichiers.append(donnees)
        t2 = time.time()
        modele = f"{MODELES}/cycle2_gen_{k:02d}.pt"
        entrainer(fichiers, modele, epoques=2, plafond=a.plafond)
        t3 = time.time()
        cand = agent(modele)
        ligne = {
            "generation": k,
            "contre_greedy": juger(cand, GREEDY, 450, 6_000_000, "2 greedys"),
            "duel_cycle1": juger(cand, agent(ref), 450, 6_100_000, "duel agent du cycle 1"),
            "duel_precedent": juger(cand, agent(courant), 450, 6_100_000, "duel modele courant"),
            "secondes": {"jeu": round(t2 - t1), "apprentissage": round(t3 - t2),
                         "jugement": round(time.time() - t3), "depuis_debut": round(time.time() - t0)},
        }
        print(json.dumps(ligne), flush=True)
        with open("experiences/resultats/cycle2.jsonl", "a") as f:
            f.write(json.dumps(ligne) + "\n")
        precedent, courant = courant, modele   # sans gardien : on suit la courbe, on ne filtre pas


if __name__ == "__main__":
    main()
