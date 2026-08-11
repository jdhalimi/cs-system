# Données et index

## Répertoires

| Répertoire | Contenu | Durée de vie |
| --- | --- | --- |
| `data/exports/` | fichiers sources bruts et datés | immuable |
| `data/cache/` | réponses API normalisées | remplaçable |
| `data/indexes/` | catalogues JSON et SHA-256 | reconstruisible |
| `data/local/` | résultats de traitements | reconstruisible ou arbitrable |
| `reports/` | restitution humaine | conservée selon besoin |
| `.state/` | jetons, sessions et curseurs | privée, non versionnée |

## Index d'exports

`sync-index` écrit un index par source dans
`data/indexes/<source>/exports.json`. Chaque entrée contient le chemin relatif,
l'entité, la taille, l'horodatage et l'empreinte SHA-256 du fichier.

Une empreinte sert au dédoublonnage et au contrôle d'intégrité ; elle ne doit
pas être traitée comme un identifiant métier.
