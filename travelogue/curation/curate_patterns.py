"""Chapter pattern hints from bucket composition (pre-layout)."""

from __future__ import annotations

from travelogue.curation.layout_planner import AspectKind, pattern_for_chapter_index


def pattern_hint_for_bucket(
    index: int,
    total: int,
    bucket: list[str],
    aspects: dict[str, AspectKind],
) -> str:
    """Rule-based pattern before items[] are planned."""
    if index == 1:
        return "open"
    if index == total and total > 1:
        return "close"
    n = len(bucket)
    if n >= 12:
        wide = sum(
            1 for aid in bucket if aspects.get(aid) in ("panorama", "landscape")
        )
        if n and wide / n >= 0.4:
            return "gallery"
    return "moment"


def resolve_chapter_pattern(
    index: int,
    total: int,
    items: list[dict],
    *,
    hint: str | None = None,
) -> str:
    """Combine layout-derived pattern with pre-layout hint (hint may upgrade to gallery)."""
    pat = pattern_for_chapter_index(index, total, items)
    if hint == "gallery" and pat == "moment":
        return "gallery"
    if hint in ("open", "close") and index in (1, total):
        return hint
    return pat
