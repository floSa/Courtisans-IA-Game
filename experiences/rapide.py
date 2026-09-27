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
from courtisans.cards import ROLES_CACHES, VALEURS, GenreZone, Position
from courtisans.engine import Phase, State

_BANQUET = GenreZone.BANQUET
_POSITIONS = tuple(Position)


def tenseur_rapide_v1(etat: State, joueur: int) -> list[float]:
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


_DISPOSITIONS: dict = {}


def _disposition(config):
    """Les index precalcules d'une configuration : (famille, role) -> rang, etc."""
    cle = (config.familles, config.roles, config.joueurs)
    if cle not in _DISPOSITIONS:
        roles = config.roles
        visibles = infoset._roles_visibles(config)
        _DISPOSITIONS[cle] = (
            {r: i for i, r in enumerate(roles)},
            {r: i for i, r in enumerate(visibles)},
            {p: i for i, p in enumerate(_POSITIONS)},
            len(roles),
            len(visibles),
        )
    return _DISPOSITIONS[cle]


def tenseur_rapide(etat: State, joueur: int) -> list[float]:
    """`infoset.tenseur`, en UNE passe sur les cartes. Egal bit a bit (experiences/test_rapide.py).

    Les marges et les scores visibles sont tires des memes comptes : influence par famille au
    banquet (valeurs signees, Espions du joueur compris -- ce sont des cartes connues) et
    valeur par domaine et par famille, puis statut = signe de l'influence.
    """
    etat._joueur_observe(joueur)
    config = etat.config
    J = config.joueurs
    F = config.familles
    ridx, rvidx, pidx, R, RV = _disposition(config)
    P = len(_POSITIONS)
    main = [0] * (F * R)
    morts = [0] * (F * R)
    connues = [0] * (F * R)
    bv = [0] * (F * RV * P)
    dv = [0] * (F * RV * J)
    bp = [0] * (F * P)
    dp = [0] * (F * J)
    infl = [0] * F
    dom = [[0] * F for _ in range(J)]
    dos_b = [0] * ((J - 1) * P)
    dos_d = [0] * ((J - 1) * J)
    dos_estime = dos_disgrace = 0
    for c in etat._mains[joueur]:
        main[c.famille * R + ridx[c.role]] += 1
    for p in etat._defausse:
        c = p.carte
        morts[c.famille * R + ridx[c.role]] += 1
    for p in etat._posees:
        c = p.carte
        z = p.zone
        cache = c.role in ROLES_CACHES
        if cache and p.poseur != joueur:
            autre = (p.poseur - joueur) % J
            if z.genre is _BANQUET:
                dos_b[(autre - 1) * P + pidx[z.position]] += 1
                if z.position is Position.ESTIME:
                    dos_estime += 1
                else:
                    dos_disgrace += 1
            else:
                dos_d[(autre - 1) * J + (z.proprietaire - joueur) % J] += 1
            continue
        f = c.famille
        connues[f * R + ridx[c.role]] += 1
        v = VALEURS[c.role]
        if z.genre is _BANQUET:
            pi = pidx[z.position]
            infl[f] += v if z.position is Position.ESTIME else -v
            if cache:
                bp[f * P + pi] += 1
            else:
                bv[(f * RV + rvidx[c.role]) * P + pi] += 1
        else:
            autre = (z.proprietaire - joueur) % J
            dom[z.proprietaire][f] += v
            if cache:
                dp[f * J + autre] += 1
            else:
                dv[(f * RV + rvidx[c.role]) * J + autre] += 1
    ex = config.exemplaires
    residu = [ex - connues[i] - main[i] - morts[i] for i in range(F * R)]
    tours = [etat.tours_restants((joueur + a) % J) for a in range(J)]
    poses_restantes = sum(tours)
    marges = []
    for f in range(F):
        en_circulation = sum(residu[f * R : (f + 1) * R])
        en_main = sum(main[f * R : (f + 1) * R])
        d = infl[f]
        marges += (d, d - dos_disgrace, d + dos_estime,
                   min(en_main + en_circulation, poses_restantes))
    signe = [1 if d >= 1 else (-1 if d <= -1 else 0) for d in infl]
    points = [sum(dom[o][f] * signe[f] for f in range(F)) for o in range(J)]
    scores = [points[(joueur + a) % J] for a in range(J)]
    ecart = scores[0] - max(scores[1:], default=0)
    return [
        float(v)
        for bloc in (
            main, bv, bp, dv, dp, residu, morts, marges, dos_b, dos_d, tours,
            (len(etat._pioche),), (len(etat._defausse),), infoset._phase_one_hot(etat),
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
