import hashlib
import json
from pathlib import Path

import pytest

from cs_system.pipelines.sync.indexes import build
from cs_system.workspace import Workspace


def test_workspace_creates_the_documented_source_entity_directories(tmp_path: Path):
    workspace = Workspace(tmp_path)
    workspace.ensure()
    assert (workspace.exports / "notion" / "proprietaires").is_dir()
    assert (workspace.exports / "notion" / "locataires").is_dir()
    assert (workspace.exports / "notion" / "lots").is_dir()
    assert (workspace.exports / "notion" / "factures").is_dir()
    assert (workspace.cache / "google" / "drive").is_dir()
    assert workspace.reports.is_dir()
    assert workspace.state.is_dir()


def test_index_contains_relative_path_and_sha256(tmp_path: Path):
    workspace = Workspace(tmp_path)
    source = workspace.exports / "notion" / "contacts" / "20260811.csv"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"Nom,Prenom\nDurand,Jean\n")

    assert build(workspace, "notion") == {"notion": 1}
    index = json.loads((workspace.indexes / "notion" / "exports.json").read_text(encoding="utf-8"))
    assert index["source"] == "notion"
    assert index["entries"] == [{
        "path": "data/exports/notion/contacts/20260811.csv",
        "entity": "contacts",
        "size": len(b"Nom,Prenom\nDurand,Jean\n"),
        "sha256": hashlib.sha256(b"Nom,Prenom\nDurand,Jean\n").hexdigest(),
        "modified_at": index["entries"][0]["modified_at"],
    }]


def test_index_rejects_an_unknown_source(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="inconnue"):
        build(Workspace(tmp_path), "inconnue")
