# Guide des agents — cs-system

## Objet

`cs-system` est la plateforme autonome de gestion des données du conseil
syndical. Elle synchronise MyCitya, Google (Contacts et Drive) et Notion ; elle
effectue ensuite des traitements locaux, des validations, puis — seulement sur
demande explicite — des écritures distantes.

Ce fichier s'adresse indifféremment à Codex, Claude et aux autres agents qui
interviennent dans ce dépôt. Les décisions et commentaires métier sont rédigés
en français.

## Prérequis

Utiliser exclusivement l'environnement Mamba `cs-system` :

```powershell
mamba run -n cs-system cs-system --help
mamba run -n cs-system python -m pytest --cov -q --basetemp .test-tmp-<run>
```

La définition reproductible se trouve dans `environment.yml`. Après une
création d'environnement, installer le navigateur nécessaire à MyCitya :

```powershell
mamba run -n cs-system playwright install chromium
```

Ne pas utiliser l'interpréteur système ni créer un environnement virtuel local.

## Configuration et secrets

- Copier `.env.example` en `.env` et ne jamais versionner ce dernier.
- Les jetons OAuth Google, le secret Notion et les identifiants MyCitya restent
  dans `.env` ou `.state/` ; ne jamais les afficher dans une sortie ou un rapport.
- Les appels API et les authentifications navigateur ne sont pas des tests : ne
  les déclencher que lorsqu'ils sont nécessaires à la tâche demandée.

## Architecture obligatoire

Le sens du flux est immuable :

```text
sync → exports/cache/indexes → local → validate → inject
```

| Zone | Rôle | Règle |
| --- | --- | --- |
| `data/exports/` | snapshots bruts datés | jamais modifiés |
| `data/cache/` | réponses techniques remplaçables | reconstruisibles |
| `data/indexes/` | catalogues JSON et empreintes | reconstruisibles |
| `data/local/` | résultats des traitements locaux | aucune écriture distante |
| `reports/` | rapports destinés aux humains | datés et explicites |
| `.state/` | sessions, curseurs et manifestes | non versionné |
| `src/cs_system/pipelines/sync/` | collecte et indexation | lecture distante autorisée |
| `src/cs_system/pipelines/local/` | rapprochements | aucun effet externe |
| `src/cs_system/pipelines/validate/` | invariants et diffs | aucune écriture distante |
| `src/cs_system/pipelines/inject/` | écritures Google/Notion/Drive | `--apply` obligatoire |

Créer les dossiers via `cs-system workspace-init`, puis régénérer les index avec
`cs-system sync-index` après l'ajout d'exports.

## Invariants métier

- Aucune source ne fait autorité seule ; une divergence est un résultat à
  arbitrer, jamais une correction automatique.
- Une coordonnée n'est pas une identité : les emails et téléphones peuvent être
  partagés, délégués ou attribués à un foyer.
- Préserver les rôles, les lots et les fiches composites ; ne pas fusionner des
  personnes à partir d'un simple email ou téléphone.
- Toute écriture externe doit être précédée d'un diff lisible, être idempotente
  et être protégée par `--apply`. Le comportement par défaut est `--dry-run`.
- Les exports et rapports doivent être déterministes, encodés en UTF-8, et les
  CSV lus/écrits en `utf-8-sig` lorsque cela correspond aux exports Google ou
  Notion existants.

## Travail collaboratif Codex / Claude

- Lire ce fichier, `README.md` et `docs/architecture.md` avant de modifier un
  pipeline.
- Préserver les modifications non liées déjà présentes ; ne jamais réinitialiser
  ni écraser des données utilisateur.
- Expliquer les hypothèses, les fichiers modifiés et les validations exécutées
  dans la restitution.
- Lorsqu'une règle métier est découverte ou modifiée, l'ajouter ici ou dans une
  documentation dédiée afin que Codex et Claude appliquent la même règle.
- Ne pas dupliquer une logique : placer les contrats de données et les fonctions
  communes dans `src/cs_system/`.

## Validation avant livraison

Après une modification Python :

```powershell
mamba run -n cs-system python -m compileall -q src
mamba run -n cs-system python -m pytest --cov -q --basetemp .test-tmp-<run>
mamba run -n cs-system cs-system --help
```

Tester toute nouvelle commande en mode non destructif. Pour les pipelines
d'écriture, contrôler le diff généré et ne jamais lancer `--apply` sans accord
explicite de l'utilisateur.
