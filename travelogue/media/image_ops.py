"""EXIF-aware load, center crop, and WebP variants for trip assets."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Literal

from PIL import Image, ImageOps

from travelogue.layout_contract.orientations import (
    AspectKind,
    classify_aspect,
)

Orientation = Literal["portrait", "landscape", "square"]

PORTRAIT_ASPECT = 9 / 16  # width / height
LANDSCAPE_ASPECT = 16 / 9
PANORAMA_ASPECT = 2 / 1  # 全景条 · 21:9≈2.33 归入 panorama
SQUARE_ASPECT = 1.0

# EXIF Orientation tag
_EXIF_ORIENTATION = 274
_EXIF_DATETIME_ORIGINAL = 36867
_EXIF_DATETIME = 306
_EXIF_DATETIME_DIGITIZED = 36868

_FILENAME_DATE_PATTERNS = (
    re.compile(r"(20\d{2})[-_]?(0[1-9]|1[0-2])[-_]?(0[1-9]|[12]\d|3[01])"),
    re.compile(r"(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])"),
    re.compile(r"IMG[_-]?(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])", re.I),
)


@dataclass
class GeoCoords:
    lat: float
    lon: float


@dataclass
class ImageLoadResult:
    image: Image.Image
    taken_at: datetime
    date_source: str  # exif | filename | mtime
    had_exif_orientation: bool
    orientation_tag: int | None
    geo: GeoCoords | None = None


from travelogue.errors import PlainCodeError


class ImageOpsError(PlainCodeError):
    def __init__(self, message: str, *, code: str = "E_IMAGE_OPS") -> None:
        super().__init__(message, code=code)


def _parse_exif_datetime(raw: object) -> datetime | None:
    if not raw:
        return None
    text = str(raw).strip()
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def parse_datetime_from_filename(path: Path) -> datetime | None:
    """Guess capture time from common filename patterns (web downloads)."""
    name = path.stem
    for pat in _FILENAME_DATE_PATTERNS:
        m = pat.search(name)
        if not m:
            continue
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return datetime(y, mo, d, 12, 0, 0)
        except ValueError:
            continue
    return None


def _rational_to_float(value: object) -> float:
    if isinstance(value, tuple) and len(value) == 2:
        num, den = value
        if den:
            return float(num) / float(den)
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def _gps_coord(values: object, ref: str) -> float | None:
    if not isinstance(values, (list, tuple)) or len(values) != 3:
        return None
    deg = _rational_to_float(values[0])
    minutes = _rational_to_float(values[1])
    seconds = _rational_to_float(values[2])
    coord = deg + minutes / 60.0 + seconds / 3600.0
    if ref in ("S", "W"):
        coord = -coord
    return coord


def read_exif_gps(img: Image.Image) -> GeoCoords | None:
    """Read latitude/longitude from EXIF GPS IFD when present."""
    try:
        exif = img.getexif()
        if not exif:
            return None
        gps = exif.get_ifd(0x8825)
        if not gps:
            return None
        lat_vals = gps.get(2)
        lat_ref = gps.get(1)
        lon_vals = gps.get(4)
        lon_ref = gps.get(3)
        if lat_vals is None or lon_vals is None:
            return None
        lat = _gps_coord(lat_vals, str(lat_ref or "N"))
        lon = _gps_coord(lon_vals, str(lon_ref or "E"))
        if lat is None or lon is None:
            return None
        if abs(lat) > 90 or abs(lon) > 180:
            return None
        return GeoCoords(lat=lat, lon=lon)
    except Exception:
        return None


def read_exif_orientation(img: Image.Image) -> int | None:
    try:
        exif = img.getexif()
        if not exif:
            return None
        ori = exif.get(_EXIF_ORIENTATION)
        return int(ori) if ori is not None else None
    except Exception:
        return None


def resolve_photo_datetime(path: Path, img: Image.Image) -> tuple[datetime, str]:
    """
    Priority: EXIF DateTimeOriginal → EXIF DateTime → filename → file mtime.
    """
    try:
        exif = img.getexif()
        if exif:
            for tag in (_EXIF_DATETIME_ORIGINAL, _EXIF_DATETIME_DIGITIZED, _EXIF_DATETIME):
                parsed = _parse_exif_datetime(exif.get(tag))
                if parsed:
                    return parsed, "exif"
    except Exception:
        pass

    from_name = parse_datetime_from_filename(path)
    if from_name:
        return from_name, "filename"

    return datetime.fromtimestamp(path.stat().st_mtime), "mtime"


def load_image_normalized(path: Path) -> ImageLoadResult:
    """
    Open image, apply EXIF transpose (rotation), return RGB image + metadata.
    Saved exports should use this result (pixels already upright).
    """
    img = Image.open(path)
    ori_tag = read_exif_orientation(img)
    had_ori = ori_tag is not None and ori_tag != 1
    geo = read_exif_gps(img)
    taken_at, date_source = resolve_photo_datetime(path, img)
    img = ImageOps.exif_transpose(img)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    return ImageLoadResult(
        image=img,
        taken_at=taken_at,
        date_source=date_source,
        had_exif_orientation=had_ori,
        orientation_tag=ori_tag,
        geo=geo,
    )


def load_normalized_image(path: Path) -> Image.Image:
    """Backward-compatible: return transposed RGB image only."""
    return load_image_normalized(path).image


def detect_orientation(width: int, height: int) -> Orientation:
    """Legacy 3-way bucket; prefer classify_aspect for layout."""
    kind = classify_aspect(width, height)
    if kind in ("panorama", "landscape"):
        return "landscape"
    if kind in ("tall", "portrait"):
        return "portrait"
    return "square"


def aspect_ratio(width: int, height: int) -> float:
    if height <= 0:
        return 1.0
    return width / height


def center_crop_aspect(img: Image.Image, aspect: float) -> Image.Image:
    """Center crop to width/height = aspect (e.g. 9/16)."""
    return crop_aspect_focal(img, aspect, focal=(0.5, 0.5))


def crop_aspect_focal(
    img: Image.Image,
    aspect: float,
    *,
    focal: tuple[float, float] = (0.5, 0.45),
) -> Image.Image:
    """Crop to aspect ratio with focal point (x,y in 0..1)."""
    w, h = img.size
    fx = min(1.0, max(0.0, focal[0]))
    fy = min(1.0, max(0.0, focal[1]))
    current = w / h
    if current > aspect:
        crop_w = max(1, int(round(h * aspect)))
        crop_h = h
    else:
        crop_w = w
        crop_h = max(1, int(round(w / aspect)))
    cx = int(fx * w)
    cy = int(fy * h)
    left = max(0, min(w - crop_w, cx - crop_w // 2))
    top = max(0, min(h - crop_h, cy - crop_h // 2))
    return img.crop((left, top, left + crop_w, top + crop_h))


def focal_from_asset(asset: dict) -> tuple[float, float]:
    fp = asset.get("focalPoint") or {}
    return (float(fp.get("x", 0.5)), float(fp.get("y", 0.45)))


def resize_to_width(img: Image.Image, width: int) -> Image.Image:
    if img.width == width:
        return img
    height = max(1, int(round(img.height * width / img.width)))
    return img.resize((width, height), Image.Resampling.LANCZOS)


def crop_for_aspect_kind(
    img: Image.Image,
    kind: AspectKind,
    *,
    slot: str = "media",
    focal: tuple[float, float] | None = None,
) -> Image.Image:
    """Focal-aware crop for display slot; preserves intent of panorama/square/tall."""
    fp = focal or (0.5, 0.45)
    if slot in ("cover", "scroll"):
        return crop_aspect_focal(img, PORTRAIT_ASPECT, focal=fp)
    if kind == "panorama":
        return crop_aspect_focal(img, PANORAMA_ASPECT, focal=fp)
    if kind == "square":
        return crop_aspect_focal(img, SQUARE_ASPECT, focal=fp)
    if kind == "tall":
        return crop_aspect_focal(img, PORTRAIT_ASPECT, focal=fp)
    if kind == "landscape":
        return crop_aspect_focal(img, LANDSCAPE_ASPECT, focal=fp)
    return crop_aspect_focal(img, PORTRAIT_ASPECT, focal=fp)


def crop_for_slot(img: Image.Image, orientation: Orientation, *, slot: str = "media") -> Image.Image:
    """Backward-compatible wrapper."""
    kind: AspectKind
    if orientation == "landscape":
        kind = "landscape"
    elif orientation == "portrait":
        kind = "portrait"
    else:
        kind = "square"
    return crop_for_aspect_kind(img, kind, slot=slot)


def save_jpeg_without_exif(img: Image.Image, path: Path, *, quality: int = 92) -> None:
    """Archive normalized pixels; strip EXIF so viewers don't double-rotate."""
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "JPEG", quality=quality, optimize=True, exif=b"")


