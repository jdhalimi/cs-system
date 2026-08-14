from __future__ import annotations

import argparse
from pathlib import Path

from .pipelines import contacts, documents, forms, google, notion
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
    google_parser = sub.add_parser("google", help="operations sur les sources Google (contacts, drive)")
    google_sub = google_parser.add_subparsers(dest="google_command", required=True)
    google_export = google_sub.add_parser("export", help="exporter/reindexer les sources Google dans data/exports/google")
    google_export.add_argument(
        "--scope", help=f"sous-ensemble a traiter, separe par des virgules ({', '.join(google.SCOPES)}) ; toutes par defaut",
    )

    notion_parser = sub.add_parser("notion", help="operations sur les bases Notion partagees avec l'integration")
    notion_sub = notion_parser.add_subparsers(dest="notion_command", required=True)
    notion_export = notion_sub.add_parser("export", help="exporter toutes les bases Notion partagees dans data/exports/notion")
    notion_export.add_argument(
        "--scope",
        help="sous-ensemble a exporter, separe par des virgules (slugs derives du titre Notion) ; toutes par defaut",
    )

    match_parser = sub.add_parser("match", help="rapprochements entre sources")
    match_sub = match_parser.add_subparsers(dest="match_command", required=True)
    match_contacts = match_sub.add_parser("contacts", help="rapprocher les Google Contacts et les contacts Notion")
    match_contacts.add_argument("--interactive", action="store_true", help="confirmer manuellement les correspondances approximatives")
    match_contacts.add_argument("--out", type=Path, help="chemin de sortie (defaut : data/local/contacts-match.csv)")

    citya = sub.add_parser("citya", help="operations sur les documents MyCitya")
    citya_sub = citya.add_subparsers(dest="citya_command", required=True)
    citya_export = citya_sub.add_parser("export", help="telecharger les documents MyCitya dans data/citya-documents")
    citya_export.add_argument("--new", action="store_true", help="ne telecharger que les documents apparus depuis le dernier controle")
    citya_export.add_argument("--headed", action="store_true", help="afficher le navigateur pendant la connexion")
    citya_capture = citya_sub.add_parser("capture", help="planifier ou copier les documents Citya dans Drive")
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
    elif args.command == "citya" and args.citya_command == "export":
        total, downloaded = citya_sync(load_settings(), new_only=args.new, headed=args.headed)
        print(f"{downloaded} document(s) telecharge(s) sur {total} document(s) Citya connus.")
    elif args.command == "citya" and args.citya_command == "capture":
        plans = documents.run(load_settings(), args.apply)
        verb = "envoyes" if args.apply else "a envoyer"
        print(f"{len(plans)} document(s) {verb}.")
        for item in plans:
            print(f"- [{item.status}] {item.source} ({item.checksum[:12]})")
    elif args.command == "google" and args.google_command == "export":
        scope = tuple(part.strip() for part in args.scope.split(",")) if args.scope else None
        results = google.export(load_settings(), scope)
        for name, result in results.items():
            if name == "drive":
                print(f"{len(result)} document(s) indexe(s) depuis Drive -> data/exports/google/drive/manifest.json")
            else:
                print(f"{name.capitalize()} Google exportes -> {result}")
        skipped = [name for name in (scope or tuple(google.SCOPES)) if name not in results]
        if skipped:
            print(f"Ignore (non configure) : {', '.join(skipped)}")
    elif args.command == "notion" and args.notion_command == "export":
        scope = tuple(part.strip() for part in args.scope.split(",")) if args.scope else None
        results = notion.export(load_settings(), scope)
        for name, path in results.items():
            print(f"{name} Notion exportee -> {path}")
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
