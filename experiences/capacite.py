"""Le reseau de valeur est-il trop petit ? Trois architectures, memes donnees, meme validation.

Apprentissage : iteration4/gen_03 + iteration5/gen_01 (auto-jeu contre la ligue, cible MC).
Validation : 600 000 vues de iteration5/gen_02, donc d'AUTRES parties. Metrique : R2 du gain.
C'est un indicateur, pas un juge : seul le gain en partie decide.

    COURTISANS_INSTANCE=complete uv run python -m experiences.capacite
"""
import json
import time

import numpy as np
import torch
from torch import nn

from experiences.valeur import ENTREE

D = "experiences/donnees/"


def reseau(largeurs):
    couches, entree = [], ENTREE
    for w in largeurs:
        couches += [nn.Linear(entree, w), nn.ReLU()]
        entree = w
    return nn.Sequential(*couches, nn.Linear(entree, 2))


def charger(fichiers, n_max=None):
    xs, ys = [], []
    for f in fichiers:
        b = np.load(f)
        n = len(b["G"]) if n_max is None else min(n_max, len(b["G"]))
        xs.append(b["X"][:n])
        ys.append(np.stack([b["G"][:n], b["M"][:n] / 5.0], 1))
    return np.concatenate(xs), np.concatenate(ys)


def main():
    dev = torch.device("cuda")
    Xa, Ya = charger([D + "iteration4/gen_03.npz", D + "iteration5/gen_01.npz"])
    Xv, Yv = charger([D + "iteration5/gen_02.npz"], 600_000)
    Xa = torch.tensor(Xa, dtype=torch.float16, device=dev)
    Ya = torch.tensor(Ya, device=dev)
    Xv = torch.tensor(Xv, dtype=torch.float32, device=dev)
    gv = torch.tensor(Yv[:, 0], device=dev)
    var = float(gv.var())
    for nom, larg in [("512-512-256 (actuel)", [512, 512, 256]),
                      ("1024-1024-512", [1024, 1024, 512]),
                      ("512 x 5", [512] * 5)]:
        torch.manual_seed(0)
        net = reseau(larg).to(dev)
        opt = torch.optim.AdamW(net.parameters(), lr=1e-3, weight_decay=1e-4)
        epoques, lot = 4, 4096
        n = len(Xa)
        sched = torch.optim.lr_scheduler.OneCycleLR(opt, 1e-3, total_steps=epoques * (n // lot))
        t = time.time()
        r2s = []
        for _ in range(epoques):
            perm = torch.randperm(n, device=dev)
            net.train()
            for i in range(0, n - lot + 1, lot):
                idx = perm[i:i + lot]
                loss = ((net(Xa[idx].float()) - Ya[idx]) ** 2).mean()
                opt.zero_grad()
                loss.backward()
                opt.step()
                sched.step()
            net.eval()
            with torch.no_grad():
                p = torch.cat([net(Xv[i:i + 65536])[:, 0] for i in range(0, len(Xv), 65536)])
            r2s.append(round(1 - float(((p - gv) ** 2).mean()) / var, 4))
        ligne = {"reseau": nom, "apprentissage": n, "r2_validation_par_epoque": r2s,
                 "secondes": round(time.time() - t)}
        print(json.dumps(ligne, ensure_ascii=False), flush=True)
        with open("experiences/resultats/capacite.jsonl", "a") as f:
            f.write(json.dumps(ligne, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
