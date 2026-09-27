"""Le tenseur d'un siege change-t-il si l'on permute l'identite des Espions ADVERSES caches ?

Si oui, l'agent d'apres-coup verrait des informations cachees. On teste a tous les noeuds,
terminal compris, en re-tirant les dos adverses (meme procede que la determinisation PIMC,
pioche comprise).
"""
import random
from collections import Counter

from courtisans.engine import Engine
from courtisans.infoset import tenseur
from experiences.pimc import determiniser, greedy_rollout
from mesure.instance import ENTRAINEMENT_3J as C

e = Engine(C)
c = Counter()
for d in range(300):
    s = e.reset(6_000_000 + d)
    pol = greedy_rollout(random.Random(d))
    while True:
        for j in range(C.joueurs):
            if s.is_terminal() or j == s.current_player():
                t = tenseur(s, j)
                for k in range(3):
                    # determiniser exige des mains adverses vides : vrai au terminal et
                    # pour le joueur courant.
                    m = determiniser(s, j, random.Random(k))
                    cle = "terminal" if s.is_terminal() else "en cours"
                    c[cle + " essais"] += 1
                    if tenseur(m, j) != t:
                        c[cle + " FUITE"] += 1
        if s.is_terminal():
            break
        s.apply(pol(s))
print(dict(c))
