"""L'agent d'apres-coup choisit-il pareil quand on re-tire les dos adverses de l'etat REEL ?

Si sa decision depend de l'identite reelle des dos, il triche. On compare, aux noeuds de
ciblage ou une cible est un dos adverse, la note de chaque action sur l'etat reel et sur un
monde re-tire, avec le meme alea de l'agent.
"""
import random
import sys
from collections import Counter

from courtisans.cards import Role
from courtisans.engine import Engine, Phase
from experiences.config import CONFIG as C
from experiences.pimc import determiniser, greedy_rollout
from experiences.valeur import agent_valeur

chemin = sys.argv[1]
aveugle = sys.argv[2] != 'temoin' if len(sys.argv) > 2 else True
c = Counter()
e = Engine(C)
for d in range(400):
    s = e.reset(6_500_000 + d)
    pol = greedy_rollout(random.Random(d))
    while not s.is_terminal():
        if s.phase() is Phase.CIBLAGE:
            moi = s.current_player()
            if any(p.carte.role is Role.ESPION and p.poseur != moi for p in s.cibles_courantes()):
                c["noeuds avec dos ciblable"] += 1
                for k in range(3):
                    vrai = agent_valeur(random.Random(k), chemin, aveugle=aveugle)(s)
                    monde = determiniser(s, moi, random.Random(100 + k))
                    faux = agent_valeur(random.Random(k), chemin, aveugle=aveugle)(monde)
                    c["essais"] += 1
                    c["decision differente"] += vrai != faux
        s.apply(pol(s))
print(dict(c))
