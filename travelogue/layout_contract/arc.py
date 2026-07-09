"""Narrative arc scoring helpers (layout kernel)."""

from __future__ import annotations

ARC_OPEN = "open"
ARC_RISE = "rise"
ARC_PEAK = "peak"
ARC_FALL = "fall"
ARC_CLOSE = "close"
ARC_MOMENT = "moment"

ArcProfile = str  # flat | moderate | dynamic

_PEAK_PATTERNS = frozenset(
    {
        "screen-mosaic-5-main-portrait-3land",
        "screen-mosaic-5-main-landscape-2portrait-2land",
        "screen-mosaic-5-2portrait-3land-balanced",
        "screen-mosaic-5-3portrait-2land-balanced",
        "screen-mosaic-5-main-hero-plus-4",
        "screen-mosaic-6-main-hero-plus-5",
        "screen-portrait-grid-8",
        "screen-landscape-4",
    }
)

_ARC_PATTERN_PREFERENCES: dict[str, frozenset[str]] = {
    ARC_OPEN: frozenset(
        {
            "screen-portrait-1",
            "screen-landscape-1",
            "screen-portrait-3",
        }
    ),
    ARC_RISE: frozenset(
        {
            "screen-portrait-3",
            "screen-landscape-2",
            "screen-landscape-3",
        }
    ),
    ARC_PEAK: frozenset(_PEAK_PATTERNS),
    ARC_FALL: frozenset(
        {
            "screen-landscape-2",
            "screen-portrait-2",
            "screen-portrait-1-landscape-2",
        }
    ),
    ARC_CLOSE: frozenset(
        {
            "screen-portrait-1",
            "screen-landscape-1",
            "screen-portrait-2",
        }
    ),
    ARC_MOMENT: frozenset(
        {
            "screen-portrait-2",
            "screen-landscape-2",
            "screen-portrait-3",
            "screen-landscape-1",
        }
    ),
}


def arc_pattern_bonus(
    pattern_id: str,
    arc_segment: str,
    *,
    profile: ArcProfile = "dynamic",
) -> float:
    if profile == "flat" and pattern_id in _PEAK_PATTERNS:
        return 0.5
    prefs = _ARC_PATTERN_PREFERENCES.get(arc_segment)
    if not prefs:
        return 0.5
    if pattern_id in prefs:
        return 1.0
    return 0.3
