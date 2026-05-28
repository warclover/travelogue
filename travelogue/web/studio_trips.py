"""List trips for Studio workbench."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def _trip_updated_at(trip_json: Path, data: dict) -> float:
    updated = data.get("updatedAt")
    if updated:
        try:
            dt = datetime.fromisoformat(str(updated).replace("Z", "+00:00"))
            return dt.timestamp()
        except ValueError:
            pass
    return trip_json.stat().st_mtime


def longshot_outputs_stale(trip_dir: Path, *, trip_mtime: float) -> bool:
    pngs = list(trip_dir.glob("*-longshot.png")) + list(trip_dir.glob("*-ch*.png"))
    if not pngs:
        return False
    latest_png = max(p.stat().st_mtime for p in pngs)
    return trip_mtime > latest_png + 0.5


def _trip_rows(trips_dir: Path) -> list[tuple[float, dict]]:
    trips_dir = trips_dir.resolve()
    if not trips_dir.is_dir():
        return []

    rows: list[tuple[float, dict]] = []
    for child in trips_dir.iterdir():
        if not child.is_dir() or child.name.startswith("_"):
            continue
        trip_json = child / "trip.json"
        if not trip_json.is_file():
            continue
        title = child.name
        updated_at = trip_json.stat().st_mtime
        photo_count = 0
        try:
            data = json.loads(trip_json.read_text(encoding="utf-8"))
            title = (data.get("meta") or {}).get("title") or title
            updated_at = _trip_updated_at(trip_json, data)
            photo_count = sum(
                1 for a in data.get("assets") or [] if a.get("type", "image") == "image"
            )
        except (OSError, json.JSONDecodeError):
            data = {}
        preview = child / "preview.jpg"
        preview_rel = "preview.jpg" if preview.is_file() else None
        rows.append(
            (
                updated_at,
                {
                    "tripId": child.name,
                    "title": title,
                    "previewUrl": f"/{child.name}/index.html",
                    "updatedAt": updated_at,
                    "photoCount": photo_count,
                    "longshotStale": longshot_outputs_stale(child, trip_mtime=updated_at),
                    "previewRelPath": preview_rel,
                },
            )
        )

    rows.sort(key=lambda item: item[0], reverse=True)
    return rows


def list_studio_trips(trips_dir: Path, *, limit: int = 20, offset: int = 0) -> list[dict]:
    rows = _trip_rows(trips_dir)
    return [row[1] for row in rows[offset : offset + limit]]


def studio_trips_total(trips_dir: Path) -> int:
    return len(_trip_rows(trips_dir))
