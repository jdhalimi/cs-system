from __future__ import annotations

import csv
from pathlib import Path

from ..connectors.notion import NOTION_ID_COLUMN
from ..settings import Settings
from .notion import notion_export_path


def notion_lots_export_path(settings: Settings) -> Path:
    return notion_export_path(settings, "lots")


def read_lots(settings: Settings) -> dict[str, dict[str, str]]:
    """Relit l'export des lots, indexe par identifiant de page Notion."""
    path = notion_lots_export_path(settings)
    if not path.exists():
        raise FileNotFoundError(f"Export introuvable : {path}. Lancer d'abord notion export --scope lots.")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return {row[NOTION_ID_COLUMN]: row for row in csv.DictReader(stream)}
