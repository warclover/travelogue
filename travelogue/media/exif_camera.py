"""Read camera EXIF fields for trip.json assets[].exif (Phase 23)."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Any

from PIL import Image
from PIL.ExifTags import TAGS

_APPLE_MODEL_PREFIXES = (
    "iPhone",
    "iPad",
)


def _exif_ifd(img: Image.Image) -> dict[int, Any]:
    try:
        exif = img.getexif()
        if not exif:
            return {}
        return dict(exif)
    except Exception:
        return {}


def _rational_to_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        if isinstance(value, Fraction):
            return float(value)
        if isinstance(value, tuple) and len(value) == 2:
            num, den = value
            if den:
                return float(num) / float(den)
        return float(value)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _format_shutter(value: object) -> str | None:
    f = _rational_to_float(value)
    if f is None or f <= 0:
        return None
    if f >= 1:
        return f"{f:.1f}".rstrip("0").rstrip(".")
    denom = round(1.0 / f)
    if denom > 0:
        return f"1/{denom}"
    return None


def _normalize_model(make: str | None, model: str | None) -> str | None:
    make_s = (make or "").strip()
    model_s = (model or "").strip()
    if not model_s and not make_s:
        return None
    if model_s and make_s and make_s.lower() not in model_s.lower():
        return f"{make_s} {model_s}".strip()
    return model_s or make_s


def _completeness(fields: dict[str, Any]) -> str:
    camera_keys = ("model", "aperture", "shutter", "iso", "focalLengthMm")
    present = sum(1 for k in camera_keys if fields.get(k) not in (None, "", 0))
    if present >= 4:
        return "full"
    if present >= 1:
        return "partial"
    return "none"


def read_camera_exif(path: Path, img: Image.Image | None = None) -> dict[str, Any] | None:
    """Extract structured camera EXIF; returns None when empty."""
    opened: Image.Image | None = None
    try:
        if img is None:
            opened = Image.open(path)
            img = opened
        ifd = _exif_ifd(img)
        if not ifd:
            return None

        by_name: dict[str, Any] = {}
        for tag_id, value in ifd.items():
            name = TAGS.get(tag_id)
            if name:
                by_name[name] = value

        make = str(by_name.get("Make") or "").strip() or None
        model_raw = str(by_name.get("Model") or "").strip() or None
        model = _normalize_model(make, model_raw)
        lens = str(by_name.get("LensModel") or "").strip() or None

        focal = _rational_to_float(by_name.get("FocalLength"))
        aperture = _rational_to_float(by_name.get("FNumber"))
        shutter = _format_shutter(by_name.get("ExposureTime"))
        iso_raw = by_name.get("ISOSpeedRatings") or by_name.get("PhotographicSensitivity")
        iso: int | None = None
        if iso_raw is not None:
            try:
                iso = int(iso_raw)
            except (TypeError, ValueError):
                iso = None

        altitude: float | None = None
        try:
            gps = ifd.get_ifd(0x8825) if hasattr(ifd, "get_ifd") else {}
            if gps:
                alt = gps.get(6)
                if alt is not None:
                    altitude = _rational_to_float(alt)
        except Exception:
            altitude = None

        out: dict[str, Any] = {}
        if make:
            out["make"] = make
        if model:
            out["model"] = model
        if lens:
            out["lens"] = lens
        if focal is not None:
            out["focalLengthMm"] = round(focal, 1)
        if aperture is not None:
            out["aperture"] = round(aperture, 1)
        if shutter:
            out["shutter"] = shutter
        if iso is not None:
            out["iso"] = iso
        if altitude is not None:
            out["altitudeM"] = round(altitude, 1)

        if not out:
            return None
        out["completeness"] = _completeness(out)
        return out
    finally:
        if opened is not None:
            opened.close()
