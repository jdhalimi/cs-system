# Flux de travail

## Documents Citya vers Drive

```text
citya export → exports Citya → citya capture → validation → Drive
```

1. `citya export --new` télécharge les documents inconnus dans les exports, avec
   leur date réelle (`dateCreated` Citya, pas la date de téléchargement).
2. `citya capture` affiche le plan d'envoi et les empreintes des fichiers.
3. Vérifier ce plan.
4. Relancer `citya capture --apply` pour envoyer les fichiers vers Drive.

L'arborescence Drive suit celle des catégories Citya (Ag cs, Factures…), sans
répéter le nom de l'immeuble — elle fusionne avec un dossier déjà synchronisé
manuellement plutôt que de le dupliquer.

Un document est considéré comme déjà présent, et donc ignoré, s'il correspond
par empreinte SHA-256 **ou** par chemin (dossier + nom) à ce que
`google export --scope drive` a trouvé sur Drive — sauf si sa date locale est
plus récente que la date de dépôt sur Drive à ce même chemin, auquel cas il
est repris dans le plan (probable mise à jour côté Citya sous le même nom).

Lancer `google export --scope drive` seul pour rafraîchir
`data/exports/google/drive/manifest.json` sans envoyer de document, par
exemple après une synchronisation manuelle.

## Exports et index

Après l'ajout ou la synchronisation d'exports :

```powershell
mamba run -n cs-system cs-system sync-index
```

Les index permettent de retrouver les snapshots, leur taille et leur empreinte,
sans altérer les fichiers sources.

## Contacts et formulaires

`google export --scope contacts` exporte les Google Contacts vers
`data/exports/google/contacts/contacts.csv`, avec les tags de classification
(groupes de contacts définis par l'utilisateur, ex. « Propriétaire A1 »,
« Locataire B3 ») dans la colonne `Labels` ; les groupes système
(`myContacts`, `starred`…) sont exclus.

`notion export` découvre et exporte toutes les bases Notion partagées avec
l'intégration (tout par défaut, ou un sous-ensemble via `--scope`, ex.
`--scope proprietaires,locataires,lots`) — partager une nouvelle base dans
Notion suffit, aucune configuration côté `cs-system`. Ces exports sont
indépendants des Google Contacts et ne nécessitent qu'un jeton Notion.

`match contacts` rapproche ensuite l'export Google et les exports Notion
Proprietaires + Locataires + Lots (à exécuter avant) : nom normalisé d'abord,
puis email partagé pour ce qui reste. Les contacts Google marqués
`Fournisseurs` sont ignorés d'emblée. Avec `--interactive`, les entrées
isolées proches d'un nom de l'autre source sont proposées une par une pour une
confirmation manuelle, sans jamais écrire dans Google ni Notion. C'est un
rapprochement plus fin que `compare-contacts`, qui reste utile pour comparer
deux exports CSV quelconques au nom seul.

Pour chaque identité rapprochée, `match contacts` signale dans la colonne
`anomalies` un téléphone manquant d'un côté ou de l'autre, ainsi qu'un écart
entre le label Google (`Propriétaire A1`, `Locataire B3`, `Propriétaire P`
pour un parking) et les lots réellement associés à la personne dans Notion —
mauvais rôle ou mauvais escalier.

`ingest-form` transforme un export Google Forms en registre d'actions. Aucune
de ces commandes n'écrit dans une API externe.
