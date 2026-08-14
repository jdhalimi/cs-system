# Commandes

## Espace de travail

```powershell
cs-system workspace-init
cs-system sync-index [--source notion|google|citya|forms]
```

## Citya et Drive

```powershell
cs-system citya export [--new] [--headed]
cs-system citya capture [--apply]
cs-system google export --scope drive
```

`google export --scope drive` reindexe le contenu reel du dossier Drive configure
(sans rien envoyer) dans `data/exports/google/drive/manifest.json`. `citya
capture` s'en sert, avec les empreintes SHA-256 et les dates des documents,
pour ne proposer que les documents realement absents ou mis a jour cote
Citya.

## Google

```powershell
cs-system google export [--scope contacts,drive]
```

Sans `--scope`, exporte/reindexe tout : les Google Contacts (noms, emails,
telephones et tags de classification issus des groupes de contacts) dans
`data/exports/google/contacts/contacts.csv`, au format compatible avec
`compare-contacts`, et le dossier Drive (voir ci-dessus). `--scope` limite a
un sous-ensemble separe par des virgules, ex. `--scope contacts`.

## Notion

```powershell
cs-system notion export [--scope slug1,slug2,...]
```

Sans `--scope`, decouvre et exporte telles quelles (une colonne par propriete
Notion) **toutes** les bases Notion partagees avec l'integration — aucune
configuration prealable n'est necessaire cote `cs-system` : partager une
nouvelle base dans Notion suffit a ce qu'elle apparaisse au prochain export.
Chaque base est ecrite dans `data/exports/notion/<slug>/<slug>.csv`, ou
`<slug>` est son titre Notion normalise (minuscule, espaces remplaces par
`_`, accents retires) — ex. `Propriétaires` -> `proprietaires`, `Factures
2025` -> `factures_2025`. `--scope` limite l'export a un sous-ensemble de
slugs separes par des virgules, ex. `--scope lots,factures_2025`.

## Rapprochements

```powershell
cs-system match contacts [--interactive] [--out chemin.csv]
```

Rapproche l'export Google Contacts et les exports Notion Proprietaires +
Locataires + Lots (executer les exports ci-dessus au prealable). Les contacts
Google du groupe `Fournisseurs` sont ignores. Le rapprochement se fait par nom
normalise, puis par email partage pour les entrees restantes. Avec
`--interactive`, chaque entree encore isolee et dotee d'un nom proche cote de
l'autre source est proposee pour confirmation manuelle (numero du candidat,
`Entree` pour ignorer, `q` pour arreter la revue). Sortie par defaut :
`data/local/contacts-match.csv`. N'ecrit dans aucune API externe.

Pour chaque identite rapprochee, la colonne `anomalies` signale :
- un telephone absent d'un cote ou de l'autre ;
- un role Google (`Propriétaire`/`Locataire <lettre><chiffre>`, ex.
  `Propriétaire A1`) qui ne correspond pas au role Notion reel ;
- un escalier Google qui ne correspond a aucun lot Notion de la personne
  (`Propriétaire P` designe un parking, sans escalier precis).

## Données locales

```powershell
cs-system compare-contacts google.csv notion.csv --out data/local/contacts/diff.csv
cs-system ingest-form reponses.csv --out data/local/forms/actions.csv
```

Utiliser `cs-system <commande> --help` pour l'aide détaillée.
