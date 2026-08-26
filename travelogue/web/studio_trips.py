"""List trips for Studio workbench."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


_LONGSHOT_FILE_PATTERNS: tuple[str, ...] = (
    # SFI D-SFI-07 · 人话展示名产物
    "*-长图.png",
    "*-长图.jpg",
    "*-长图.jpeg",
    "*-长图-*.png",
    "*-长图-*.jpg",
    "*-长图-*.jpeg",
    # 兼容旧 tripId / -longshot / -chNN 命名（迁移期；新导出后会清理）
    "*-longshot.png",
    "*-longshot.jpg",
    "*-longshot.jpeg",
    "*-ch*.png",
    "*-ch*.jpg",
    "*-ch*.jpeg",
    # Longshot 2.0 platform outputs (ADR-016 D7 / AC-LNG2-06)
    "*-moments-*.png",
    "*-moments-*.jpg",
    "*-moments-*.jpeg",
    "*-xhs-*.png",
    "*-xhs-*.jpg",
    "*-xhs-*.jpeg",
    "*-ins-*.png",
    "*-ins-*.jpg",
    "*-weibo-*.png",
    "*-weibo-*.jpg",
    "*-douyin-cover.png",
    "*-douyin-cover.jpg",
    "*-custom-*.png",
    "*-custom-*.jpg",
    "*-poster*.png",
    "*-poster*.jpg",
)


def _export_search_dirs(trip_dir: Path) -> list[Path]:
    """EOI · 新导出统一落在 EXPORT_OUTPUT_DIRNAME 子目录；trip_dir 根目录仍一并扫描，
    兼容本次改动前已导出、未迁移的老游记（D-EOI-05 · 不迁移不清理）。"""
    from travelogue.export.longshot import EXPORT_OUTPUT_DIRNAME

    export_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    return [trip_dir, export_dir] if export_dir.is_dir() else [trip_dir]


def _longshot_files(trip_dir: Path) -> list[Path]:
    files: list[Path] = []
    for base in _export_search_dirs(trip_dir):
        for pattern in _LONGSHOT_FILE_PATTERNS:
            files.extend(base.glob(pattern))
    # Drop atomic temp leftovers if any
    return [p for p in files if not p.name.endswith(".part")]


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
    """Return cover: preview.jpg → 长图/ch01 → longshot (png/jpg)."""
    primary = trip_dir / "preview.jpg"
    if primary.is_file():
        return "preview.jpg"

    def _glob(*patterns: str) -> list[Path]:
        rows: list[Path] = []
        for base in _export_search_dirs(trip_dir):
            for pattern in patterns:
                rows.extend(base.glob(pattern))
        return rows

    # Prefer new SFI names, then legacy
    preferred = sorted(
        _glob(
            "*-长图-01.png",
            "*-长图-01.jpg",
            "*-长图.png",
            "*-长图.jpg",
            "*-ch01.png",
            "*-ch01.jpg",
            "*-ch01.jpeg",
        )
    )
    if preferred:
        return preferred[0].relative_to(trip_dir).as_posix()
    longshots = sorted(_glob("*-longshot.png", "*-longshot.jpg", "*-longshot.jpeg"))
    if longshots:
        return longshots[0].relative_to(trip_dir).as_posix()
    any_ch = sorted(
        _glob(
            "*-长图-*.png",
            "*-长图-*.jpg",
            "*-ch*.png",
            "*-ch*.jpg",
            "*-ch*.jpeg",
        )
    )
    if any_ch:
        return any_ch[0].relative_to(trip_dir).as_posix()
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


def longshot_reveal_rel_path(trip_dir: Path) -> str | None:
    """Prefer ``longshot-current.json`` first file; else newest matching export."""
    from travelogue.export.longshot import EXPORT_OUTPUT_DIRNAME, read_longshot_current

    current = read_longshot_current(trip_dir)
    if current:
        files = list(current.get("files") or [])
        if files:
            # 清单文件里存的是"与清单同层"的裸文件名（现指子目录内），补回子目录前缀
            # 才是相对 trip_dir 的正确 relPath（供前端直传 /__travelogue/reveal）。
            return (Path(EXPORT_OUTPUT_DIRNAME) / str(files[0])).as_posix()
    matches = _longshot_files(trip_dir)
    if not matches:
        return None
    newest = max(matches, key=lambda p: (p.stat().st_mtime, p.name))
    return newest.relative_to(trip_dir).as_posix()


def _shelf_edition_fields(data: dict) -> dict:
    """PIS · 游记行带 edition=journal；作品集带 edition + pageCount。"""
    if not data:
        return {"edition": "journal"}
    from travelogue.web.studio_entry import edition_chrome

    chrome = edition_chrome(data)
    if chrome.get("edition") != "portfolio":
        return {"edition": "journal"}
    out: dict = {"edition": "portfolio"}
    folio = chrome.get("portfolio") if isinstance(chrome.get("portfolio"), dict) else {}
    try:
        page_count = int(folio.get("pageCount"))
    except (TypeError, ValueError):
        page_count = 0
    if page_count > 0:
        out["pageCount"] = page_count
    if chrome.get("overflowLine"):
        out["overflowLine"] = chrome["overflowLine"]
    return out


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
            from travelogue.domain.title_humanize import resolve_display_title

            meta = data.get("meta") or {}
            # BE-FST-06 / USR-04 · 书架主标题与封面 / FirstSuccess 同源展示名
            title = resolve_display_title(meta) or title
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
        render_bundle_stale = False
        if data:
            from travelogue.layout_templates.css_stale import (
                trip_layout_css_stale,
                trip_render_bundle_stale,
            )

            layout_css_stale = trip_layout_css_stale(child, data)
            render_bundle_stale = trip_render_bundle_stale(child, data)
        rows.append(
            (
                updated_at,
                {
                    "tripId": child.name,
                    "title": title,
                    "previewUrl": f"/{child.name}/index.html",
                    "updatedAt": updated_at,
                    "photoCount": photo_count,
                    **_shelf_edition_fields(data),
                    "longshotStale": longshot_outputs_stale(child, trip_mtime=updated_at),
                    "layoutCssStale": layout_css_stale,
                    "renderBundleStale": render_bundle_stale,
                    "hasLongshotExport": has_longshot_exports(child),
                    "longshotRevealRelPath": longshot_reveal_rel_path(child),
                    "previewRelPath": preview_rel,
                    "shelfCoverRelPath": shelf_cover_rel,
                    "derivativesStatus": str(
                        (data.get("pipeline") or {}).get("derivativesStatus") or ""
                    )
                    or None,
                    "derivativesReady": (
                        ((data.get("pipeline") or {}).get("derivativesStatus") == "ready")
                        if data
                        else False
                    ),
                    "derivativesPreparing": int(
                        ((data.get("pipeline") or {}).get("derivativesPreparing") or 0)
                        if data
                        else 0
                    ),
                    "g1Pending": (
                        ((data.get("pipeline") or {}).get("status") == "structure_draft")
                        if data
                        else False
                    ),
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
    rows, _total = list_studio_trips_page(trips_dir, limit=limit, offset=offset)
    return rows


def list_studio_trips_page(
    trips_dir: Path,
    *,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Return ``(page_rows, total)`` from a single directory scan."""
    rows = _trip_rows(trips_dir)
    return [row[1] for row in rows[offset : offset + limit]], len(rows)


def studio_trips_total(trips_dir: Path) -> int:
    return len(_trip_rows(trips_dir))
