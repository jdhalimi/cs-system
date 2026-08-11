# Contribution

Lire `AGENTS.md` avant toute modification.

## Vérifications

```powershell
make tests
mamba run -n cs-system mkdocs build --strict
```

Les tests unitaires couvrent les traitements déterministes. Les connecteurs
distants doivent être testés avec des doubles/mocks ou dans un environnement de
test contrôlé, jamais avec des secrets de production.

## Règles de code

- privilégier des fonctions déterministes et idempotentes ;
- ne jamais modifier un export brut ;
- garder toute écriture externe dans `pipelines/inject/` ;
- documenter les nouvelles commandes dans le guide utilisateur.
