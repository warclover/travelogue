"""Format one-line EXIF footnote for moment-screen (Phase 23)."""

from __future__ import annotations

from datetime import datetime


def _month_label(taken_at: str | None) -> str | None:
    if not taken_at:
        return None
    try:
        dt = datetime.fromisoformat(str(taken_at).replace("Z", "+00:00"))
        return f"{dt.year}.{dt.month:02d}"
    except ValueError:
        return None


def _daypart_label(taken_at: str | None) -> str | None:
    if not taken_at:
        return None
    try:
        dt = datetime.fromisoformat(str(taken_at).replace("Z", "+00:00"))
        hour = dt.hour
        if 5 <= hour < 9:
            return "清晨"
        if 9 <= hour < 12:
            return "上午"
        if 12 <= hour < 14:
            return "正午"
        if 14 <= hour < 17:
            return "下午"
        if 17 <= hour < 20:
            return "黄昏"
        return "夜晚"
    except ValueError:
        return None


def _place_label(asset: dict) -> str | None:
    place = asset.get("place")
    if isinstance(place, dict):
        city = str(place.get("city") or "").strip()
        if city:
            return city
    for key in ("location", "city", "placeName"):
        val = asset.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def format_moment_exif_line(asset: dict) -> str | None:
    """Build footnote segments; returns None when fewer than 2 valid parts."""
    segments: list[str] = []

    place = _place_label(asset)
    if place:
        segments.append(place)

    month = _month_label(str(asset.get("takenAt") or "") or None)
    if month:
        segments.append(month)

    daypart = _daypart_label(str(asset.get("takenAt") or "") or None)
    if daypart:
        segments.append(daypart)

    # BE-FST-04 / D-FST-07 · 读者面禁止相机 Make/Model 与曝光串
    _ = asset.get("exif")

    if len(segments) < 2:
        if place and len(segments) == 1:
            return place
        return None
    return " · ".join(segments)
