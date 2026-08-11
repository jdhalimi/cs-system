# Flux de travail

## Documents Citya vers Drive

```text
citya-sync → exports Citya → capture-documents → validation → Drive
```

1. `citya-sync --new` télécharge les documents inconnus dans les exports.
2. `capture-documents` affiche le plan d'envoi et les empreintes des fichiers.
3. Vérifier ce plan.
4. Relancer `capture-documents --apply` pour envoyer les fichiers vers Drive.

L'envoi est dédoublonné par empreinte SHA-256.

## Exports et index

Après l'ajout ou la synchronisation d'exports :

```powershell
mamba run -n cs-system cs-system sync-index
```

Les index permettent de retrouver les snapshots, leur taille et leur empreinte,
sans altérer les fichiers sources.

## Contacts et formulaires

`compare-contacts` produit une première comparaison locale de deux exports CSV.
`ingest-form` transforme un export Google Forms en registre d'actions. Ces deux
commandes n'écrivent dans aucune API externe.
