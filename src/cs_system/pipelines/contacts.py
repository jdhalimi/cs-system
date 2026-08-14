from __future__ import annotations

import csv
import difflib
import re
from pathlib import Path
from typing import Callable

from ..connectors.google import list_contact_group_names, list_people
from ..connectors.notion import export_table
from ..settings import Settings
from .lots import read_lots

STATUS_COMMUN = "commun"
STATUS_EMAIL = "rapproche_email"
STATUS_MANUEL = "rapproche_manuel"
STATUS_GOOGLE_SEUL = "google_seul"
STATUS_NOTION_SEUL = "notion_seul"

IGNORED_GOOGLE_LABELS = {"Fournisseurs"}

# Convention constatee dans les groupes Google : "Propriétaire A1"/"Locataire B3" signifie
# l'escalier 1 du batiment A ; "Propriétaire P" signifie un parking, sans localisation precise.
_ESCALIER_LABEL_RE = re.compile(r"^(Propriétaire|Locataire) ([A-Z]\d)$")
_PARKING_LABEL_RE = re.compile(r"^(Propriétaire|Locataire) P$")
_ROLE_BY_LABEL = {"Propriétaire": "proprietaire", "Locataire": "locataire"}


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


# Seuil bas car les cles comparees sont deja tres courtes (prenom+nom sans separateur) :
# un cutoff eleve laisse passer trop peu de vraies correspondances (ex. inversions prenom/nom).
_INTERACTIVE_CUTOFF = 0.55


def _swapped_key(entry: dict) -> str:
    """Cle avec prenom et nom inverses, pour retrouver les fiches ou l'un des deux systemes les a intervertis."""
    first = entry.get("First Name") or entry.get("Prenom") or ""
    last = entry.get("Last Name") or entry.get("Nom") or ""
    return _norm(f"{last} {first}")


def _read(path: Path, source: str) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = csv.DictReader(stream)
        result = {}
        for row in rows:
            first = row.get("First Name") or row.get("Prenom") or ""
            last = row.get("Last Name") or row.get("Nom") or ""
            key = _norm(f"{first} {last}")
            if key:
                result[key] = {"source": source, "nom": f"{first} {last}".strip(), **row}
        return result


def _label(entry: dict) -> str:
    return entry.get("formattedType") or entry.get("type", "")


def google_contacts_export_path(settings: Settings) -> Path:
    return settings.root / "data" / "exports" / "google" / "contacts" / "contacts.csv"


def _group_labels(person: dict, group_names: dict[str, str]) -> str:
    resource_names = (
        membership.get("contactGroupMembership", {}).get("contactGroupResourceName")
        for membership in person.get("memberships", [])
    )
    return " ::: ".join(sorted(group_names[name] for name in resource_names if name in group_names))


def export_google_contacts(settings: Settings) -> Path:
    """Exporte les Google Contacts en CSV, sans rien y ecrire."""
    people = list_people(settings.google_client_secrets, settings.google_token_file)
    group_names = list_contact_group_names(settings.google_client_secrets, settings.google_token_file)
    contacts = []
    for person in people:
        name = (person.get("names") or [{}])[0]
        contacts.append((name, _group_labels(person, group_names), person.get("emailAddresses", []), person.get("phoneNumbers", [])))
    max_emails = max((len(emails) for _, _, emails, _ in contacts), default=0)
    max_phones = max((len(phones) for _, _, _, phones in contacts), default=0)
    fieldnames = ["First Name", "Last Name", "Labels"]
    for i in range(1, max_emails + 1):
        fieldnames += [f"E-mail {i} - Label", f"E-mail {i} - Value"]
    for i in range(1, max_phones + 1):
        fieldnames += [f"Phone {i} - Label", f"Phone {i} - Value"]
    rows = []
    for name, labels, emails, phones in contacts:
        row = {"First Name": name.get("givenName", ""), "Last Name": name.get("familyName", ""), "Labels": labels}
        for i in range(1, max_emails + 1):
            entry = emails[i - 1] if i <= len(emails) else {}
            row[f"E-mail {i} - Label"], row[f"E-mail {i} - Value"] = _label(entry), entry.get("value", "")
        for i in range(1, max_phones + 1):
            entry = phones[i - 1] if i <= len(phones) else {}
            row[f"Phone {i} - Label"], row[f"Phone {i} - Value"] = _label(entry), entry.get("value", "")
        rows.append(row)
    output = google_contacts_export_path(settings)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return output


def notion_proprietaires_export_path(settings: Settings) -> Path:
    return settings.root / "data" / "exports" / "notion" / "proprietaires" / "proprietaires.csv"


def notion_locataires_export_path(settings: Settings) -> Path:
    return settings.root / "data" / "exports" / "notion" / "locataires" / "locataires.csv"


