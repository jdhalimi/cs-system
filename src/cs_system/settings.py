from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
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


def _load_config(root: Path) -> dict:
    """Lit config.toml (regles metier non secretes, versionnees). Absent : configuration vide."""
    path = root / "config.toml"
    if not path.exists():
        return {}
    with path.open("rb") as stream:
        return tomllib.load(stream)


@dataclass(frozen=True)
class Settings:
    root: Path
    citya_documents_dir: Path
    drive_folder_id: str
    google_client_secrets: Path | None
    google_token_file: Path
    notion_token: str
    citya_email: str
    citya_password: str
    citya_documents_url: str
    citya_immeuble_id: str
    ignored_google_labels: tuple[str, ...] = field(default_factory=tuple)


def _path(root: Path, value: str, default: str) -> Path:
    path = Path(value or default)
    return path if path.is_absolute() else (root / path).resolve()


def load_settings(root: Path | None = None) -> Settings:
    root = (root or Path.cwd()).resolve()
    load_dotenv(root / ".env")
    config = _load_config(root)
    matching_config = config.get("matching", {})
    google_config = config.get("google", {})
    citya_config = config.get("citya", {})
    return Settings(
        root=root,
        citya_documents_dir=_path(root, os.getenv("CITYA_DOCUMENTS_DIR", ""), "data/exports/citya/documents"),
        drive_folder_id=str(google_config.get("drive_inbox_folder_id", "")).strip(),
        google_client_secrets=(
            _path(root, os.environ["GOOGLE_CLIENT_SECRETS"], "")
            if os.getenv("GOOGLE_CLIENT_SECRETS") else None
        ),
        google_token_file=_path(root, os.getenv("GOOGLE_TOKEN_FILE", ""), ".state/google-token.json"),
        notion_token=os.getenv("NOTION_TOKEN", "").strip(),
        citya_email=os.getenv("CITYA_EMAIL", "").strip(),
        citya_password=os.getenv("CITYA_PASSWORD", "").strip(),
        citya_documents_url=str(citya_config.get("documents_url", "")).strip(),
        citya_immeuble_id=str(citya_config.get("immeuble_id", "")).strip(),
        ignored_google_labels=tuple(matching_config.get("ignored_google_labels", [])),
    )
