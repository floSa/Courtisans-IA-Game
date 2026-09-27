"""`tenseur_rapide` == `infoset.tenseur`, bit a bit, sur les deux instances.

Lance : uv run python -m experiences.test_rapide
"""
import random
import time

from courtisans.cards import Role
from courtisans.config import GameConfig
from courtisans.engine import Engine
from courtisans.infoset import tenseur
from experiences.rapide import appliquer, tenseur_rapide
from mesure.instance import ENTRAINEMENT_3J

COMPLETE = GameConfig(familles=6, roles=tuple(Role), exemplaires=3, joueurs=3)
CONFIGS = [ENTRAINEMENT_3J, COMPLETE,
           GameConfig(familles=5, roles=tuple(Role), exemplaires=2, joueurs=4),
           GameConfig(familles=3, roles=tuple(Role), exemplaires=2, joueurs=2)]


def main():
    total = 0
    for config in CONFIGS:
        e = Engine(config)
        for d in range(150):
            rng = random.Random(d)
            s = e.reset(9_900_000 + d)
            while True:
                for j in range(config.joueurs):
                    a, b = tenseur(s, j), tenseur_rapide(s, j)
                    ecarts = [i for i, (x, y) in enumerate(zip(a, b, strict=True)) if x != y]
                    assert a == b, (config, d, j, ecarts)
                    total += 1
                if s.is_terminal():
                    break
                act = rng.choice(s.legal_actions())
                if rng.random() < 0.5:
                    appliquer(s, act)
                else:
                    s.apply(act)
    print(f"OK : {total} tenseurs identiques bit a bit, {len(CONFIGS)} configurations")
    e = Engine(COMPLETE)
    s = e.reset(1)
    for _ in range(20):
        s.apply(random.Random(0).choice(s.legal_actions()))
    for f in (tenseur, tenseur_rapide):
        t = time.perf_counter()
        for _ in range(2000):
            f(s, 0)
        print(f.__name__, f"{(time.perf_counter() - t) / 2000 * 1e6:.0f} us")


if __name__ == "__main__":
    main()
