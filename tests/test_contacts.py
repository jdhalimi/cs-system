from pathlib import Path

import pytest

from cs_system.pipelines.contacts import (
    compare,
    google_contacts_export_path,
    match,
    notion_locataires_export_path,
    notion_proprietaires_export_path,
)
from cs_system.pipelines.lots import notion_lots_export_path
from cs_system.settings import Settings


def test_compare_handles_google_and_notion_headers(tmp_path: Path):
    google = tmp_path / "google.csv"
    notion = tmp_path / "notion.csv"
    google.write_text("First Name,Last Name\nJean,Durand\n", encoding="utf-8")
    notion.write_text("Prenom,Nom\nJean,Durand\nClaire,Martin\n", encoding="utf-8")
    rows = compare(google, notion)
    assert [(row["cle"], row["statut"]) for row in rows] == [
        ("clairemartin", "notion_seul"),
        ("jeandurand", "commun"),
    ]


def _settings(root: Path) -> Settings:
    return Settings(
        root=root, citya_documents_dir=root / "documents", drive_folder_id="", google_client_secrets=None,
        google_token_file=root / ".state/google.json", notion_token="", notion_proprietaires_database_id="",
        notion_locataires_database_id="", notion_lots_database_id="", citya_email="", citya_password="",
        citya_documents_url="", citya_immeuble_id="",
    )


def _write_exports(settings: Settings, google: str, proprietaires: str, locataires: str, lots: str = "_notion_id,Type,Escalier\n") -> None:
    for path, content in (
        (google_contacts_export_path(settings), google),
        (notion_proprietaires_export_path(settings), proprietaires),
        (notion_locataires_export_path(settings), locataires),
        (notion_lots_export_path(settings), lots),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def test_match_requires_exports_to_exist_first(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="Lancer d'abord"):
        match(_settings(tmp_path))


def test_match_finds_common_email_and_orphan_entries(tmp_path: Path):
    settings = _settings(tmp_path)
    _write_exports(
        settings,
        google=(
            "First Name,Last Name,E-mail 1 - Value\n"
            "Jean,Durand,jean.durand@mail.fr\n"
            "Alix,Petit,alix.variante@mail.fr\n"
            "Sam,Inconnu,\n"
        ),
        proprietaires=(
            "Prenom,Nom,Email 1\n"
            "Jean,Durand,jean.durand@mail.fr\n"
            "Alixe,Petitte,alix.variante@mail.fr\n"
        ),
        locataires="Prenom,Nom,Email 1\nClaire,Martin,claire.martin@mail.fr\n",
    )
    rows = {row["cle"]: row for row in match(settings)}
    assert rows["jeandurand"]["statut"] == "commun"
    assert rows["alixpetit"]["statut"] == "rapproche_email"
    assert rows["saminconnu"]["statut"] == "google_seul"
    assert rows["clairemartin"]["statut"] == "notion_seul"
    assert rows["clairemartin"]["notion"] == "Claire Martin (locataire)"


def test_match_interactive_confirms_a_manual_pairing(tmp_path: Path):
    settings = _settings(tmp_path)
    _write_exports(
        settings,
        google="First Name,Last Name\nJean David,Halimi\n",
        proprietaires="Prenom,Nom\nJeanne David,Halimi\n",
        locataires="Prenom,Nom\n",
    )
    answers = iter(["1"])
    rows = {row["cle"]: row for row in match(settings, interactive=True, prompt=lambda _: next(answers))}
    assert rows["jeandavidhalimi"]["statut"] == "rapproche_manuel"
    assert "proprietaire" in rows["jeandavidhalimi"]["notion"]


def test_match_interactive_skips_when_declined(tmp_path: Path):
    settings = _settings(tmp_path)
    _write_exports(
        settings,
        google="First Name,Last Name\nJean David,Halimi\n",
        proprietaires="Prenom,Nom\nJeanne David,Halimi\n",
        locataires="Prenom,Nom\n",
    )
    answers = iter([""])
    rows = {row["cle"]: row for row in match(settings, interactive=True, prompt=lambda _: next(answers))}
    assert rows["jeandavidhalimi"]["statut"] == "google_seul"
    assert rows["jeannedavidhalimi"]["statut"] == "notion_seul"


def test_match_ignores_fournisseurs(tmp_path: Path):
    settings = _settings(tmp_path)
    _write_exports(
        settings,
        google="First Name,Last Name,Labels\nAcme,Plombier,Fournisseurs\n",
        proprietaires="Prenom,Nom\n",
        locataires="Prenom,Nom\n",
    )
    assert match(settings) == []


def test_match_reports_escalier_role_and_phone_anomalies(tmp_path: Path):
    settings = _settings(tmp_path)
    _write_exports(
        settings,
        google="First Name,Last Name,Labels\nJean,Dupont,Propriétaire A1\n",
        proprietaires="Prenom,Nom,Lots,Telephone 1\nJean,Dupont,lot-1,\n",
        locataires="Prenom,Nom\n",
        lots="_notion_id,Type,Escalier\nlot-1,appart,B2\n",
    )
    rows = {row["cle"]: row for row in match(settings)}
    anomalies = rows["jeandupont"]["anomalies"]
    assert "escalier Google 'A1' absent des lots Notion (B2)" in anomalies
    assert "telephone absent" in anomalies


def test_match_reports_no_anomaly_when_consistent(tmp_path: Path):
    settings = _settings(tmp_path)
    _write_exports(
        settings,
        google="First Name,Last Name,Labels,Phone 1 - Value\nJean,Dupont,Propriétaire A1,0600000000\n",
        proprietaires="Prenom,Nom,Lots,Telephone 1\nJean,Dupont,lot-1,0600000000\n",
        locataires="Prenom,Nom\n",
        lots="_notion_id,Type,Escalier\nlot-1,appart,A1\n",
    )
    rows = {row["cle"]: row for row in match(settings)}
    assert rows["jeandupont"]["anomalies"] == ""


def test_match_fills_phone_missing_on_one_side(tmp_path: Path):
    settings = _settings(tmp_path)
    _write_exports(
        settings,
        google="First Name,Last Name,Labels,Phone 1 - Value\nJean,Dupont,Propriétaire A1,0600000000\n",
        proprietaires="Prenom,Nom,Lots,Telephone 1\nJean,Dupont,lot-1,\n",
        locataires="Prenom,Nom\n",
        lots="_notion_id,Type,Escalier\nlot-1,appart,A1\n",
    )
    rows = {row["cle"]: row for row in match(settings)}
    assert rows["jeandupont"]["telephone"] == "0600000000"
    assert rows["jeandupont"]["anomalies"] == ""

