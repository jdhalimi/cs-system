from __future__ import annotations

from pathlib import Path

from ..connectors.notion import database_title, export_table, list_databases, slugify
from ..settings import Settings


def notion_export_path(settings: Settings, slug: str) -> Path:
    return settings.root / "data" / "exports" / "notion" / slug / f"{slug}.csv"


def _discover(settings: Settings) -> dict[str, dict]:
    """Bases Notion partagees avec l'integration, indexees par slug (titre normalise)."""
    return {slugify(database_title(database)): database for database in list_databases(settings.notion_token)}


def export(settings: Settings, scope: tuple[str, ...] | None = None) -> dict[str, Path]:
    """Exporte toutes les bases Notion partagees avec l'integration, sans rien y ecrire.

    Aucune configuration prealable n'est necessaire : chaque base partagee avec
    l'integration (via le partage Notion, pas ce depot) est decouverte et
    exportee sous un slug derive de son titre (minuscule, espaces en '_',
    accents retires). `--scope` limite l'export a un sous-ensemble de slugs.
    """
    if not settings.notion_token:
        raise ValueError("Configurer NOTION_TOKEN dans .env avant notion export.")
    databases = _discover(settings)
    selected = scope or tuple(sorted(databases))
    unknown = [name for name in selected if name not in databases]
    if unknown:
        disponibles = ", ".join(sorted(databases)) or "aucune base partagee avec l'integration"
        raise ValueError(f"Portee(s) Notion inconnue(s) : {', '.join(unknown)} (disponibles : {disponibles})")
    return {
        name: export_table(settings.notion_token, databases[name]["id"], notion_export_path(settings, name))
        for name in selected
    }
