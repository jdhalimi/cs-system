# Architecture

Le flux de production est volontairement linéaire :

```text
sync → exports/cache/indexes → local → validate → inject
```

Chaque étape a une responsabilité unique. Une étape en aval ne modifie pas les
données d'une étape en amont.

| Étape | Responsabilité | Écriture distante |
| --- | --- | --- |
| `sync` | collecte d'API et documents | lecture seulement |
| `exports/cache/indexes` | snapshots et catalogues | locale seulement |
| `local` | rapprochement et enrichissement | aucune |
| `validate` | invariants et diff | aucune |
| `inject` | mise à jour des systèmes | uniquement avec `--apply` |

Les connecteurs sont dans `src/cs_system/connectors/`, les pipelines dans
`src/cs_system/pipelines/` et la convention des chemins dans `workspace.py`.
