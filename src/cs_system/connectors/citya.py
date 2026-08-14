"""Connecteur autonome MyCitya : navigateur pour la session, API GED pour les fichiers."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

from ..settings import Settings

LOGIN_URL = "https://www.citya.com/mycitya"
GED_BASE_URL = "https://my.citya.com/V5/webservice/gedservice/"
ID_SERVICE_URL = "https://my.citya.com/V5/webservice/idservice/index.php"
ID_SERVICE_PARAMS = {"clePortefeuille": "affb468440e9de13775ab6450daad8d3", "login": "ics", "mdp": "ics06@ics.fr", "nomProduit": "Ged", "operation": "get", "retour": "json"}
_ILLEGAL_CHARS = re.compile(r'[\\/:*?"<>|]')


def _safe(value: str) -> str:
    return re.sub(r"\s+", " ", _ILLEGAL_CHARS.sub("_", value).strip()) or "sans_nom"


@dataclass(frozen=True)
class CityaDocument:
    name: str
    extension: str
    location: str
    folders: tuple[str, ...]
    date_created: str | None = None

    @property
    def relative_path(self) -> Path:
        extension = self.extension if self.extension.startswith(".") else f".{self.extension}"
        return Path(*(_safe(part) for part in self.folders)) / f"{_safe(self.name)}{extension}"


class CityaClient:
    def __init__(self, settings: Settings, headed: bool = False):
        if not all((settings.citya_email, settings.citya_password, settings.citya_documents_url, settings.citya_immeuble_id)):
            raise ValueError("Configurer CITYA_EMAIL, CITYA_PASSWORD, CITYA_DOCUMENTS_URL et CITYA_IMMEUBLE_ID dans .env.")
        self.settings, self.headed = settings, headed
        self._pw = self.browser = self.context = self.page = self.token = None

    def __enter__(self):
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch(headless=not self.headed)
        session = self.settings.root / ".state" / "citya-session.json"
        self.context = self.browser.new_context(storage_state=str(session) if session.exists() else None)
        self.page = self.context.new_page()
        return self

    def __exit__(self, *_):
        if self.context:
            session = self.settings.root / ".state" / "citya-session.json"
            session.parent.mkdir(parents=True, exist_ok=True)
            self.context.storage_state(path=str(session))
            self.context.close()
        if self.browser: self.browser.close()
        if self._pw: self._pw.stop()

    def login(self) -> None:
        self.page.goto(self.settings.citya_documents_url, wait_until="networkidle", timeout=60_000)
        if "mycitya" in self.page.url or "connexion" in self.page.url:
            self.page.goto(LOGIN_URL, wait_until="networkidle", timeout=60_000)
            self.page.fill("#login", self.settings.citya_email)
            self.page.fill("#mdp", self.settings.citya_password)
            with self.page.expect_navigation(wait_until="networkidle", timeout=60_000):
                self.page.click("form button[type=submit]")
            self.page.goto(self.settings.citya_documents_url, wait_until="networkidle", timeout=60_000)
            if "mycitya" in self.page.url or "connexion" in self.page.url:
                raise RuntimeError("Echec de connexion MyCitya : verifier les identifiants.")
        response = self.context.request.get(ID_SERVICE_URL, params=ID_SERVICE_PARAMS).json()
        if not response.get("success") or not response.get("token"):
            raise RuntimeError("Impossible d'obtenir le jeton GED MyCitya.")
        self.token = response["token"]

    def _get(self, endpoint: str, **params) -> dict:
        response = self.context.request.get(endpoint, params=params)
        if not response.ok: raise RuntimeError(f"Erreur GED {response.status} : {endpoint}")
        data = response.json()
        if data.get("responseCode") not in (None, "200"): raise RuntimeError(f"Erreur GED : {data.get('msg')}")
        return data

    def list_documents(self) -> list[CityaDocument]:
        root = self._get(GED_BASE_URL + "GetEntityContentServlet", cabinet="true", droits="Conseil syndical", id=self.settings.citya_immeuble_id, isPermissionFilterEnabled="true", page=1, resultNumber=500, sortName="DESCENDING_DATE", toJson="true", token=self.token, type="Immeuble")["payload"]
        root_name = root["directory"]["nom"]
        result, stack = [], [(root, (root_name,))]
        while stack:
            payload, folders = stack.pop()
            result.extend(
                CityaDocument(d["nom"], d.get("extension", ""), d["emplacement"], folders, d.get("dateCreated") or d.get("dateUpload"))
                for d in payload.get("docs", [])
            )
            for child in payload.get("sons", []):
                data = self._get(GED_BASE_URL + "SearchArborescenceContentServlet", cabinet="true", droits="Conseil syndical", id=child["idArbo"], page=1, resultNumber=500, sortName="DESCENDING_DATE", toJson="true", token=self.token)["payload"]
                stack.append((data, folders + (child["nom"],)))
        return result

    def download(self, document: CityaDocument, destination: Path) -> Path:
        target = destination / document.relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        location, extension = document.location, document.extension
        if extension.casefold() == ".pcl":
            converted = self._get(GED_BASE_URL + "pcl2PdfServlet", cabinet="true", token=self.token, emplacement=location)["payload"]
            location, extension, target = converted["emplacement"], converted["extension"], target.with_suffix(converted["extension"])
        response = self.context.request.get(GED_BASE_URL + "getFileByFTPServlet", params={"token": self.token, "emplacement": location, "cabinet": "true", "nomFile": document.name, "extension": extension}, timeout=120_000)
        if not response.ok: raise RuntimeError(f"Telechargement echoue ({response.status}) : {document.name}")
        target.write_bytes(response.body())
        if document.date_created:
            timestamp = datetime.strptime(document.date_created, "%Y-%m-%d %H:%M:%S").timestamp()
            os.utime(target, (timestamp, timestamp))
        return target


def sync(settings: Settings, *, new_only: bool, headed: bool) -> tuple[int, int]:
    manifest_path = settings.root / ".state" / "citya-manifest.json"
    known = set(json.loads(manifest_path.read_text(encoding="utf-8"))) if manifest_path.exists() else set()
    with CityaClient(settings, headed) as client:
        client.login()
        documents = client.list_documents()
        todo = [document for document in documents if not new_only or document.location not in known]
        for document in todo:
            target = settings.citya_documents_dir / document.relative_path
            if not target.exists(): client.download(document, settings.citya_documents_dir)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(sorted(doc.location for doc in documents), ensure_ascii=False, indent=2), encoding="utf-8")
    return len(documents), len(todo)
