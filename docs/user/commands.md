# Commandes

## Espace de travail

```powershell
cs-system workspace-init
cs-system sync-index [--source notion|google|citya|forms]
```

## Citya et Drive

```powershell
cs-system citya-docs export [--new] [--headed]
cs-system citya-docs capture [--apply]
cs-system google-drive index
```

`google-drive index` reindexe le contenu reel du dossier Drive configure (sans rien
envoyer) dans `data/exports/google/drive/manifest.json`. `citya-docs capture`
s'en sert, avec les empreintes SHA-256 et les dates des documents, pour ne
proposer que les documents realement absents ou mis a jour cote Citya.

## Google Contacts

```powershell
cs-system google-contacts export
```

Exporte les contacts Google (noms, emails, telephones et tags de
classification issus des groupes de contacts) dans
`data/exports/google/contacts/contacts.csv`, au format compatible avec
`compare-contacts`.

## Notion Contacts et Lots

```powershell
cs-system notion-contacts export
cs-system notion-lots export
```

`notion-contacts export` exporte les bases Notion `NOTION_PROPRIETAIRES_DATABASE_ID`
et `NOTION_LOCATAIRES_DATABASE_ID` telles quelles (une colonne par propriete
Notion) dans `data/exports/notion/proprietaires/proprietaires.csv` et
`data/exports/notion/locataires/locataires.csv`. `notion-lots export` fait de
meme pour `NOTION_LOTS_DATABASE_ID` dans `data/exports/notion/lots/lots.csv`.

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
