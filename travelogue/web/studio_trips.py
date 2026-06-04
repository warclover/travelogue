"""List trips for Studio workbench."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def _longshot_files(trip_dir: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in (
        "*-longshot.png",
        "*-longshot.jpg",
        "*-longshot.jpeg",
        "*-ch*.png",
        "*-ch*.jpg",
        "*-ch*.jpeg",
    ):
        files.extend(trip_dir.glob(pattern))
    return files


def _trip_updated_at(trip_json: Path, data: dict) -> float:
    updated = data.get("updatedAt")
    if updated:
        try:
            dt = datetime.fromisoformat(str(updated).replace("Z", "+00:00"))
            return dt.timestamp()
        except ValueError:
            pass
    return trip_json.stat().st_mtime


def _pick_preview(trip_dir: Path) -> str | None:
    """Return cover: preview.jpg → ch01 (png/jpg) → longshot (png/jpg)."""
    primary = trip_dir / "preview.jpg"
    if primary.is_file():
        return "preview.jpg"
    ch01 = sorted(list(trip_dir.glob("*-ch01.png")) + list(trip_dir.glob("*-ch01.jpg")) + list(trip_dir.glob("*-ch01.jpeg")))
    if ch01:
        return ch01[0].name
    longshots = sorted(
        list(trip_dir.glob("*-longshot.png"))
        + list(trip_dir.glob("*-longshot.jpg"))
        + list(trip_dir.glob("*-longshot.jpeg"))
    )
    if longshots:
        return longshots[0].name
    any_ch = sorted(
        list(trip_dir.glob("*-ch*.png"))
        + list(trip_dir.glob("*-ch*.jpg"))
        + list(trip_dir.glob("*-ch*.jpeg"))
    )
    if any_ch:
        return any_ch[0].name
    return None


def longshot_outputs_stale(trip_dir: Path, *, trip_mtime: float) -> bool:
    files = _longshot_files(trip_dir)
    if not files:
        return False
    latest_png = max(p.stat().st_mtime for p in files)
    return trip_mtime > latest_png + 0.5


def has_longshot_exports(trip_dir: Path) -> bool:
    """True when trip folder contains server-exported longshot images (png/jpg)."""
    return bool(_longshot_files(trip_dir))


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
        template_meta: dict = {}
        if data:
            from travelogue.templating.summary import build_template_summary

            template_meta = build_template_summary(data)
        preview_rel = _pick_preview(child)
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
                    "hasLongshotExport": has_longshot_exports(child),
                    "previewRelPath": preview_rel,
                    "resolvedTemplateId": template_meta.get("resolvedTemplateId", "visual-journal"),
                    "templateSource": template_meta.get("source", "legacy"),
                    "templateSourceLabel": template_meta.get("sourceLabel", "默认模板"),
                    "templateLocked": bool(template_meta.get("locked")),
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
