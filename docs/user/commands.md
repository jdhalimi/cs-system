# Commandes

## Espace de travail

```powershell
cs-system workspace-init
cs-system sync-index [--source notion|google|citya|forms]
```

## Citya et Drive

```powershell
cs-system citya-sync [--new] [--headed]
cs-system capture-documents [--apply]
```

## Données locales

```powershell
cs-system compare-contacts google.csv notion.csv --out data/local/contacts/diff.csv
cs-system ingest-form reponses.csv --out data/local/forms/actions.csv
```

Utiliser `cs-system <commande> --help` pour l'aide détaillée.
