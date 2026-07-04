"""Unified screen density classification (PRD §3.7)."""

from __future__ import annotations

from typing import Literal

from travelogue.curation.screen_layout_state import is_dense_collage_pattern

ScreenDensity = Literal["airy", "balanced", "dense"]

_AIRY_PATTERNS: frozenset[str] = frozenset(
    {
        "screen-landscape-1",
        "screen-portrait-1",
        "screen-portrait-2",
        "screen-landscape-2",
    }
)

_DENSE_PREFIXES: tuple[str, ...] = (
    "screen-mosaic-5-main-hero-",
    "screen-mosaic-6-main-hero-",
    "screen-mosaic-5-hero-",
    "screen-mosaic-5-main-",
)


def classify_screen_density(pattern_id: str) -> ScreenDensity:
    pid = str(pattern_id or "").strip()
    if not pid:
        return "balanced"
    if pid in _AIRY_PATTERNS or pid.startswith("screen-editorial-"):
        return "airy"
    if is_dense_collage_pattern(pid):
        return "dense"
    if pid.endswith("-9") or pid.endswith("-6"):
        return "dense"
    for prefix in _DENSE_PREFIXES:
        if pid.startswith(prefix):
            return "dense"
    return "balanced"
