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

Renseigner les jetons et identifiants de connexion (secrets) dans `.env`, et
les identifiants non secrets (dossier Drive, immeuble et URL Citya) dans
`config.toml`. Les bases Notion n'ont besoin d'aucune configuration : partager
une base avec l'integration dans Notion suffit a ce qu'elle soit exportee.
Le fichier OAuth Google peut pointer vers celui deja utilise par
`cs-contacts`, mais `cs-system` conserve son propre jeton, avec uniquement
les scopes necessaires.

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
cs-system citya export --new

# Inventorier les documents Citya absents ou perimes par rapport a Drive
cs-system citya capture

# Envoyer ces documents vers le dossier Drive configure
cs-system citya capture --apply

# Reindexer le contenu reel du dossier Drive sans rien envoyer
cs-system google export --scope drive

# Exporter les Google Contacts (dont les tags de classification) en CSV
cs-system google export --scope contacts

# Decouvrir et exporter toutes les bases Notion partagees avec l'integration en CSV
cs-system notion export

# Exporter uniquement un sous-ensemble (slugs derives du titre Notion)
cs-system notion export --scope lots,proprietaires

# Rapprocher les contacts Google et Notion (--interactive pour confirmer les cas ambigus)
cs-system match contacts

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
