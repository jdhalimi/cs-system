from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

DRIVE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/drive"
PEOPLE_READ_SCOPE = "https://www.googleapis.com/auth/contacts.readonly"


def google_service(client_secrets: Path, token_file: Path, scopes: list[str], api: str, version: str):
    """Construit un client Google avec un jeton local au projet, accumule les scopes au fil des pipelines."""
    credentials = None
    granted_scopes: set[str] = set()
    if token_file.exists():
        granted_scopes = set(json.loads(token_file.read_text(encoding="utf-8")).get("scopes", []))
        credentials = Credentials.from_authorized_user_file(str(token_file), scopes)
    missing_scopes = not set(scopes) <= granted_scopes
    if not credentials or not credentials.valid or missing_scopes:
        if credentials and credentials.expired and credentials.refresh_token and not missing_scopes:
            credentials.refresh(Request())
        else:
            combined_scopes = sorted(set(scopes) | granted_scopes)
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), combined_scopes)
            credentials = flow.run_local_server(port=0)
        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(credentials.to_json(), encoding="utf-8")
    return build(api, version, credentials=credentials)


def drive_service(client_secrets: Path, token_file: Path):
    """Construit un client Drive ; une autorisation navigateur peut etre demandee."""
    return google_service(client_secrets, token_file, [DRIVE_UPLOAD_SCOPE], "drive", "v3")


def list_people(client_secrets: Path, token_file: Path) -> list[dict]:
    """Lit les fiches Google Contacts, sans aucune ecriture."""
    service = google_service(client_secrets, token_file, [PEOPLE_READ_SCOPE], "people", "v1")
    people, token = [], None
    while True:
        response = service.people().connections().list(
            resourceName="people/me",
            personFields="names,emailAddresses,phoneNumbers,memberships",
            pageSize=1000,
            pageToken=token,
        ).execute()
        people.extend(response.get("connections", []))
        token = response.get("nextPageToken")
        if not token:
            return people


def list_contact_group_names(client_secrets: Path, token_file: Path) -> dict[str, str]:
    """Fait correspondre les groupes de contacts (tags de classification) definis par l'utilisateur a leur nom."""
    service = google_service(client_secrets, token_file, [PEOPLE_READ_SCOPE], "people", "v1")
    groups = service.contactGroups().list(pageSize=1000).execute().get("contactGroups", [])
    return {
        group["resourceName"]: group["name"]
        for group in groups
        if group.get("groupType") == "USER_CONTACT_GROUP"
    }


def ensure_folder(service, parent_id: str, name: str, cache: dict[tuple[str, str], str]) -> str:
    key = (parent_id, name)
    if key in cache:
        return cache[key]
    escaped = name.replace("\\", "\\\\").replace("'", "\\'")
    query = (
        f"'{parent_id}' in parents and name = '{escaped}' "
        "and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    )
    files = service.files().list(q=query, fields="files(id)", pageSize=1).execute().get("files", [])
    if files:
        folder_id = files[0]["id"]
    else:
        metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]}
        folder_id = service.files().create(body=metadata, fields="id").execute()["id"]
    cache[key] = folder_id
    return folder_id


def resolve_folder(service, root_id: str, parts: tuple[str, ...], cache: dict[tuple[str, str], str]) -> str:
    folder_id = root_id
    for part in parts:
        folder_id = ensure_folder(service, folder_id, part, cache)
    return folder_id


FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"


@dataclass(frozen=True)
class DriveFile:
    folders: tuple[str, ...]
    name: str
    id: str
    checksum: str | None
    modified_time: str | None
    web_view_link: str | None


def list_drive_files(service, root_id: str, folders: tuple[str, ...] = ()) -> list[DriveFile]:
    """Parcourt recursivement un dossier Drive et liste ses fichiers, sans rien modifier."""
    entries = service.files().list(
        q=f"'{root_id}' in parents and trashed = false",
        fields="files(id,name,mimeType,appProperties,modifiedTime,webViewLink)",
        pageSize=1000,
    ).execute().get("files", [])
    result: list[DriveFile] = []
    for entry in entries:
        if entry["mimeType"] == FOLDER_MIME_TYPE:
            result.extend(list_drive_files(service, entry["id"], folders + (entry["name"],)))
        else:
            result.append(DriveFile(
                folders=folders,
                name=entry["name"],
                id=entry["id"],
                checksum=(entry.get("appProperties") or {}).get("cs_sha256"),
                modified_time=entry.get("modifiedTime"),
                web_view_link=entry.get("webViewLink"),
            ))
    return result


def upload_file(service, source: Path, folder_id: str, checksum: str) -> str:
    from googleapiclient.http import MediaFileUpload

    metadata = {"name": source.name, "parents": [folder_id], "appProperties": {"cs_sha256": checksum}}
    media = MediaFileUpload(str(source), resumable=True)
    result = service.files().create(body=metadata, media_body=media, fields="id,webViewLink").execute()
    return result.get("webViewLink") or f"https://drive.google.com/open?id={result['id']}"
