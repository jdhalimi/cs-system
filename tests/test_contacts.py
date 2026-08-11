from pathlib import Path

from cs_system.pipelines.contacts import compare


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

