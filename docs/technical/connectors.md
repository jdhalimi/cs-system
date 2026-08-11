# Connecteurs et sécurité

## Google

Google utilise OAuth. Le fichier client peut être partagé avec les autres
outils de la résidence, mais `cs-system` conserve son jeton dans `.state/`.
Les scopes doivent rester limités au pipeline exécuté.

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
