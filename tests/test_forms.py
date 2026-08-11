import csv
from pathlib import Path

from cs_system.pipelines.forms import ingest


def test_ingest_keeps_actionable_answers_and_rejects_empty_ones(tmp_path: Path):
    source = tmp_path / "responses.csv"
    source.write_text(
        "Horodateur,Adresse e-mail,Demande,Priorite\n"
        "2026-08-11,a@example.test,Reparer le portail,Haute\n"
        "2026-08-11,b@example.test,,\n",
        encoding="utf-8-sig",
    )
    output = tmp_path / "actions.csv"

    assert ingest(source, output) == (1, 1)
    with output.open(encoding="utf-8-sig", newline="") as stream:
        assert list(csv.DictReader(stream)) == [{
            "id": "1", "statut": "a_traiter", "reponse": "Demande: Reparer le portail | Priorite: Haute"
        }]
