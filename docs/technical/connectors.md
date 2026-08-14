# Connecteurs et sécurité

## Google

Google utilise OAuth. Le fichier client peut être partagé avec les autres
outils de la résidence, mais `cs-system` conserve son jeton dans `.state/`.

Le jeton est partagé entre tous les pipelines Google et accumule les scopes au
fil des autorisations (Drive, Contacts) : `google_service()` détecte les
scopes manquants par rapport à ce qui a réellement été accordé et redemande un
consentement combiné plutôt que d'écraser un scope déjà obtenu.

Le scope Drive est `drive` (accès complet), pas `drive.file` : ce dernier ne
rend visibles que les fichiers créés par l'application elle-même, ce qui
empêche d'atteindre un dossier Drive existant (ex. un dossier MyCYTIA déjà
synchronisé manuellement).

## Notion

Utiliser une intégration interne partagée uniquement avec les bases nécessaires.
La lecture et l'écriture demandent des droits distincts. Toute modification doit
être précédée d'un diff validé.

## MyCitya

Le connecteur utilise Playwright pour établir ou réutiliser une session, puis
l'API GED MyCitya pour parcourir et télécharger les documents. La session et le
manifeste sont stockés dans `.state/`.

Ne pas loguer les mots de passe, jetons, URLs temporaires ou contenus de
documents dans les rapports techniques.
