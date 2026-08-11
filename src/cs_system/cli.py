from __future__ import annotations

import argparse
from pathlib import Path

from .pipelines import contacts, documents, forms
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
    capture = sub.add_parser("capture-documents", help="planifier ou copier les documents Citya dans Drive")
    capture.add_argument("--apply", action="store_true", help="envoyer effectivement dans Google Drive")
    citya = sub.add_parser("citya-sync", help="telecharger les documents MyCitya dans data/citya-documents")
    citya.add_argument("--new", action="store_true", help="ne telecharger que les documents apparus depuis le dernier controle")
    citya.add_argument("--headed", action="store_true", help="afficher le navigateur pendant la connexion")
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
    elif args.command == "citya-sync":
        total, downloaded = citya_sync(load_settings(), new_only=args.new, headed=args.headed)
        print(f"{downloaded} document(s) telecharge(s) sur {total} document(s) Citya connus.")
    elif args.command == "capture-documents":
        plans = documents.run(load_settings(), args.apply)
        verb = "envoyes" if args.apply else "a envoyer"
        print(f"{len(plans)} document(s) {verb}.")
        for item in plans:
            print(f"- {item.source} ({item.checksum[:12]})")
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
