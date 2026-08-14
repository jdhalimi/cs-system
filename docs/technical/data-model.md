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

## Exports Google

`data/exports/google/drive/manifest.json` est le relevé réel du dossier Drive
configuré (chemin, id, empreinte si connue, date de dépôt), régénéré par
`google-drive index` ou après chaque `citya-docs capture --apply`. Les fichiers qui
n'ont pas été déposés par `cs-system` (synchronisation manuelle) n'ont pas
d'empreinte : le dédoublonnage retombe alors sur une correspondance de chemin,
arbitrée par comparaison de dates (cf. guide des flux de travail).

`data/exports/google/contacts/contacts.csv` est l'export des Google Contacts
(`google-contacts export`), au format des exports Google natifs.

## Exports Notion

`notion-contacts export` écrit `data/exports/notion/proprietaires/proprietaires.csv`
et `data/exports/notion/locataires/locataires.csv` ; `notion-lots export` écrit
`data/exports/notion/lots/lots.csv`. Chaque export porte une colonne
`_notion_id` (identifiant de page Notion) en plus des propriétés telles
quelles ; les relations (`Lots`, `Lots loues`) restent des listes
d'identifiants de page, résolues à la volée par `match contacts` via
`_notion_id` — jamais réécrites dans les exports eux-mêmes.

## Rapprochement des contacts

`match contacts` lit les quatre exports ci-dessus (Google, Proprietaires,
Locataires, Lots) et écrit `data/local/contacts-match.csv` par défaut : une
ligne par identité, avec un statut (`commun`, `rapproche_email`,
`rapproche_label`, `rapproche_manuel`, `google_seul`, `notion_seul`) et une
colonne `anomalies`. Les contacts Google appartenant aux groupes listés dans
`config.toml` (`[matching].ignored_google_labels`, par défaut `Ancien`,
`Syndic` et `Fournisseurs`) sont exclus avant tout rapprochement. C'est un
résultat de `data/local/`, reconstructible à volonté — il ne modifie aucun
export.

Le rapprochement s'appuie sur une convention observée dans les groupes Google
de ce compte : un label `Propriétaire <lettre><chiffre>` (ex. `Propriétaire
A1`) désigne un escalier précis, `Propriétaire P` un parking sans
localisation. Pour chaque personne Notion, `match contacts` reconstitue
l'escalier ou le parking attendu à partir de ses lots (colonne `Escalier` et
`Type` de `lots.csv`, via `_notion_id`) et de son rôle. Ce label reconstitué
sert d'abord de troisième critère de rapprochement (`rapproche_label`) : quand
le nom et l'email n'ont rien donné, une fiche Google restante est associée à
la fiche Notion restante qui reconstitue le même label, à condition que ce
soit la seule candidate des deux côtés (ambigu sinon, laissé de côté). Une
fois une paire établie (par nom, email ou label), une divergence entre le
label Google et les lots réels de la personne, ou entre le rôle Google
(Propriétaire/Locataire) et le rôle Notion, est signalée en anomalie.
