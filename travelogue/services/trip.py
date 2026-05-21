"""Trip.json load/save and trip directory layout."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.services.validate import load_json


class TripNotFoundError(FileNotFoundError):
    pass


class TripService:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path.cwd()

    def trip_dir(self, trip_id: str) -> Path:
        return self.root / "trips" / trip_id

    def trip_json_path(self, trip_id: str) -> Path:
        return self.trip_dir(trip_id) / "trip.json"

    def load(self, path: Path | str) -> dict:
        p = Path(path)
        if not p.is_file():
            raise TripNotFoundError(f"E_TRIP_NOT_FOUND {p}")
        return load_json(p)

    def save(self, trip: dict, path: Path | str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(trip, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def resolve_trip_root(self, trip_json: Path) -> Path:
        """Directory containing trip.json and assets/."""
        return trip_json.resolve().parent

    def resolve_trip_json(self, trip_id_or_path: str | Path, *, trips_dir: Path | None = None) -> Path:
        """Resolve tripId or path to trip.json."""
        p = Path(trip_id_or_path)
        if p.is_file():
            return p.resolve()
        if p.suffix == ".json" and p.exists():
            return p.resolve()
        base = trips_dir or (self.root / "trips")
        candidate = base / str(trip_id_or_path) / "trip.json"
        if candidate.is_file():
            return candidate.resolve()
        raise TripNotFoundError(f"E_TRIP_NOT_FOUND {trip_id_or_path}")
