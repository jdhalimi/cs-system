from __future__ import annotations

import json
import urllib.request

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
