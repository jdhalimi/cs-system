from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # La CLI reste lisible avant l'installation des dependances.
    def load_dotenv(path: Path) -> None:
        if not path.exists():
            return
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


@dataclass(frozen=True)
class Settings:
    root: Path
    citya_documents_dir: Path
    drive_folder_id: str
    google_client_secrets: Path | None
    google_token_file: Path
    notion_token: str
    notion_proprietaires_database_id: str
    notion_locataires_database_id: str
    notion_lots_database_id: str
    citya_email: str
    citya_password: str
    citya_documents_url: str
    citya_immeuble_id: str


def _path(root: Path, value: str, default: str) -> Path:
    path = Path(value or default)
    return path if path.is_absolute() else (root / path).resolve()


def load_settings(root: Path | None = None) -> Settings:
    root = (root or Path.cwd()).resolve()
    load_dotenv(root / ".env")
    return Settings(
        root=root,
        citya_documents_dir=_path(root, os.getenv("CITYA_DOCUMENTS_DIR", ""), "data/exports/citya/documents"),
        drive_folder_id=os.getenv("GOOGLE_DRIVE_INBOX_FOLDER_ID", "").strip(),
        google_client_secrets=(
            _path(root, os.environ["GOOGLE_CLIENT_SECRETS"], "")
            if os.getenv("GOOGLE_CLIENT_SECRETS") else None
        ),
        google_token_file=_path(root, os.getenv("GOOGLE_TOKEN_FILE", ""), ".state/google-token.json"),
        notion_token=os.getenv("NOTION_TOKEN", "").strip(),
        notion_proprietaires_database_id=os.getenv("NOTION_PROPRIETAIRES_DATABASE_ID", "").strip(),
        notion_locataires_database_id=os.getenv("NOTION_LOCATAIRES_DATABASE_ID", "").strip(),
        notion_lots_database_id=os.getenv("NOTION_LOTS_DATABASE_ID", "").strip(),
        citya_email=os.getenv("CITYA_EMAIL", "").strip(),
        citya_password=os.getenv("CITYA_PASSWORD", "").strip(),
        citya_documents_url=os.getenv("CITYA_DOCUMENTS_URL", "").strip(),
        citya_immeuble_id=os.getenv("CITYA_IMMEUBLE_ID", "").strip(),
    )
