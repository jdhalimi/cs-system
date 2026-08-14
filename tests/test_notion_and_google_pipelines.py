from pathlib import Path

import pytest

from cs_system.connectors.notion import database_title, slugify
from cs_system.pipelines import google, notion
from cs_system.settings import Settings


def _settings(root: Path, **overrides) -> Settings:
    base = dict(
        root=root, citya_documents_dir=root / "documents", drive_folder_id="", google_client_secrets=None,
        google_token_file=root / ".state/google.json", notion_token="", citya_email="", citya_password="",
        citya_documents_url="", citya_immeuble_id="",
    )
    base.update(overrides)
    return Settings(**base)


def _configured_settings(root: Path) -> Settings:
    return _settings(root, drive_folder_id="folder-id", google_client_secrets=root / "creds.json", notion_token="secret-token")


def test_slugify_lowercases_replaces_spaces_and_strips_accents():
    assert slugify("Propriétaires") == "proprietaires"
    assert slugify("Factures 2025") == "factures_2025"
    assert slugify("État des dépenses") == "etat_des_depenses"


def test_database_title_concatenates_rich_text_segments():
    database = {"title": [{"plain_text": "Fact"}, {"plain_text": "ures 2025"}]}
    assert database_title(database) == "Factures 2025"


def test_notion_export_discovers_and_exports_every_shared_database(tmp_path: Path, monkeypatch):
    settings = _configured_settings(tmp_path)
    fake_databases = [
        {"id": "db-proprietaires", "title": [{"plain_text": "Propriétaires"}]},
        {"id": "db-factures-2025", "title": [{"plain_text": "Factures 2025"}]},
    ]
    monkeypatch.setattr(notion, "list_databases", lambda token: fake_databases)
    calls = []
    monkeypatch.setattr(
        notion, "export_table",
        lambda token, database_id, output: calls.append((database_id, output)) or output,
    )
    results = notion.export(settings)
    assert set(results) == {"proprietaires", "factures_2025"}
    assert results["proprietaires"] == notion.notion_export_path(settings, "proprietaires")
    assert ("db-proprietaires", notion.notion_export_path(settings, "proprietaires")) in calls
    assert ("db-factures-2025", notion.notion_export_path(settings, "factures_2025")) in calls


def test_notion_export_honors_requested_scope(tmp_path: Path, monkeypatch):
    settings = _configured_settings(tmp_path)
    fake_databases = [
        {"id": "db-lots", "title": [{"plain_text": "Lots"}]},
        {"id": "db-banque", "title": [{"plain_text": "Banque"}]},
    ]
    monkeypatch.setattr(notion, "list_databases", lambda token: fake_databases)
    called = []
    monkeypatch.setattr(
        notion, "export_table",
        lambda token, database_id, output: called.append(database_id) or output,
    )
    results = notion.export(settings, ("lots",))
    assert list(results) == ["lots"]
    assert called == ["db-lots"]


def test_notion_export_rejects_unknown_scope(tmp_path: Path, monkeypatch):
    settings = _configured_settings(tmp_path)
    monkeypatch.setattr(notion, "list_databases", lambda token: [{"id": "db-lots", "title": [{"plain_text": "Lots"}]}])
    with pytest.raises(ValueError, match="inconnue"):
        notion.export(settings, ("charges",))


def test_notion_export_requires_token(tmp_path: Path):
    with pytest.raises(ValueError, match="NOTION_TOKEN"):
        notion.export(_settings(tmp_path))


def test_google_export_defaults_to_every_configured_scope(tmp_path: Path, monkeypatch):
    settings = _configured_settings(tmp_path)
    monkeypatch.setitem(google.SCOPES, "contacts", lambda settings: Path("contacts.csv"))
    monkeypatch.setitem(google.SCOPES, "drive", lambda settings: {"a": {}})
    results = google.export(settings)
    assert results == {"contacts": Path("contacts.csv"), "drive": {"a": {}}}


def test_google_export_honors_requested_scope(tmp_path: Path, monkeypatch):
    settings = _configured_settings(tmp_path)
    called = []
    monkeypatch.setitem(google.SCOPES, "contacts", lambda settings: called.append("contacts") or Path("contacts.csv"))
    monkeypatch.setitem(google.SCOPES, "drive", lambda settings: called.append("drive") or {})
    results = google.export(settings, ("contacts",))
    assert list(results) == ["contacts"]
    assert called == ["contacts"]


def test_google_export_rejects_unknown_scope(tmp_path: Path):
    with pytest.raises(ValueError, match="inconnue"):
        google.export(_configured_settings(tmp_path), ("calendar",))


def test_google_export_skips_unconfigured_scope_by_default(tmp_path: Path, monkeypatch):
    settings = _settings(tmp_path, google_client_secrets=tmp_path / "creds.json")
    monkeypatch.setitem(google.SCOPES, "contacts", lambda settings: Path("contacts.csv"))
    monkeypatch.setitem(google.SCOPES, "drive", lambda settings: (_ for _ in ()).throw(AssertionError("ne doit pas etre appele")))
    results = google.export(settings)
    assert results == {"contacts": Path("contacts.csv")}


def test_google_export_raises_when_explicit_scope_is_unconfigured(tmp_path: Path):
    with pytest.raises(ValueError, match="drive_inbox_folder_id"):
        google.export(_settings(tmp_path), ("drive",))
