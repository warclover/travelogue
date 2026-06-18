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


def _asset_rel_path(trip_dir: Path, asset: dict) -> str | None:
    """Resolve on-disk relative path for a cover asset (mobile display variant)."""
    from travelogue.render.context import pick_image_src

    rel = pick_image_src(asset, export_layout="mobile")
    if rel:
        path = trip_dir / rel
        if path.is_file():
            return rel.replace("\\", "/")
    paths = asset.get("paths") or {}
    if isinstance(paths, dict):
        for key in ("w800", "w1600", "w2400", "w3200"):
            candidate = paths.get(key)
            if not candidate:
                continue
            path = trip_dir / candidate
            if path.is_file():
                return str(candidate).replace("\\", "/")
    source = asset.get("sourceFile")
    if source and (trip_dir / source).is_file():
        return str(source).replace("\\", "/")
    return None


def _pick_shelf_cover_rel(trip_dir: Path, data: dict) -> str | None:
    """Portrait-oriented shelf thumbnail (mobile cover), not web letterboxed preview.jpg."""
    if data:
        try:
            from travelogue.curation.curate import resolve_cover_asset_id
            from travelogue.services.validate import asset_map

            cover_id = resolve_cover_asset_id(data, export_layout="mobile")
            if cover_id:
                asset = asset_map(data).get(cover_id)
                if asset:
                    rel = _asset_rel_path(trip_dir, asset)
                    if rel:
                        return rel
            primary = str(data.get("coverAssetId") or "").strip()
            if primary and primary != cover_id:
                asset = asset_map(data).get(primary)
                if asset:
                    rel = _asset_rel_path(trip_dir, asset)
                    if rel:
                        return rel
        except Exception:
            pass
    return _pick_preview(trip_dir)


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
        freshness: dict = {}
        if data:
            from travelogue.curation.algorithm_profile import assess_algorithm_freshness
            from travelogue.templating.summary import build_template_summary

            template_meta = build_template_summary(data)
            freshness = assess_algorithm_freshness(data, child)
        preview_rel = _pick_preview(child)
        shelf_cover_rel = _pick_shelf_cover_rel(child, data)
        layout_css_stale = False
        if data:
            from travelogue.layout_templates.css_stale import trip_layout_css_stale

            layout_css_stale = trip_layout_css_stale(child, data)
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
                    "layoutCssStale": layout_css_stale,
                    "hasLongshotExport": has_longshot_exports(child),
                    "previewRelPath": preview_rel,
                    "shelfCoverRelPath": shelf_cover_rel,
                    "resolvedTemplateId": template_meta.get("resolvedTemplateId", "visual-journal"),
                    "templateSource": template_meta.get("source", "legacy"),
                    "templateSourceLabel": template_meta.get("sourceLabel", "默认模板"),
                    "templateLocked": bool(template_meta.get("locked")),
                    "algorithmStale": bool(freshness.get("algorithmStale")),
                    "aestheticStale": bool(freshness.get("aestheticStale")),
                    "cullStale": bool(freshness.get("cullStale")),
                    "layoutStale": bool(freshness.get("layoutStale")),
                    "previewStale": bool(freshness.get("previewStale")),
                    "staleHints": freshness.get("staleHints") or [],
                    "staleHint": freshness.get("staleHint"),
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
