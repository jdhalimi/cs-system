from __future__ import annotations

from typing import Callable

from ..settings import Settings
from .contacts import export_google_contacts
from .documents import sync_drive_index

SCOPES: dict[str, Callable[[Settings], object]] = {
    "contacts": export_google_contacts,
    "drive": sync_drive_index,
}

# Configuration a renseigner pour que la portee correspondante soit exportable
# (GOOGLE_CLIENT_SECRETS dans .env ; drive_inbox_folder_id dans config.toml [google]).
REQUIRED_CONFIG: dict[str, str] = {
    "contacts": "GOOGLE_CLIENT_SECRETS (.env)",
    "drive": "GOOGLE_CLIENT_SECRETS (.env) et drive_inbox_folder_id (config.toml [google])",
}

_CONFIGURED: dict[str, Callable[[Settings], bool]] = {
    "contacts": lambda settings: settings.google_client_secrets is not None,
    "drive": lambda settings: settings.google_client_secrets is not None and bool(settings.drive_folder_id),
}


def export(settings: Settings, scope: tuple[str, ...] | None = None) -> dict[str, object]:
    """Synchronise les sources Google demandees, sans rien y ecrire.

    Sans --scope explicite (toutes les portees), celles dont la configuration
    requise est absente sont ignorees plutot que de faire echouer l'export
    entier ; demandee explicitement, une portee non configuree leve une
    erreur claire.
    """
    explicit = scope is not None
    selected = scope or tuple(SCOPES)
    unknown = [name for name in selected if name not in SCOPES]
    if unknown:
        raise ValueError(f"Portee(s) Google inconnue(s) : {', '.join(unknown)} (valides : {', '.join(SCOPES)})")
    results: dict[str, object] = {}
    for name in selected:
        if not _CONFIGURED[name](settings):
            if explicit:
                raise ValueError(f"Portee '{name}' demandee mais {REQUIRED_CONFIG[name]} n'est pas configure.")
            continue
        results[name] = SCOPES[name](settings)
    return results
