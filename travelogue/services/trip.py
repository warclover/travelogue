"""Trip.json load/save and trip directory layout."""

from __future__ import annotations

import json
import os
import tempfile
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
        payload = json.dumps(trip, ensure_ascii=False, indent=2) + "\n"
        fd, tmp_path = tempfile.mkstemp(
            suffix=".json",
            prefix=f".{p.stem}-",
            dir=p.parent,
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(tmp_path, p)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def resolve_trip_root(self, trip_json: Path) -> Path:
        """Directory containing trip.json and assets/."""
        return trip_json.resolve().parent

    def resolve_trip_json(self, trip_id_or_path: str | Path, *, trips_dir: Path | None = None) -> Path:
        """Resolve tripId, trip dir, or trip.json path."""
        p = Path(trip_id_or_path)
        if p.is_file():
            return p.resolve()

        cwd = Path.cwd()
        cwd_trip_json = cwd / "trip.json"
        cwd_trip_id = cwd.name if cwd_trip_json.is_file() else None
        normalized = str(p).replace("\\", "/").strip("/")

        search_roots: list[Path] = [p, self.root / p, cwd / p]
        if cwd_trip_id:
            if p in (Path("."), Path("..")) or normalized in (
                cwd_trip_id,
                f"trips/{cwd_trip_id}",
                f"./{cwd_trip_id}",
            ):
                search_roots.insert(0, cwd)

        seen: set[Path] = set()
        for root in search_roots:
            try:
                resolved = root.resolve()
            except OSError:
                continue
            if resolved in seen:
                continue
            seen.add(resolved)
            if resolved.is_dir():
                trip_json = resolved / "trip.json"
                if trip_json.is_file():
                    return trip_json.resolve()

        if p.suffix == ".json" and p.exists():
            return p.resolve()

        base = trips_dir or (self.root / "trips")
        trip_key = p.name if normalized.startswith("trips/") else str(trip_id_or_path)
        candidate = base / trip_key / "trip.json"
        if candidate.is_file():
            return candidate.resolve()

        if cwd_trip_id and str(trip_id_or_path) == cwd_trip_id:
            return cwd_trip_json.resolve()

        raise TripNotFoundError(f"E_TRIP_NOT_FOUND {trip_id_or_path}")