def export_notion_contacts(settings: Settings) -> tuple[Path, Path]:
    """Exporte les bases Notion Proprietaires et Locataires en CSV, sans rien y ecrire."""
    proprietaires = export_table(settings.notion_token, settings.notion_proprietaires_database_id, notion_proprietaires_export_path(settings))
    locataires = export_table(settings.notion_token, settings.notion_locataires_database_id, notion_locataires_export_path(settings))
    return proprietaires, locataires


def compare(google_csv: Path, notion_csv: Path) -> list[dict[str, str]]:
    google, notion = _read(google_csv, "google"), _read(notion_csv, "notion")
    rows = []
    for key in sorted(set(google) | set(notion)):
        g, n = google.get(key), notion.get(key)
        status = "commun" if g and n else "google_seul" if g else "notion_seul"
        rows.append({"cle": key, "statut": status, "google": g["nom"] if g else "", "notion": n["nom"] if n else ""})
    return rows


def write(rows: list[dict[str, str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["cle", "statut", "google", "notion", "telephone", "email", "anomalies"])
        writer.writeheader()
        writer.writerows(rows)


def _emails(entry: dict) -> set[str]:
    return {
        value.strip().lower()
        for key, value in entry.items()
        if "mail" in key.lower() and value and value.strip()
    }


def _has_phone(entry: dict) -> bool:
    return any(
        value and value.strip()
        for key, value in entry.items()
        if "phone" in key.lower() or "telephone" in key.lower()
    )


def _phone_value(entry: dict) -> str:
    return next(
        (value.strip() for key, value in entry.items() if ("phone" in key.lower() or "telephone" in key.lower()) and value and value.strip()),
        "",
    )


def _email_value(entry: dict) -> str:
    return next((value.strip() for key, value in entry.items() if "mail" in key.lower() and value and value.strip()), "")


def _merged_field(google_entry: dict, notion_entry: dict, getter: Callable[[dict], str]) -> str:
    """Comble le champ manquant d'un cote avec la valeur de l'autre (Notion prioritaire si les deux existent)."""
    return getter(notion_entry) or getter(google_entry)


def _location_hints(labels: str) -> list[tuple[str, str]]:
    """Extrait (role, escalier ou 'parking') des labels Google 'Propriétaire A1' / 'Propriétaire P'."""
    hints = []
    for label in labels.split(" ::: "):
        escalier_match = _ESCALIER_LABEL_RE.match(label)
        if escalier_match:
            hints.append((_ROLE_BY_LABEL[escalier_match.group(1)], escalier_match.group(2)))
            continue
        parking_match = _PARKING_LABEL_RE.match(label)
        if parking_match:
            hints.append((_ROLE_BY_LABEL[parking_match.group(1)], "parking"))
    return hints


def _lot_ids(entry: dict) -> list[str]:
    raw = entry.get("Lots") or entry.get("Lots loues") or ""
    return [lot_id.strip() for lot_id in raw.split(",") if lot_id.strip()]


def _location_tokens(entry: dict, lots_by_id: dict[str, dict[str, str]]) -> set[str]:
    tokens: set[str] = set()
    for lot_id in _lot_ids(entry):
        lot = lots_by_id.get(lot_id)
        if not lot:
            continue
        if lot.get("Type", "").strip().casefold() == "parking":
            tokens.add("parking")
        escalier = lot.get("Escalier", "").strip()
        if escalier:
            tokens.add(escalier)
    return tokens


def _anomalies(google_entry: dict, notion_entry: dict, lots_by_id: dict[str, dict[str, str]]) -> list[str]:
    """Signale les incoherences entre le contact rapproche et les donnees Notion (role, escalier, telephone)."""
    issues = []
    roles = set(notion_entry.get("role", "").split("+")) - {""}
    tokens = _location_tokens(notion_entry, lots_by_id)
    for hint_role, hint_token in _location_hints(google_entry.get("Labels", "")):
        if roles and hint_role not in roles:
            issues.append(f"role Google '{hint_role}' absent cote Notion ({'+'.join(sorted(roles))})")
        elif tokens and hint_token not in tokens:
            issues.append(f"escalier Google '{hint_token}' absent des lots Notion ({', '.join(sorted(tokens))})")
    if not _has_phone(notion_entry) and not _has_phone(google_entry):
        issues.append("telephone absent")
    return issues


def _notion_label(entry: dict) -> str:
    return f"{entry['nom']} ({entry['role']})"


def _merge_notion(*sources: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for source in sources:
        for key, entry in source.items():
            if key in merged:
                merged[key] = {**merged[key], "role": f"{merged[key]['role']}+{entry['role']}"}
            else:
                merged[key] = dict(entry)
    return merged


def _match_by_email(google: dict, notion: dict) -> list[tuple[str, str]]:
    """Associe les entrees google/notion restantes qui partagent un email."""
    email_to_notion: dict[str, str] = {}
    for key, entry in notion.items():
        for email in _emails(entry):
            email_to_notion.setdefault(email, key)
    pairs = []
    for key, entry in google.items():
        for email in _emails(entry):
            notion_key = email_to_notion.get(email)
            if notion_key:
                pairs.append((key, notion_key))
                break
    return pairs


def _matched_row(key: str, status: str, google_entry: dict, notion_entry: dict, lots_by_id: dict[str, dict[str, str]]) -> dict[str, str]:
    return {
        "cle": key, "statut": status, "google": google_entry["nom"], "notion": _notion_label(notion_entry),
        "telephone": _merged_field(google_entry, notion_entry, _phone_value),
        "email": _merged_field(google_entry, notion_entry, _email_value),
        "anomalies": "; ".join(_anomalies(google_entry, notion_entry, lots_by_id)),
    }


def _review_interactively(
    google_left: dict, notion_left: dict, results: dict, prompt: Callable[[str], str], lots_by_id: dict[str, dict[str, str]],
) -> None:
    for google_key in list(google_left):
        entry = google_left[google_key]
        swapped_key = _swapped_key(entry)
        candidate_keys = set(difflib.get_close_matches(google_key, notion_left.keys(), n=5, cutoff=_INTERACTIVE_CUTOFF))
        if swapped_key != google_key:
            candidate_keys |= set(difflib.get_close_matches(swapped_key, notion_left.keys(), n=5, cutoff=_INTERACTIVE_CUTOFF))
        if not candidate_keys:
            continue

        def _score(candidate_key: str) -> float:
            return max(
                difflib.SequenceMatcher(None, google_key, candidate_key).ratio(),
                difflib.SequenceMatcher(None, swapped_key, candidate_key).ratio(),
            )

        candidates = sorted(candidate_keys, key=_score, reverse=True)[:3]
        print(f"\nGoogle seul : {entry['nom']}")
        for position, candidate_key in enumerate(candidates, start=1):
            print(f"  {position}. {_notion_label(notion_left[candidate_key])}")
        answer = prompt("Rapprocher avec quel numero ? (Entree pour ignorer, q pour arreter) ").strip().lower()
        if answer == "q":
            return
        if answer.isdigit() and 1 <= int(answer) <= len(candidates):
            notion_key = candidates[int(answer) - 1]
            notion_entry = notion_left[notion_key]
            results[google_key] = _matched_row(google_key, STATUS_MANUEL, entry, notion_entry, lots_by_id)
            del google_left[google_key]
            del notion_left[notion_key]


def match(settings: Settings, interactive: bool = False, prompt: Callable[[str], str] = input) -> list[dict[str, str]]:
    """Rapproche les Google Contacts et les contacts Notion (proprietaires + locataires)."""
    google_path = google_contacts_export_path(settings)
    proprietaires_path = notion_proprietaires_export_path(settings)
    locataires_path = notion_locataires_export_path(settings)
    for path in (google_path, proprietaires_path, locataires_path):
        if not path.exists():
            raise FileNotFoundError(f"Export introuvable : {path}. Lancer d'abord google-contacts export et notion-contacts export.")
    lots_by_id = read_lots(settings)

    google = {
        key: entry for key, entry in _read(google_path, "google").items()
        if not IGNORED_GOOGLE_LABELS & set(entry.get("Labels", "").split(" ::: "))
    }
    proprietaires = {key: {**entry, "role": "proprietaire"} for key, entry in _read(proprietaires_path, "notion").items()}
    locataires = {key: {**entry, "role": "locataire"} for key, entry in _read(locataires_path, "notion").items()}
    notion = _merge_notion(proprietaires, locataires)

    common = sorted(set(google) & set(notion))
    google_left = {key: entry for key, entry in google.items() if key not in common}
    notion_left = {key: entry for key, entry in notion.items() if key not in common}

    email_pairs = _match_by_email(google_left, notion_left)

    results: dict[str, dict[str, str]] = {}
    for key in common:
        results[key] = _matched_row(key, STATUS_COMMUN, google[key], notion[key], lots_by_id)
    for google_key, notion_key in email_pairs:
        if google_key not in google_left or notion_key not in notion_left:
            continue
        results[google_key] = _matched_row(google_key, STATUS_EMAIL, google_left[google_key], notion_left[notion_key], lots_by_id)
        del google_left[google_key]
        del notion_left[notion_key]

    if interactive:
        _review_interactively(google_left, notion_left, results, prompt, lots_by_id)

    for key, entry in google_left.items():
        results.setdefault(key, {
            "cle": key, "statut": STATUS_GOOGLE_SEUL, "google": entry["nom"], "notion": "",
            "telephone": _phone_value(entry), "email": _email_value(entry), "anomalies": "",
        })
    for key, entry in notion_left.items():
        results.setdefault(key, {
            "cle": key, "statut": STATUS_NOTION_SEUL, "google": "", "notion": _notion_label(entry),
            "telephone": _phone_value(entry), "email": _email_value(entry), "anomalies": "",
        })

    return [results[key] for key in sorted(results)]
