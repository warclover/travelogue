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
    "picsart photo",
    "canva",
    "layout",
    "collage",
    "拼图",
    "拼贴",
    "拼好照",
    "美图秀秀",
    "醒图",
    "剪映",
    "capcut",
    "黄油相机",
    "一甜相机",
    "轻颜",
    "inshot",
    "photo grid",
    "grid maker",
    "diptic",
    "unfold",
    "snapseed collage",
    "google photos",
    "天天拼图",
    "百度贴贴",
    "九宫格",
    "长图拼接",
)

_COLLAGE_FILENAME_KEYWORDS = (
    "collage",
    "pintu",
    "pin_tu",
    "拼图",
    "拼贴",
    "grid",
    "九宫格",
    "长图",
    "jigsaw",
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

    preset = str(asset.get("mediaClass") or "")
    if preset == "collage":
        return "collage"

    # Collage before screenshot: wide multi-panel collages often exceed 2.4 AR.
    if detect_collage_asset(path=path, img=img, asset=asset):
        return "collage"
    if _path_suggests_collage(path):
        return "collage"

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


def _path_suggests_collage(path: Path) -> bool:
    stem = path.stem.lower().replace("-", "_").replace(" ", "_")
    return any(kw in stem for kw in _COLLAGE_FILENAME_KEYWORDS)


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


def _seam_near_fraction(pos: int, span: int, target: float, *, tol: float = 0.12) -> bool:
    if span <= 0:
        return False
    return abs(pos / span - target) <= tol


def _has_center_panel_seam(seams: list[int], span: int) -> bool:
    """Single gutter near 50% (2-panel split)."""
    return len(seams) == 1 and _seam_near_fraction(seams[0], span, 0.5)


def _has_three_column_seams(seams: list[int], span: int) -> bool:
    """Exactly two gutters near ⅓ and ⅔ (3-panel horizontal split)."""
    if len(seams) != 2 or span <= 0:
        return False
    a, b = sorted(s / span for s in seams)
    return abs(a - 1 / 3) <= 0.10 and abs(b - 2 / 3) <= 0.10


def _seam_grid_suggests_collage(img: Image.Image) -> bool:
    """Conservative v3: seams must align with collage grid gutters, not scene edges."""
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
    if ratio >= 1.35 and w >= 640 and _has_center_panel_seam(v_seams, sw):
        return True
    if ratio <= 0.74 and h >= 640 and _has_center_panel_seam(h_seams, sh):
        return True
    # Three-column horizontal collage
    if ratio >= 1.12 and w >= 600 and _has_three_column_seams(v_seams, sw):
        return True

    # Near-square 2×2 grid
    if 0.88 <= ratio <= 1.18 and min(w, h) >= 720:
        return _has_center_panel_seam(v_seams, sw) and _has_center_panel_seam(h_seams, sh)
    return False


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
    if _path_suggests_collage(path):
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
