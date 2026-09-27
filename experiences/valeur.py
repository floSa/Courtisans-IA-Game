"""Reseau de valeur d'apres-coup, et l'agent qui s'en sert.

V(vue du siege j) -> (gain final attendu de j, ecart de score final / 5).
L'agent evalue CHAQUE action legale par la vue de l'etat qui en resulte : l'action n'est
jamais un indice a interpreter, c'est sa consequence qui est notee. Le ciblage de
l'Assassin cesse donc d'etre aveugle par construction.
"""
import argparse
import random

import numpy as np
import torch
from torch import nn

from courtisans.engine import Engine, Phase
from experiences.config import CONFIG
from experiences.pimc import determiniser
from experiences.rapide import appliquer
from experiences.rapide import tenseur_rapide as tenseur

ENTREE = len(tenseur(Engine(CONFIG).reset(0), 0))


class V(nn.Module):
    def __init__(self, largeur=512):
        super().__init__()
        self.f = nn.Sequential(
            nn.Linear(ENTREE, largeur), nn.ReLU(),
            nn.Linear(largeur, largeur), nn.ReLU(),
            nn.Linear(largeur, 256), nn.ReLU(),
            nn.Linear(256, 2),
        )

    def forward(self, x):
        return self.f(x)


def entrainer(chemins, sortie, epoques=6, lot=4096, lr=1e-3):
    X = np.concatenate([np.load(c)["X"] for c in chemins])
    G = np.concatenate([np.load(c)["G"] for c in chemins])
    M = np.concatenate([np.load(c)["M"] for c in chemins])
    n = len(X)
    coupe = int(0.92 * n)  # donnes contigues : la fin est faite d'autres parties
    dev = torch.device("cuda")
    Xt = torch.tensor(X, dtype=torch.float16, device=dev)
    Y = torch.tensor(np.stack([G, M / 5.0], 1), dtype=torch.float32, device=dev)
    net = V().to(dev)
    opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=1e-4)
    etapes = epoques * (coupe // lot)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, lr, total_steps=etapes)
    var_g = float(Y[coupe:, 0].var())
    for ep in range(epoques):
        perm = torch.randperm(coupe, device=dev)
        net.train()
        for i in range(0, coupe - lot + 1, lot):
            idx = perm[i:i + lot]
            p = net(Xt[idx].float())
            loss = ((p - Y[idx]) ** 2).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
        net.eval()
        with torch.no_grad():
            mse = 0.0
            for i in range(coupe, n, 65536):
                p = net(Xt[i:i + 65536].float())
                mse += float(((p[:, 0] - Y[i:i + 65536, 0]) ** 2).sum())
            mse /= n - coupe
        print(f"epoque {ep} mse_gain_val {mse:.4f}  R2 {1 - mse / var_g:.4f}", flush=True)
    torch.save(net.cpu().state_dict(), sortie)


_CACHE = {}


def _charger(chemin):
    if chemin not in _CACHE:
        torch.set_num_threads(1)
        net = V()
        net.load_state_dict(torch.load(chemin, map_location="cpu"))
        net.eval()
        _CACHE[chemin] = net
    return _CACHE[chemin]


def agent_valeur(rng, chemin, poids_ecart=0.05, temperature=0.0, mondes_ciblage=8, aveugle=True):
    net = _charger(chemin)

    def pol(etat):
        moi = etat.current_player()
        legales = etat.legal_actions()
        if len(legales) == 1:
            return legales[0]
        # Au CIBLAGE, tuer un dos adverse le revele (defausse publique) : noter l'apres-coup
        # sur l'etat REEL ferait voir l'identite de la victime avant de choisir. On note donc
        # chaque action en moyenne sur des mondes tires a l'aveugle. En POSE, l'apres-coup ne
        # revele rien (controle : experiences/fuite_terminal.py), un seul monde suffit.
        if aveugle and etat.phase() is Phase.CIBLAGE:
            mondes = [determiniser(etat, moi, rng) for _ in range(mondes_ciblage)]
        else:
            mondes = [etat]
        vues = []
        for monde in mondes:
            for a in legales:
                s = monde.clone()
                appliquer(s, a)
                vues.append(tenseur(s, moi))
        with torch.no_grad():
            p = net(torch.from_numpy(np.asarray(vues, dtype=np.float32)))
        p = p.view(len(mondes), len(legales), 2).mean(0)
        score = (p[:, 0] + poids_ecart * p[:, 1]).tolist()
        if temperature > 0:
            m = max(score)
            w = [np.exp((x - m) / temperature) for x in score]
            return rng.choices(legales, weights=w)[0]
        m = max(score)
        return rng.choice([a for a, x in zip(legales, score, strict=True) if x == m])

    return pol


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("sortie")
    ap.add_argument("donnees", nargs="+")
    ap.add_argument("--epoques", type=int, default=6)
    a = ap.parse_args()
    entrainer(a.donnees, a.sortie, a.epoques)


def agent_ppo_phase3(rng, chemin="models/phase3/final.pt"):
    """L'agent PPO de la phase 3, pour situer les nouveaux agents sur la meme arene."""
    from agents.politique_reseau import charger, politique_reseau
    if chemin not in _CACHE:
        torch.set_num_threads(1)
        _CACHE[chemin] = charger(chemin, ENTREE, 24)
    return politique_reseau(_CACHE[chemin], rng)


def pimc_valeur(rng, chemin, nb_mondes=8, poids_ecart=0.05, adversaires="greedy"):
    """Recherche + valeur : PIMC tronque a UN tour de table, feuilles notees par V.

    Pour chaque monde tire a l'aveugle et chaque action legale : jouer l'action, laisser les
    adversaires repondre (greedy, rapide) jusqu'a ma prochaine decision de POSE -- ou la fin --,
    puis noter la vue qui en resulte par V. La vue de ma prochaine pose contient ma NOUVELLE
    main, tiree dans ce monde : c'est ce que l'apres-coup seul ne voit pas.
    """
    net = _charger(chemin)
    from agents import greedy
    from agents.perception import percevoir

    def pol(etat):
        moi = etat.current_player()
        legales = etat.legal_actions()
        if len(legales) == 1:
            return legales[0]
        vues = []
        for _ in range(nb_mondes):
            monde = determiniser(etat, moi, rng)
            r = random.Random(rng.random())
            if adversaires == "valeur":
                # Les adversaires simules par la politique apprise elle-meme : c'est ce qui
                # fait de la recherche une amelioration, et non une exploitation du greedy.
                simule = agent_valeur(r, chemin, poids_ecart=poids_ecart, mondes_ciblage=2)
            else:
                def simule(s, r=r):
                    return greedy.choisir(percevoir(s, s.current_player()), r)
            for a in legales:
                s = monde.clone()
                appliquer(s, a)
                while not s.is_terminal() and not (
                    s.current_player() == moi and s.phase() is Phase.POSE
                ):
                    s.apply(simule(s))
                vues.append(tenseur(s, moi))
        with torch.no_grad():
            p = net(torch.from_numpy(np.asarray(vues, dtype=np.float32)))
        p = p.view(nb_mondes, len(legales), 2).mean(0)
        score = (p[:, 0] + poids_ecart * p[:, 1]).tolist()
        m = max(score)
        return rng.choice([a for a, x in zip(legales, score, strict=True) if x == m])

    return pol
