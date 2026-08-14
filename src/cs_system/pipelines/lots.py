from __future__ import annotations

import csv
from pathlib import Path

from ..connectors.notion import NOTION_ID_COLUMN, export_table
from ..settings import Settings


def notion_lots_export_path(settings: Settings) -> Path:
    return settings.root / "data" / "exports" / "notion" / "lots" / "lots.csv"


def export_notion_lots(settings: Settings) -> Path:
    """Exporte la base Notion des lots en CSV, sans rien y ecrire."""
    return export_table(settings.notion_token, settings.notion_lots_database_id, notion_lots_export_path(settings))


def read_lots(settings: Settings) -> dict[str, dict[str, str]]:
    """Relit l'export des lots, indexe par identifiant de page Notion."""
    path = notion_lots_export_path(settings)
    if not path.exists():
        raise FileNotFoundError(f"Export introuvable : {path}. Lancer d'abord notion-lots export.")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return {row[NOTION_ID_COLUMN]: row for row in csv.DictReader(stream)}
