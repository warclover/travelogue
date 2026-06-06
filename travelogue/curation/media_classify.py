"""Classify assets (photo / screenshot / thumbnail / …) and date confidence."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from PIL import Image

from travelogue.curation.asset_quality import (
    is_suspected_thumbnail_asset,
    is_upscaled_thumbnail,
)

MediaClass = str  # photo | screenshot | thumbnail | reupload | archive | unknown

_COVER_CLASS_WEIGHT: dict[str, float] = {
    "photo": 1.0,
    "unknown": 0.85,
    "archive": 0.15,
    "screenshot": 0.12,
    "thumbnail": 0.0,
    "reupload": 0.0,
}


def date_confidence_for_source(source: str) -> str:
    if source in ("exif", "filename"):
        return "high"
    return "low"


def classify_media_class(
    *,
    path: Path,
    img: Image.Image,
    date_source: str,
    asset: dict | None = None,
) -> MediaClass:
    """Heuristic media type at ingest (no ML)."""
    asset = asset or {}
    nw = int(asset.get("nativeWidth") or img.width)
    nh = int(asset.get("nativeHeight") or img.height)
    if nw <= 0 or nh <= 0:
        return "unknown"

    # Classify from source pixels only — ingest may set width/height to the largest
    # responsive WebP variant, which upscales small sources for srcset (not reupload).
    native_probe = {
        "id": "x",
        "type": "image",
        "nativeWidth": nw,
        "nativeHeight": nh,
        "width": nw,
        "height": nh,
    }
    if is_suspected_thumbnail_asset(native_probe):
        return "thumbnail"
    if is_upscaled_thumbnail(native_probe):
        return "reupload"

    ratio = nw / nh if nh else 1.0
    ext = path.suffix.lower()
    no_exif = date_source == "mtime"
    if no_exif and (ratio >= 2.4 or ratio <= 0.42) and max(nw, nh) >= 720:
        return "screenshot"
    if no_exif and ext == ".png" and min(nw, nh) >= 400:
        return "screenshot"

    return "photo"


def refine_archive_media_class(assets: list[dict]) -> None:
    """Mark low-confidence photos far from the main date cluster as archive."""
    dated: list[tuple[date, str]] = []
    for a in assets:
        if a.get("mediaClass") not in ("photo", "unknown"):
            continue
        if a.get("dateConfidence") != "high":
            continue
        d = _parse_date(a.get("takenAt"))
        if d:
            dated.append((d, a["id"]))

    if len(dated) < 3:
        return

    ordinals = sorted(d.toordinal() for d, _ in dated)
    mid = ordinals[len(ordinals) // 2]
    median_year = date.fromordinal(mid).year

    for a in assets:
        if a.get("mediaClass") not in ("photo", "unknown"):
            continue
        if a.get("dateConfidence") == "high":
            continue
        d = _parse_date(a.get("takenAt"))
        if not d:
            continue
        if d.year < median_year - 1:
            a["mediaClass"] = "archive"


def cover_class_weight(media_class: str | None) -> float:
    return _COVER_CLASS_WEIGHT.get(media_class or "unknown", 0.85)


def summarize_media_classes(assets: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for a in assets:
        key = a.get("mediaClass") or "unknown"
        counts[key] = counts.get(key, 0) + 1
    return counts


def _parse_date(raw: object) -> date | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).date()
    except ValueError:
        return None
