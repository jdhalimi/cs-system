import json
from pathlib import Path

from cs_system.ledger import load, save
from cs_system.settings import load_settings


def test_settings_loads_relative_paths_from_dotenv(tmp_path: Path, monkeypatch):
    for key in ("GOOGLE_CLIENT_SECRETS", "GOOGLE_TOKEN_FILE", "CITYA_DOCUMENTS_DIR", "NOTION_TOKEN"):
        monkeypatch.delenv(key, raising=False)
    (tmp_path / ".env").write_text(
        "GOOGLE_CLIENT_SECRETS=creds/client.json\n"
        "GOOGLE_TOKEN_FILE=tokens/google.json\n"
        "CITYA_DOCUMENTS_DIR=exports/citya\n"
        "NOTION_TOKEN=token-test\n",
        encoding="utf-8",
    )
    settings = load_settings(tmp_path)
    assert settings.google_client_secrets == tmp_path / "creds" / "client.json"
    assert settings.google_token_file == tmp_path / "tokens" / "google.json"
    assert settings.citya_documents_dir == tmp_path / "exports" / "citya"
    assert settings.notion_token == "token-test"


def test_ledger_loads_missing_file_and_round_trips_json(tmp_path: Path):
    path = tmp_path / ".state" / "ledger.json"
    assert load(path) == {}
    save(path, {"hash-b": "url-b", "hash-a": "url-a"})
    assert load(path) == {"hash-a": "url-a", "hash-b": "url-b"}
    assert list(json.loads(path.read_text(encoding="utf-8"))) == ["hash-a", "hash-b"]
