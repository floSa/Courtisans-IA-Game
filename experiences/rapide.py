"""Chemins rapides, et SEULEMENT des chemins rapides : aucune regle n'est reecrite ici.

`tenseur_rapide` rend **exactement** `infoset.tenseur` -- meme ordre, memes valeurs -- mais
compte les cartes en une passe au lieu d'un balayage complet du plateau par composante
(~150 balayages par tenseur). L'egalite bit a bit est verifiee par
`experiences/test_rapide.py` sur les deux instances, tous sieges, toutes phases, terminal
compris. Les petits blocs (marges, scores visibles, phase, assassin) appellent les fonctions
de `infoset` elles-memes.

`appliquer` joue une action **deja tiree de `legal_actions()`** sans la re-verifier :
`State.apply` recalcule toute la liste des actions legales a chaque appel pour la valider.
"""

from __future__ import annotations

from courtisans import infoset
from courtisans.cards import ROLES_CACHES, GenreZone, Position
from courtisans.engine import Phase, State

_BANQUET = GenreZone.BANQUET
_POSITIONS = tuple(Position)


def tenseur_rapide(etat: State, joueur: int) -> list[float]:
    config = etat.config
    vue = etat.vue_privilegiee()
    su = infoset.vue_du_joueur(etat, joueur)
    joueurs = config.joueurs
    roles = config.roles
    roles_visibles = infoset._roles_visibles(config)

    compte_main = infoset._compte(vue.mains[joueur], config)
    compte_morts = infoset._compte((p.carte for p in vue.defausse), config)
    compte_connues = infoset._compte((p.carte for p in su.connues), config)

    # Une passe sur les cartes connues.
    banq: dict[tuple, int] = {}
    dom: dict[tuple, int] = {}
    banq_prive: dict[tuple, int] = {}
    dom_prive: dict[tuple, int] = {}
    for p in su.connues:
        c, z = p.carte, p.zone
        cache = c.role in ROLES_CACHES
        if z.genre is _BANQUET:
            k = (c.famille, c.role, z.position)
            banq[k] = banq.get(k, 0) + 1
            if cache:
                k2 = (c.famille, z.position)
                banq_prive[k2] = banq_prive.get(k2, 0) + 1
        else:
            autre = (z.proprietaire - joueur) % joueurs
            k = (c.famille, c.role, autre)
            dom[k] = dom.get(k, 0) + 1
            if cache:
                k2 = (c.famille, autre)
                dom_prive[k2] = dom_prive.get(k2, 0) + 1

    ma_main, bv, bp, dv, dp, residu, morts = [], [], [], [], [], [], []
    for f in range(config.familles):
        for r in roles:
            ma_main.append(compte_main[(f, r)])
            morts.append(compte_morts[(f, r)])
            residu.append(
                config.exemplaires
                - compte_connues[(f, r)]
                - compte_main[(f, r)]
                - compte_morts[(f, r)]
            )
        for r in roles_visibles:
            for pos in _POSITIONS:
                bv.append(banq.get((f, r, pos), 0))
            for autre in range(joueurs):
                dv.append(dom.get((f, r, autre), 0))
        for pos in _POSITIONS:
            bp.append(banq_prive.get((f, pos), 0))
        for autre in range(joueurs):
            dp.append(dom_prive.get((f, autre), 0))

    marges = infoset._marges(etat, joueur, su, compte_main, config)

    dos_b: dict[tuple, int] = {}
    dos_d: dict[tuple, int] = {}
    for p in su.dos_adverses:
        z = p.zone
        if z.genre is _BANQUET:
            k = (p.poseur, z.position)
            dos_b[k] = dos_b.get(k, 0) + 1
        else:
            k = (p.poseur, z.proprietaire)
            dos_d[k] = dos_d.get(k, 0) + 1
    dos_banquet, dos_domaine = [], []
    for autre in range(1, joueurs):
        poseur = (joueur + autre) % joueurs
        for pos in _POSITIONS:
            dos_banquet.append(dos_b.get((poseur, pos), 0))
        for domaine in range(joueurs):
            dos_domaine.append(dos_d.get((poseur, (joueur + domaine) % joueurs), 0))

    tours = [etat.tours_restants((joueur + a) % joueurs) for a in range(joueurs)]
    scores = infoset._scores_visibles(su, joueur, config)
    ecart = scores[0] - max(scores[1:], default=0)
    return [
        float(v)
        for bloc in (
            ma_main, bv, bp, dv, dp, residu, morts, marges, dos_banquet, dos_domaine, tours,
            (len(vue.pioche),), (len(vue.defausse),), infoset._phase_one_hot(etat),
            infoset._assassin_one_hot(etat.assassin_en_resolution(), joueur, config),
            (infoset._assassins_restants(etat),), scores, (ecart,),
        )
        for v in bloc
    ]


def appliquer(etat: State, action: int) -> None:
    """`State.apply` sans la re-verification de legalite. L'action DOIT venir de
    `legal_actions()` sur ce meme etat."""
    phase = etat._phase
    if phase is Phase.POSE:
        etat._poser(action)
    elif phase is Phase.CIBLAGE:
        etat._resoudre_assassin(action)
    else:
        etat.apply(action)
