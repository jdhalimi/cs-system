from __future__ import annotations

import csv
import re
from pathlib import Path


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _read(path: Path, source: str) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = csv.DictReader(stream)
        result = {}
        for row in rows:
            first = row.get("First Name") or row.get("Prenom") or ""
            last = row.get("Last Name") or row.get("Nom") or ""
            key = _norm(f"{first} {last}")
            if key:
                result[key] = {"source": source, "nom": f"{first} {last}".strip(), **row}
        return result


def compare(google_csv: Path, notion_csv: Path) -> list[dict[str, str]]:
    google, notion = _read(google_csv, "google"), _read(notion_csv, "notion")
    rows = []
    for key in sorted(set(google) | set(notion)):
        g, n = google.get(key), notion.get(key)
        status = "commun" if g and n else "google_seul" if g else "notion_seul"
        rows.append({"cle": key, "statut": status, "google": g["nom"] if g else "", "notion": n["nom"] if n else ""})
    return rows


def write(rows: list[dict[str, str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["cle", "statut", "google", "notion"])
        writer.writeheader()
        writer.writerows(rows)

