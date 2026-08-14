from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

_STALE_TOLERANCE_SECONDS = 60

from ..connectors.google import drive_service, list_drive_files, resolve_folder, upload_file
from ..ledger import load, save
from ..settings import Settings


@dataclass(frozen=True)
class DocumentPlan:
    source: Path
    checksum: str
    status: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def drive_index_path(settings: Settings) -> Path:
    return settings.root / "data" / "exports" / "google" / "drive" / "manifest.json"


def sync_drive_index(settings: Settings) -> dict[str, dict]:
    """Reindexe le contenu reel du dossier Drive inbox dans data/exports/google/drive."""
    if not settings.drive_folder_id or not settings.google_client_secrets:
        raise ValueError(
            "Configurer drive_inbox_folder_id dans config.toml [google] et GOOGLE_CLIENT_SECRETS "
            "dans .env avant google export --scope drive."
        )
    service = drive_service(settings.google_client_secrets, settings.google_token_file)
    files = list_drive_files(service, settings.drive_folder_id)
    index = {
        "/".join(file.folders + (file.name,)): {
            "id": file.id,
            "checksum": file.checksum,
            "modified_time": file.modified_time,
            "web_view_link": file.web_view_link,
        }
        for file in files
    }
    path = drive_index_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


def _drive_relative_parts(settings: Settings, source: Path) -> tuple[str, ...]:
    # Le premier segment est le nom de l'immeuble (dossier racine cote Citya) ; MyCYTIA sur
    # Drive part directement des categories (Ag cs, Factures...), donc on ne le reprend pas.
    return source.relative_to(settings.citya_documents_dir).parts[1:]


def _known_checksums(settings: Settings) -> set[str]:
    ledger = load(settings.root / ".state" / "documents.json")
    known = set(ledger)
    index_path = drive_index_path(settings)
    if index_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))
        known.update(entry["checksum"] for entry in index.values() if entry.get("checksum"))
    return known


def _known_drive_index(settings: Settings) -> dict[str, dict]:
    index_path = drive_index_path(settings)
    if not index_path.exists():
        return {}
    return json.loads(index_path.read_text(encoding="utf-8"))


def _is_stale(source: Path, drive_entry: dict) -> bool:
    """Vrai si le document local est plus recent que ce qui a ete depose sur Drive au meme chemin."""
    modified_time = drive_entry.get("modified_time")
    if not modified_time:
        return False
    drive_timestamp = datetime.fromisoformat(modified_time.replace("Z", "+00:00")).timestamp()
    return source.stat().st_mtime > drive_timestamp + _STALE_TOLERANCE_SECONDS


def plan(settings: Settings) -> list[DocumentPlan]:
    if not settings.citya_documents_dir.exists():
        raise FileNotFoundError(f"Repertoire Citya introuvable : {settings.citya_documents_dir}")
    known_checksums = _known_checksums(settings)
    known_paths = _known_drive_index(settings)
    plans = []
    for source in sorted(path for path in settings.citya_documents_dir.rglob("*") if path.is_file()):
        if "_nouveaux" in source.parts or source.name.startswith("."):
            continue
        checksum = _sha256(source)
        if checksum in known_checksums:
            continue
        drive_entry = known_paths.get("/".join(_drive_relative_parts(settings, source)))
        if drive_entry is not None and not _is_stale(source, drive_entry):
            continue
        status = "modifie" if drive_entry is not None else "nouveau"
        plans.append(DocumentPlan(source, checksum, status))
    return plans


def run(settings: Settings, apply: bool) -> list[DocumentPlan]:
    if settings.drive_folder_id and settings.google_client_secrets:
        sync_drive_index(settings)
    plans = plan(settings)
    if not apply or not plans:
        return plans
    if not settings.drive_folder_id or not settings.google_client_secrets:
        raise ValueError(
            "Configurer drive_inbox_folder_id dans config.toml [google] et GOOGLE_CLIENT_SECRETS "
            "dans .env avant --apply."
        )
    service = drive_service(settings.google_client_secrets, settings.google_token_file)
    ledger_path = settings.root / ".state" / "documents.json"
    ledger = load(ledger_path)
    folder_cache: dict[tuple[str, str], str] = {}
    for item in plans:
        folder_parts = _drive_relative_parts(settings, item.source)[:-1]
        folder_id = resolve_folder(service, settings.drive_folder_id, folder_parts, folder_cache)
        ledger[item.checksum] = upload_file(service, item.source, folder_id, item.checksum)
    save(ledger_path, ledger)
    sync_drive_index(settings)
    return plans

