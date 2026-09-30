"""L'IA ressemble-t-elle au greedy, et OU s'en ecarte-t-elle ?

Hypothese de l'auteur du jeu (27/09) : au debut, la logique du greedy est la bonne ; plus la
partie avance, plus le comptage des cartes restantes devrait l'emporter. Donc l'accord
IA / greedy devrait etre fort au debut et chuter en fin de partie.

On joue l'IA contre 2 greedys ; a chaque decision de POSE de l'IA, on calcule l'ensemble des
coups que le greedy juge optimaux (`greedy.evaluer_actions`, sa propre evaluation myope) et
on note, par tour restant : la part des decisions ou le greedy a une EGALITE (plusieurs coups
optimaux, qu'il departage au hasard), et la part ou l'IA joue un coup optimal pour le greedy.

    COURTISANS_INSTANCE=complete uv run python -m experiences.ressemblance --donnes 60
"""
import argparse
import random
from collections import defaultdict

from agents import greedy
from agents.perception import percevoir
from courtisans.engine import Engine, Phase
from experiences.config import CONFIG
from experiences.pimc import greedy_rollout
from experiences.valeur import agent_valeur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modele", default="experiences/modeles/meilleur.pt")
    ap.add_argument("--donnes", type=int, default=60)
    ap.add_argument("--depart", type=int, default=6_300_000)
    a = ap.parse_args()
    moteur = Engine(CONFIG)
    stats = defaultdict(lambda: [0, 0, 0, 0])  # decisions, egalites, accord, ecart de score
    for donne in range(a.depart, a.depart + a.donnes):
        for siege in range(CONFIG.joueurs):
            ia = agent_valeur(random.Random(donne), a.modele)
            adv = greedy_rollout(random.Random(donne + 7))
            etat = moteur.reset(donne)
            while not etat.is_terminal():
                j = etat.current_player()
                if j != siege:
                    etat.apply(adv(etat))
                    continue
                action = ia(etat)
                if etat.phase() is Phase.POSE and len(etat.legal_actions()) > 1:
                    valeurs = greedy.evaluer_actions(percevoir(etat, j))
                    m = max(valeurs.values())
                    optimaux = [x for x, v in valeurs.items() if v == m]
                    t = etat.tours_restants(j)
                    s = stats[t]
                    s[0] += 1
                    s[1] += len(optimaux) > 1
                    s[2] += action in optimaux
                    s[3] += m - valeurs[action]
                etat.apply(action)
    print(f"{'tours restants':>14} {'decisions':>9} {'egalite greedy':>15} "
          f"{'IA = greedy':>12} {'points cedes':>13}")
    for t in sorted(stats, reverse=True):
        n, eg, acc, cede = stats[t]
        print(f"{t:>14} {n:>9} {100 * eg / n:>14.1f}% {100 * acc / n:>11.1f}% {cede / n:>13.2f}")


if __name__ == "__main__":
    main()
