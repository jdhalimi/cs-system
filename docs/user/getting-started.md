# Démarrage

## Prérequis

Le projet utilise l'environnement Mamba `cs-system` :

```powershell
make env
Copy-Item .env.example .env
```

Renseigner uniquement les variables correspondant aux connecteurs utilisés.
Les secrets de `.env` ne doivent jamais être partagés ni versionnés.

## Initialiser le poste

```powershell
mamba run -n cs-system cs-system workspace-init
```

Cette commande crée l'espace de données local. Il est ignoré par Git car il
peut contenir des données personnelles et des documents de la résidence.

## Première capture Citya

Configurer les quatre variables `CITYA_*` dans `.env`, puis exécuter :

`CITYA_IMMEUBLE_ID` n'est pas la référence d'immeuble affichée sur le site
(ex. `0491`), mais l'identifiant technique encodé dans `CITYA_DOCUMENTS_URL`
(le premier segment `documents-syndic-<ID>-<...>.html`). Utiliser la
référence affichée provoque une erreur GED silencieuse (`responseCode: 500`)
lors de `citya-docs export`.

```powershell
mamba run -n cs-system cs-system citya-docs export --new
```

Le navigateur s'ouvre seulement si nécessaire. Ajouter `--headed` pour le voir
pendant une connexion ou un diagnostic.
