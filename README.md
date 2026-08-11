# cs-system

Couche autonome d'orchestration du conseil syndical. Elle integre la capture
MyCitya et utilise les anciens depots uniquement comme references historiques.

## Principes

- Toute collecte est tracable dans `.state/` et idempotente.
- Les comparaisons ne modifient aucune source.
- Les ecritures dans Drive ou Notion demandent toujours `--apply` ; le mode par
  defaut est un apercu.
- Les secrets restent dans l'environnement ou dans `.env`, jamais dans Git.

## Installation

```bash
cd cs-system
mamba env create -f environment.yml
mamba run -n cs-system cs-system --help
Copy-Item .env.example .env
```

Renseigner les identifiants de dossier et les jetons dans `.env`. Le fichier OAuth
Google peut pointer vers celui deja utilise par `cs-contacts`, mais `cs-system`
conserve son propre jeton, avec uniquement les scopes necessaires.

Raccourcis disponibles avec GNU Make :

```bash
make env     # environnement Mamba, paquet local et Chromium
make tests   # tests unitaires et couverture
make docs    # régénère docs/commands.md depuis la CLI
```

## Pipelines

```bash
# Créer l'espace de travail local (à faire une fois)
cs-system workspace-init

# Recalculer les index à partir des exports bruts déjà présents
cs-system sync-index

# Capturer MyCitya dans data/exports/citya/documents (authentification navigateur au besoin)
cs-system citya-sync --new

# Inventorier les documents Citya absents du registre Drive
cs-system capture-documents

# Envoyer ces documents vers le dossier Drive configure
cs-system capture-documents --apply

# Comparer deux exports CSV Google Contacts et Notion
cs-system compare-contacts google.csv notion.csv --out data/contact-diff.csv

# Normaliser les reponses CSV d'un Google Form vers un registre d'actions
cs-system ingest-form responses.csv --out data/form-actions.csv
```

## Cycle de production

Le code est rangé dans `src/cs_system/pipelines/` :

```text
sync → exports/cache/indexes → local → validate → inject
```

Les données suivent la même séparation dans `data/`. Les snapshots dans
`data/exports/` ne sont jamais modifiés ; `data/cache/` et `data/indexes/` sont
reconstruisibles. Seul le pipeline `inject/` pourra écrire dans Drive, Google
Contacts ou Notion, et devra exiger `--apply`.

Installer Chromium une seule fois après la création de l'environnement :

```bash
mamba run -n cs-system playwright install chromium
```

La documentation utilisateur et technique est publiée localement avec MkDocs :

```bash
make docs
mamba run -n cs-system mkdocs serve
```

Voir notamment le [guide de démarrage](docs/user/getting-started.md) et
l'[architecture technique](docs/technical/architecture.md).
