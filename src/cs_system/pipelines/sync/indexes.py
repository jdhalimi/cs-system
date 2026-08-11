"""Indexe les snapshots exportés sans modifier leur contenu."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from ...workspace import Workspace


def _digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def build(workspace: Workspace, source: str | None = None) -> dict[str, int]:
    """Produit un index JSON par source/entité depuis les exports bruts."""
    workspace.ensure()
    sources = [source] if source else sorted(path.name for path in workspace.exports.iterdir() if path.is_dir())
    counts: dict[str, int] = {}
    for name in sources:
        source_dir = workspace.exports / name
        if not source_dir.exists():
            raise FileNotFoundError(f"Source d'exports inconnue : {name}")
        entries = []
        for path in sorted(item for item in source_dir.rglob("*") if item.is_file()):
            entries.append({
                "path": path.relative_to(workspace.root).as_posix(),
                "entity": path.parent.name,
                "size": path.stat().st_size,
                "sha256": _digest(path),
                "modified_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
            })
        output = workspace.indexes / name / "exports.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({"source": name, "generated_at": datetime.now(timezone.utc).isoformat(), "entries": entries}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        counts[name] = len(entries)
    return counts
