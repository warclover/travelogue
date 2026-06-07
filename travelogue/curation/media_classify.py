"""Classify assets (photo / screenshot / thumbnail / …) and date confidence."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from PIL import Image

from travelogue.curation.asset_quality import (
    is_suspected_thumbnail_asset,
    is_upscaled_thumbnail,
)

MediaClass = str  # photo | screenshot | thumbnail | reupload | archive | collage | unknown

_COLLAGE_SOFTWARE_KEYWORDS = (
    "pic collage",
    "picsart",
    "canva",
    "layout",
    "collage",
    "拼图",
    "拼贴",
    "美图秀秀",
    "inshot",
    "photo grid",
    "grid maker",
    "diptic",
    "unfold",
    "snapseed collage",
)

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

    preset = str(asset.get("mediaClass") or "")
    if preset == "collage":
        return "collage"

    if detect_collage_asset(path=path, img=img, asset=asset):
        return "collage"

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


def _exif_software_suggests_collage(img: Image.Image) -> bool:
    try:
        exif = img.getexif()
        if not exif:
            return False
        from PIL.ExifTags import Base

        software = exif.get(getattr(Base, "Software", 0x0131))
        if not software:
            return False
        text = str(software).lower()
        return any(kw in text for kw in _COLLAGE_SOFTWARE_KEYWORDS)
    except (AttributeError, OSError, TypeError, ValueError):
        return False


def _seam_grid_suggests_collage(img: Image.Image) -> bool:
    """Conservative v2: EXIF-first; seams for grid collages and 2-panel splits."""
    w, h = img.size
    if min(w, h) < 480:
        return False

    sample = img.convert("L").resize((96, 96))
    px = sample.load()
    sw, sh = sample.size

    def _band_means(axis: str) -> list[float]:
        if axis == "col":
            return [sum(px[x, y] for y in range(sh)) / sh for x in range(sw)]
        return [sum(px[x, y] for x in range(sw)) / sw for y in range(sh)]

    def _seam_positions(means: list[float], *, min_gap: int = 8) -> list[int]:
        if len(means) < 3:
            return []
        diffs = [abs(means[i + 1] - means[i]) for i in range(len(means) - 1)]
        if not diffs:
            return []
        threshold = max(8.0, sum(diffs) / len(diffs) * 2.2)
        peaks: list[int] = []
        for i, d in enumerate(diffs):
            if d < threshold:
                continue
            pos = i + 1
            if peaks and pos - peaks[-1] < min_gap:
                if d > diffs[peaks[-1] - 1]:
                    peaks[-1] = pos
                continue
            peaks.append(pos)
        return peaks

    ratio = w / h if h else 1.0
    v_seams = _seam_positions(_band_means("col"))
    h_seams = _seam_positions(_band_means("row"))

    # Two-panel landscape/portrait splits (e.g. 1600×800, 800×1600)
    if ratio >= 1.35 and len(v_seams) == 1 and w >= 640:
        return True
    if ratio <= 0.74 and len(h_seams) == 1 and h >= 640:
        return True
    # Three-column (or more) horizontal collage
    if ratio >= 1.12 and len(v_seams) >= 2 and w >= 600:
        return True

    if ratio < 0.88 or ratio > 1.18:
        return False
    if len(v_seams) < 1 or len(h_seams) < 1:
        return False
    if len(v_seams) >= 2 and len(h_seams) >= 2:
        return True
    return len(v_seams) == 1 and len(h_seams) == 1 and min(w, h) >= 720


def detect_collage_asset(
    *,
    path: Path,
    img: Image.Image,
    asset: dict | None = None,
) -> bool:
    """PRD §3.4: EXIF whitelist first; conservative seam heuristic second."""
    asset = asset or {}
    if str(asset.get("mediaClass") or "") == "collage":
        return True
    if _exif_software_suggests_collage(img):
        return True
    return _seam_grid_suggests_collage(img)


def is_collage_asset(asset: dict | None) -> bool:
    """True when asset is tagged collage (PRD §3.4 · AC-P16-18)."""
    return str((asset or {}).get("mediaClass") or "") == "collage"


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
