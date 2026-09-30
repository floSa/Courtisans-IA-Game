# Les journaux bruts des campagnes de mutation de la phase 4

Ce dossier garde **tous** les jeux payes, valides comme invalides, sous leur propre nom.
Un releve qu'on ne peut pas recompter soi-meme n'est pas un releve.

## Les deux jeux VALIDES, cote a cote

| Fichier | Jeu | Passe de base | Temoin |
|---|---|---|---|
| `mutations_campagne_VALIDE_jeu3.log` | 3 | 1240 verts, 0 rouges | 1 temoin, 1240 verts |
| `mutations_campagne_VALIDE_jeu5.log` | 5 | 1251 verts, 0 rouges | 20 temoins, 1251 verts |

Les deux sont ici pour une seule raison : **la reproduction est le resultat qui compte le
plus de l'etape 0**, et elle ne se verifie qu'en ayant les deux relevés sous la main.

### Recompter la reproduction soi-meme

Depuis ce dossier :

```bash
diff <(awk 'NF>=4 && ($2 ~ /^[0-9]+$/ || $2=="-") {print $1, $3, $4}' mutations_campagne_VALIDE_jeu3.log) <(awk 'NF>=4 && ($2 ~ /^[0-9]+$/ || $2=="-") {print $1, $3, $4}' mutations_campagne_VALIDE_jeu5.log)
```

Sortie attendue : **rien**. Les 57 lignes portent le meme nom, le meme nombre de rouges et
le meme verdict. C'est ce qui etablit que les verdicts sont reproductibles et non seulement
justes.

Et pour l'ecart des verts, qui lui n'est pas nul :

```bash
join <(awk 'NF>=4 && $2 ~ /^[0-9]+$/ {print $1, $2}' mutations_campagne_VALIDE_jeu3.log | sort) <(awk 'NF>=4 && $2 ~ /^[0-9]+$/ {print $1, $2}' mutations_campagne_VALIDE_jeu5.log | sort) | awk '{print $3-$2}' | sort | uniq -c
```

Sortie attendue : **`56 11`** -- les 56 mutations qui rendent un compte gagnent toutes
exactement **+11 verts**, qui est le nombre de cas ajoutes entre les deux jeux. La 57e
(`masse-binomiale-part-de-zero`) ne rend aucun compte : elle EXPIRE.

Un ecart de verts **uniforme** est ce qu'on attend d'une suite qui a grossi ; un ecart qui
varierait d'une mutation a l'autre dirait que les cas ajoutes reagissent aux mutations, et
il faudrait alors les regarder un par un.

## Les jeux INVALIDES, gardes expres

| Fichier | Ce qu'il montre |
|---|---|
| `mutations_campagne1_sans_passe_de_base_1.log` | jeu 1, bloque : pas de delai de garde |
| `mutations_campagne1_sans_passe_de_base_2.log` | la reprise du jeu 1, meme defaut |
| `mutations_rejeu_INVALIDE_deux_tests_miroirs.log` | jeu 2 : deux cas lisaient le disque, +2 rouges partout |
| `mutations_campagne_INVALIDE_head_empoisonne.log` | jeu 4 : un commit en vol a fige une mutation dans le code |

Ils sont gardes parce qu'un releve invalide **nomme le defaut de l'instrument** qui l'a
produit, et que ce defaut est le vrai resultat de l'etape 0.
