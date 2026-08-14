from __future__ import annotations

import csv
import json
import urllib.request
from pathlib import Path

NOTION_VERSION = "2022-06-28"


def query_database(token: str, database_id: str) -> list[dict]:
    """Lit toutes les pages d'une base Notion partagee avec l'integration."""
    pages: list[dict] = []
    cursor = None
    while True:
        payload = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor
        request = urllib.request.Request(
            f"https://api.notion.com/v1/databases/{database_id}/query",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.load(response)
        pages.extend(data.get("results", []))
        cursor = data.get("next_cursor")
        if not data.get("has_more"):
            return pages


def flatten_property(prop: dict) -> str:
    """Reduit une propriete Notion typee a une valeur texte plate."""
    kind = prop.get("type")
    if kind in ("title", "rich_text"):
        return "".join(part.get("plain_text", "") for part in prop.get(kind, []))
    if kind in ("email", "phone_number", "url"):
        return prop.get(kind) or ""
    if kind == "number":
        value = prop.get("number")
        return "" if value is None else str(value)
    if kind == "checkbox":
        return "Oui" if prop.get("checkbox") else "Non"
    if kind == "select":
        value = prop.get("select")
        return value["name"] if value else ""
    if kind == "multi_select":
        return ", ".join(item["name"] for item in prop.get("multi_select", []))
    if kind == "date":
        value = prop.get("date")
        return value["start"] if value else ""
    if kind == "relation":
        return ", ".join(item["id"] for item in prop.get("relation", []))
    return ""


NOTION_ID_COLUMN = "_notion_id"


def export_table(token: str, database_id: str, output: Path) -> Path:
    """Exporte une base Notion en CSV (une colonne par propriete), sans rien y ecrire."""
    pages = query_database(token, database_id)
    fieldnames: list[str] = [NOTION_ID_COLUMN]
    rows = []
    for page in pages:
        row = {NOTION_ID_COLUMN: page["id"]}
        for name, prop in page["properties"].items():
            if name not in fieldnames:
                fieldnames.append(name)
            row[name] = flatten_property(prop)
        rows.append(row)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return output
