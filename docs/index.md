# cs-system

`cs-system` centralise les opérations de données du conseil syndical :
documents MyCitya, Google Drive et Contacts, Notion et Google Forms.

Le système protège les données sources et sépare strictement collecte,
traitement local, validation et écriture distante.

## Commencer

1. Installer l'environnement avec `make env`.
2. Copier `.env.example` dans `.env` et renseigner les accès nécessaires.
3. Créer les répertoires locaux avec `cs-system workspace-init`.
4. Consulter le [guide de démarrage](user/getting-started.md).

## Principes

- Aucun export brut n'est modifié.
- Les rapprochements n'écrivent dans aucun système externe.
- Toute écriture dans Drive, Google Contacts ou Notion doit être validée puis
  lancée explicitement avec `--apply`.
