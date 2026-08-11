from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from ..connectors.google import drive_service, upload_file
from ..ledger import load, save
from ..settings import Settings


@dataclass(frozen=True)
class DocumentPlan:
    source: Path
    checksum: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def plan(settings: Settings) -> list[DocumentPlan]:
    if not settings.citya_documents_dir.exists():
        raise FileNotFoundError(f"Repertoire Citya introuvable : {settings.citya_documents_dir}")
    ledger = load(settings.root / ".state" / "documents.json")
    plans = []
    for source in sorted(path for path in settings.citya_documents_dir.rglob("*") if path.is_file()):
        if "_nouveaux" in source.parts:
            continue
        checksum = _sha256(source)
        if checksum not in ledger:
            plans.append(DocumentPlan(source, checksum))
    return plans


def run(settings: Settings, apply: bool) -> list[DocumentPlan]:
    plans = plan(settings)
    if not apply or not plans:
        return plans
    if not settings.drive_folder_id or not settings.google_client_secrets:
        raise ValueError("Configurer GOOGLE_DRIVE_INBOX_FOLDER_ID et GOOGLE_CLIENT_SECRETS avant --apply.")
    service = drive_service(settings.google_client_secrets, settings.google_token_file)
    ledger_path = settings.root / ".state" / "documents.json"
    ledger = load(ledger_path)
    for item in plans:
        ledger[item.checksum] = upload_file(service, item.source, settings.drive_folder_id, item.checksum)
    save(ledger_path, ledger)
    return plans

