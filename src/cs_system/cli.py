from __future__ import annotations

import argparse
from pathlib import Path

from .pipelines import contacts, documents, forms, lots
from .settings import load_settings
from .connectors.citya import sync as citya_sync
from .pipelines.sync.indexes import build as build_indexes
from .workspace import Workspace


def main() -> int:
    parser = argparse.ArgumentParser(prog="cs-system", description="Pipelines du conseil syndical")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("workspace-init", help="créer l'arborescence de données locale")
    index = sub.add_parser("sync-index", help="reconstruire les index des exports locaux")
    index.add_argument("--source", help="source à indexer (notion, google, citya ou forms)")
    google_drive = sub.add_parser("google-drive", help="operations sur le dossier Google Drive")
    google_drive_sub = google_drive.add_subparsers(dest="google_drive_command", required=True)
    google_drive_sub.add_parser("index", help="reindexer le contenu reel du dossier Drive dans data/exports/google/drive")

    google_contacts = sub.add_parser("google-contacts", help="operations sur les Google Contacts")
    google_contacts_sub = google_contacts.add_subparsers(dest="google_contacts_command", required=True)
    google_contacts_sub.add_parser("export", help="exporter les Google Contacts dans data/exports/google/contacts")

    notion_contacts = sub.add_parser("notion-contacts", help="operations sur les bases Notion Proprietaires et Locataires")
    notion_contacts_sub = notion_contacts.add_subparsers(dest="notion_contacts_command", required=True)
    notion_contacts_sub.add_parser("export", help="exporter Proprietaires et Locataires dans data/exports/notion")

    notion_lots = sub.add_parser("notion-lots", help="operations sur la base Notion des lots")
    notion_lots_sub = notion_lots.add_subparsers(dest="notion_lots_command", required=True)
    notion_lots_sub.add_parser("export", help="exporter la base Notion des lots dans data/exports/notion/lots")

    match_parser = sub.add_parser("match", help="rapprochements entre sources")
    match_sub = match_parser.add_subparsers(dest="match_command", required=True)
    match_contacts = match_sub.add_parser("contacts", help="rapprocher les Google Contacts et les contacts Notion")
    match_contacts.add_argument("--interactive", action="store_true", help="confirmer manuellement les correspondances approximatives")
    match_contacts.add_argument("--out", type=Path, help="chemin de sortie (defaut : data/local/contacts-match.csv)")

    citya_docs = sub.add_parser("citya-docs", help="operations sur les documents MyCitya")
    citya_docs_sub = citya_docs.add_subparsers(dest="citya_docs_command", required=True)
    citya_export = citya_docs_sub.add_parser("export", help="telecharger les documents MyCitya dans data/citya-documents")
    citya_export.add_argument("--new", action="store_true", help="ne telecharger que les documents apparus depuis le dernier controle")
    citya_export.add_argument("--headed", action="store_true", help="afficher le navigateur pendant la connexion")
    citya_capture = citya_docs_sub.add_parser("capture", help="planifier ou copier les documents Citya dans Drive")
    citya_capture.add_argument("--apply", action="store_true", help="envoyer effectivement dans Google Drive")
    compare = sub.add_parser("compare-contacts", help="comparer deux exports CSV de contacts")
    compare.add_argument("google", type=Path)
    compare.add_argument("notion", type=Path)
    compare.add_argument("--out", type=Path, required=True)
    ingest = sub.add_parser("ingest-form", help="transformer un export CSV Google Forms en registre d'actions")
    ingest.add_argument("source", type=Path)
    ingest.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "workspace-init":
        workspace = Workspace(Path.cwd().resolve())
        workspace.ensure()
        print(f"Espace de travail prêt : {workspace.data}")
    elif args.command == "sync-index":
        counts = build_indexes(Workspace(Path.cwd().resolve()), args.source)
        print("Indexes reconstruits : " + ", ".join(f"{source}={count}" for source, count in counts.items()))
    elif args.command == "citya-docs" and args.citya_docs_command == "export":
        total, downloaded = citya_sync(load_settings(), new_only=args.new, headed=args.headed)
        print(f"{downloaded} document(s) telecharge(s) sur {total} document(s) Citya connus.")
    elif args.command == "citya-docs" and args.citya_docs_command == "capture":
        plans = documents.run(load_settings(), args.apply)
        verb = "envoyes" if args.apply else "a envoyer"
        print(f"{len(plans)} document(s) {verb}.")
        for item in plans:
            print(f"- [{item.status}] {item.source} ({item.checksum[:12]})")
    elif args.command == "google-drive":
        index = documents.sync_drive_index(load_settings())
        print(f"{len(index)} document(s) indexe(s) depuis Drive -> data/exports/google/drive/manifest.json")
    elif args.command == "google-contacts":
        output = contacts.export_google_contacts(load_settings())
        print(f"Contacts Google exportes -> {output}")
    elif args.command == "notion-contacts":
        proprietaires, locataires = contacts.export_notion_contacts(load_settings())
        print(f"Contacts Notion exportes -> {proprietaires}, {locataires}")
    elif args.command == "notion-lots":
        output = lots.export_notion_lots(load_settings())
        print(f"Lots Notion exportes -> {output}")
    elif args.command == "match" and args.match_command == "contacts":
        settings = load_settings()
        rows = contacts.match(settings, interactive=args.interactive)
        output = args.out or settings.root / "data" / "local" / "contacts-match.csv"
        contacts.write(rows, output)
        print(f"{len(rows)} identite(s) rapprochee(s) -> {output}")
    elif args.command == "compare-contacts":
        rows = contacts.compare(args.google, args.notion)
        contacts.write(rows, args.out)
        print(f"{len(rows)} identite(s) comparee(s) -> {args.out}")
    else:
        accepted, rejected = forms.ingest(args.source, args.out)
        print(f"{accepted} reponse(s) a traiter, {rejected} ignoree(s) -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
