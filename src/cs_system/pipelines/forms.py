from __future__ import annotations

import csv
from pathlib import Path

SYSTEM_COLUMNS = {"timestamp", "horodateur", "adresse e-mail", "email address"}


def ingest(source: Path, output: Path) -> tuple[int, int]:
    with source.open(encoding="utf-8-sig", newline="") as stream:
        source_rows = list(csv.DictReader(stream))
    result = []
    rejected = 0
    for index, row in enumerate(source_rows, 1):
        useful = {key: value.strip() for key, value in row.items() if value and key.casefold() not in SYSTEM_COLUMNS}
        if not useful:
            rejected += 1
            continue
        result.append({"id": str(index), "statut": "a_traiter", "reponse": " | ".join(f"{k}: {v}" for k, v in useful.items())})
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "statut", "reponse"])
        writer.writeheader()
        writer.writerows(result)
    return len(result), rejected

