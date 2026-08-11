from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

DRIVE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/drive.file"
PEOPLE_READ_SCOPE = "https://www.googleapis.com/auth/contacts.readonly"


def google_service(client_secrets: Path, token_file: Path, scopes: list[str], api: str, version: str):
    """Construit un client Google avec un jeton local au projet."""
    credentials = None
    if token_file.exists():
        credentials = Credentials.from_authorized_user_file(str(token_file), scopes)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), scopes)
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


def upload_file(service, source: Path, folder_id: str, checksum: str) -> str:
    from googleapiclient.http import MediaFileUpload

    metadata = {"name": source.name, "parents": [folder_id], "appProperties": {"cs_sha256": checksum}}
    media = MediaFileUpload(str(source), resumable=True)
    result = service.files().create(body=metadata, media_body=media, fields="id,webViewLink").execute()
    return result.get("webViewLink") or f"https://drive.google.com/open?id={result['id']}"
