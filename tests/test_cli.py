from pathlib import Path

from cs_system import cli


def test_workspace_init_command_creates_data_tree(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["cs-system", "workspace-init"])
    assert cli.main() == 0
    assert (tmp_path / "data" / "exports" / "notion" / "proprietaires").is_dir()
    assert "Espace de travail prêt" in capsys.readouterr().out


def test_sync_index_command_uses_requested_source(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "build_indexes", lambda workspace, source: {source: 3})
    monkeypatch.setattr("sys.argv", ["cs-system", "sync-index", "--source", "google"])
    assert cli.main() == 0
    assert "google=3" in capsys.readouterr().out


def test_citya_command_dispatches_with_options(tmp_path: Path, monkeypatch, capsys):
    marker = object()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "load_settings", lambda: marker)
    monkeypatch.setattr(cli, "citya_sync", lambda settings, new_only, headed: (12, 2))
    monkeypatch.setattr("sys.argv", ["cs-system", "citya", "export", "--new", "--headed"])
    assert cli.main() == 0
    assert "2 document(s) telecharge(s) sur 12" in capsys.readouterr().out


def test_capture_command_dispatches_apply(tmp_path: Path, monkeypatch, capsys):
    marker = object()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "load_settings", lambda: marker)
    monkeypatch.setattr(cli.documents, "run", lambda settings, apply: [])
    monkeypatch.setattr("sys.argv", ["cs-system", "citya", "capture", "--apply"])
    assert cli.main() == 0
    assert "0 document(s) envoyes" in capsys.readouterr().out


def test_notion_export_command_dispatches_requested_scope(tmp_path: Path, monkeypatch, capsys):
    marker = object()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "load_settings", lambda: marker)
    monkeypatch.setattr(cli.notion, "export", lambda settings, scope: {"lots": Path("lots.csv")} if scope == ("lots",) else {})
    monkeypatch.setattr("sys.argv", ["cs-system", "notion", "export", "--scope", "lots"])
    assert cli.main() == 0
    assert "lots Notion exportee -> lots.csv" in capsys.readouterr().out


def test_google_export_command_reports_drive_count(tmp_path: Path, monkeypatch, capsys):
    marker = object()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "load_settings", lambda: marker)
    monkeypatch.setattr(cli.google, "export", lambda settings, scope: {"drive": {"a": {}, "b": {}}} if scope is None else {})
    monkeypatch.setattr("sys.argv", ["cs-system", "google", "export"])
    assert cli.main() == 0
    assert "2 document(s) indexe(s) depuis Drive" in capsys.readouterr().out


def test_contacts_and_forms_commands_dispatch(tmp_path: Path, monkeypatch, capsys):
    google, notion, output = tmp_path / "g.csv", tmp_path / "n.csv", tmp_path / "out.csv"
    monkeypatch.setattr(cli.contacts, "compare", lambda left, right: [{"cle": "x"}])
    monkeypatch.setattr(cli.contacts, "write", lambda rows, path: None)
    monkeypatch.setattr("sys.argv", ["cs-system", "compare-contacts", str(google), str(notion), "--out", str(output)])
    assert cli.main() == 0
    assert "1 identite(s) comparee(s)" in capsys.readouterr().out
    monkeypatch.setattr(cli.forms, "ingest", lambda source, path: (4, 1))
    monkeypatch.setattr("sys.argv", ["cs-system", "ingest-form", str(google), "--out", str(output)])
    assert cli.main() == 0
    assert "4 reponse(s) a traiter, 1 ignoree(s)" in capsys.readouterr().out