def export_layout_crops(
    img: Image.Image,
    assets_dir: Path,
    asset_id: str,
    *,
    quality: int = 82,
    webp_method: int = 4,
    focal: tuple[float, float] = (0.5, 0.45),
    max_width: int = 1600,
) -> tuple[str, str]:
    """Write 9:16 (-m) and 16:9 (-w) profile crops; return relative paths."""
    assets_dir.mkdir(parents=True, exist_ok=True)
    method = max(0, min(6, int(webp_method)))
    mobile = crop_aspect_focal(img, PORTRAIT_ASPECT, focal=focal)
    web = crop_aspect_focal(img, LANDSCAPE_ASPECT, focal=focal)
    mobile = resize_to_width(mobile, max_width)
    web = resize_to_width(web, max_width)
    rel_m = f"assets/{asset_id}-m.webp"
    rel_w = f"assets/{asset_id}-w.webp"
    mobile.save(assets_dir / f"{asset_id}-m.webp", "WEBP", quality=quality, method=method)
    web.save(assets_dir / f"{asset_id}-w.webp", "WEBP", quality=quality, method=method)
    return rel_m, rel_w


def export_webp_variants(
    img: Image.Image,
    assets_dir: Path,
    asset_id: str,
    *,
    widths: tuple[int, ...] = (800, 1600),
    quality: int = 82,
    webp_method: int = 4,
    generate_crops: bool = False,
    focal: tuple[float, float] = (0.5, 0.45),
) -> tuple[str, list[dict], int, int, str | None, str | None]:
    assets_dir.mkdir(parents=True, exist_ok=True)
    method = max(0, min(6, int(webp_method)))
    srcset: list[dict] = []
    largest = img

    for w in sorted(widths):
        variant = resize_to_width(img, w)
        rel = f"assets/{asset_id}-w{w}.webp"
        out = assets_dir / f"{asset_id}-w{w}.webp"
        variant.save(out, "WEBP", quality=quality, method=method)
        srcset.append({"file": rel, "width": w})
        if w == max(widths):
            largest = variant

    display = f"assets/{asset_id}-w{max(widths)}.webp"
    crop_m: str | None = None
    crop_w: str | None = None
    if generate_crops:
        max_w = max(widths)
        crop_m, crop_w = export_layout_crops(
            img, assets_dir, asset_id, quality=quality, focal=focal, max_width=max_w, webp_method=method
        )
    return display, srcset, largest.width, largest.height, crop_m, crop_w


def filter_trip_dates(
    dates: list[date],
    *,
    sources: list[str] | None = None,
) -> list[date]:
    """
    Drop outliers (e.g. one 2005 EXIF among 2024 photos).
    Prefer exif/filename dates when most photos lack trustworthy EXIF.
    """
    if len(dates) <= 2:
        return dates

    if sources and sum(1 for s in sources if s == "mtime") > len(sources) * 0.6:
        trusted = [d for d, s in zip(dates, sources) if s in ("exif", "filename")]
        if len(trusted) >= 2:
            dates = trusted

    ordinals = sorted(d.toordinal() for d in dates)
    mid = ordinals[len(ordinals) // 2]
    return [d for d in dates if abs(d.toordinal() - mid) <= 400]


def min_dimension_ok(img: Image.Image, min_px: int = 320) -> bool:
    return min(img.size) >= min_px
