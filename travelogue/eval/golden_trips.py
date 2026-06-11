"""Golden trip manifest for Phase 19 book-quality gates."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MANIFEST = _REPO_ROOT / "docs" / "acceptance-records" / "p19-golden-trips.json"


@lru_cache(maxsize=1)
def load_p19_golden_manifest() -> dict[str, Any]:
    if not _MANIFEST.is_file():
        raise FileNotFoundError(f"P19 golden manifest missing: {_MANIFEST}")
    return json.loads(_MANIFEST.read_text(encoding="utf-8"))


def load_p19_golden_trip_ids(*, include_bsp: bool = True) -> list[str]:
    manifest = load_p19_golden_manifest()
    trips = manifest.get("trips") or []
    ids: list[str] = []
    for row in trips:
        role = row.get("gateRole") or "primary"
        if role == "bsp" and not include_bsp:
            continue
        tid = str(row.get("tripId") or "").strip()
        if tid:
            ids.append(tid)
    return ids


def trip_dir_for_id(trip_id: str, *, root: Path | None = None) -> Path:
    base = root or _REPO_ROOT
    return base / "trips" / trip_id


def resolve_existing_golden_trips(root: Path | None = None) -> list[dict[str, Any]]:
    base = root or _REPO_ROOT
    out: list[dict[str, Any]] = []
    for row in load_p19_golden_manifest().get("trips") or []:
        tid = str(row.get("tripId") or "").strip()
        if not tid:
            continue
        trip_dir = trip_dir_for_id(tid, root=base)
        alt = row.get("altTripId")
        if not (trip_dir / "trip.json").is_file() and alt:
            trip_dir = trip_dir_for_id(str(alt), root=base)
            tid = str(alt)
        exists = (trip_dir / "trip.json").is_file()
        out.append({**row, "tripId": tid, "tripDir": str(trip_dir), "exists": exists})
    return out
