from pathlib import Path

import pytest

from cs_system.pipelines.documents import plan, run
from cs_system.settings import Settings


def _settings(root: Path, documents: Path) -> Settings:
    return Settings(root, documents, "", None, root / ".state/google.json", "", "", "", "", "", "")


def test_document_plan_deduplicates_checksum_and_ignores_new_report(tmp_path: Path):
    documents = tmp_path / "documents"
    documents.mkdir()
    (documents / "a.pdf").write_bytes(b"same")
    (documents / "b.pdf").write_bytes(b"same")
    report = documents / "_nouveaux"
    report.mkdir()
    (report / "nouveaux.md").write_text("rapport", encoding="utf-8")
    settings = _settings(tmp_path, documents)

    initial = plan(settings)
    assert [item.source.name for item in initial] == ["a.pdf", "b.pdf"]
    (tmp_path / ".state").mkdir()
    (tmp_path / ".state" / "documents.json").write_text('{"' + initial[0].checksum + '": "drive-url"}', encoding="utf-8")
    assert plan(settings) == []


def test_document_apply_requires_drive_configuration(tmp_path: Path):
    documents = tmp_path / "documents"
    documents.mkdir()
    (documents / "a.pdf").write_bytes(b"document")
    with pytest.raises(ValueError, match="GOOGLE_DRIVE"):
        run(_settings(tmp_path, documents), apply=True)
