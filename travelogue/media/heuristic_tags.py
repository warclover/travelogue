"""Rule-based semantic tags at ingest (no cloud vision)."""

from __future__ import annotations

from datetime import datetime

from travelogue.media.image_ops import AspectKind

_ASPECT_TAGS: dict[str, str] = {
    "panorama": "全景",
    "tall": "竖长图",
    "landscape": "横图",
    "portrait": "竖图",
    "square": "方图",
}


def time_of_day_tag(taken_at: datetime) -> str | None:
    hour = taken_at.hour
    if 5 <= hour < 9:
        return "早晨"
    if 9 <= hour < 17:
        return "白天"
    if 17 <= hour < 20:
        return "傍晚"
    if 20 <= hour or hour < 5:
        return "夜景"
    return None


def aspect_tag(aspect_kind: AspectKind | str) -> str | None:
    return _ASPECT_TAGS.get(str(aspect_kind))


def merge_tags(*groups: tuple[str, ...] | list[str], max_tags: int = 5) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for group in groups:
        for tag in group:
            t = tag.strip()
            if not t or t in seen:
                continue
            seen.add(t)
            out.append(t[:32])
            if len(out) >= max_tags:
                return out
    return out


def build_heuristic_tags(
    *,
    taken_at: datetime,
    aspect_kind: AspectKind | str,
    subject_tags: tuple[str, ...] | list[str] = (),
    place_city: str | None = None,
    max_tags: int = 5,
) -> list[str]:
    optional: list[str] = []
    tod = time_of_day_tag(taken_at)
    if tod:
        optional.append(tod)
    asp = aspect_tag(aspect_kind)
    if asp:
        optional.append(asp)
    if place_city and place_city not in ("未知", "旅途"):
        optional.append(place_city)
    return merge_tags(subject_tags, optional, max_tags=max_tags)
