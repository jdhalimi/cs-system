"""Convention unique des répertoires de données de cs-system."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Workspace:
    root: Path

    @property
    def data(self) -> Path: return self.root / "data"
    @property
    def exports(self) -> Path: return self.data / "exports"
    @property
    def cache(self) -> Path: return self.data / "cache"
    @property
    def indexes(self) -> Path: return self.data / "indexes"
    @property
    def local(self) -> Path: return self.data / "local"
    @property
    def reports(self) -> Path: return self.root / "reports"
    @property
    def state(self) -> Path: return self.root / ".state"

    def ensure(self) -> None:
        for path in (self.exports, self.cache, self.indexes, self.local, self.reports, self.state):
            path.mkdir(parents=True, exist_ok=True)
        for source, entities in {
            # Notion : proprietaires/lots/locataires sont necessaires a `match contacts` ; les autres
            # bases partagees avec l'integration sont decouvertes et creees a la volee par `notion export`.
            "notion": ("proprietaires", "lots", "locataires"),
            "google": ("contacts", "drive"),
            "citya": ("documents",),
            "forms": ("responses",),
        }.items():
            for entity in entities:
                (self.exports / source / entity).mkdir(parents=True, exist_ok=True)
                (self.cache / source / entity).mkdir(parents=True, exist_ok=True)
                (self.local / source / entity).mkdir(parents=True, exist_ok=True)

