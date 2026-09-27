"""Le reseau de la phase 3 sait-il QUELLE carte est la cible i ?

On joue des parties greedy ; a chaque noeud de ciblage, on inverse l'ordre des cartes de la
zone de l'Assassin dans `_posees` (ordre d'arrivee), ce qui change la carte designee par
chaque indice d'action, et on regarde si le tenseur du decideur change.
"""
import random
from collections import Counter

from courtisans.engine import Engine, Phase
from courtisans.infoset import tenseur
from experiences.pimc import greedy_rollout
from mesure.instance import ENTRAINEMENT_3J as C

e = Engine(C)
c = Counter()
for d in range(2000):
    s = e.reset(7_000_000 + d)
    pol = greedy_rollout(random.Random(d))
    while not s.is_terminal():
        if s.phase() is Phase.CIBLAGE:
            j = s.current_player()
            cibles = s.cibles_courantes()
            ids = {(p.carte.famille, p.carte.role) for p in cibles}
            c["noeuds"] += 1
            if len(cibles) >= 2:
                c[">=2 cibles"] += 1
                if len(ids) >= 2:
                    c[">=2 cibles d'identite differente"] += 1
                    z = s.assassin_en_resolution().zone
                    t0 = tenseur(s, j)
                    m = s.clone()
                    dans = [p for p in m._posees if p.zone == z]
                    hors = [p for p in m._posees if p.zone != z]
                    m._posees = hors + dans[::-1]
                    if [p.carte for p in m.cibles_courantes()] != [p.carte for p in cibles]:
                        c["ordre change"] += 1
                        if tenseur(m, j) == t0:
                            c["ordre change ET tenseur identique"] += 1
        s.apply(pol(s))
print(dict(c))
