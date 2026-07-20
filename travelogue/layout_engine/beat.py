"""Narrative beat profile bias · LSE-CAP-03 (§4.5.3)."""

from __future__ import annotations

from travelogue.layout_contract.rhythm import (
    is_nine_grid_pattern,
    is_portrait_single_pattern,
)


def _is_hero_pattern(pattern_id: str) -> bool:
    pid = str(pattern_id or "")
    return "hero" in pid or "main-hero" in pid


def _is_mosaic_dense(pattern_id: str) -> bool:
    pid = str(pattern_id or "")
    return "mosaic" in pid or is_nine_grid_pattern(pid)


def beat_score_multiplier(
    pattern_id: str,
    *,
    screen_index: int,
    chapter_screen_count: int,
    beat_profile: str,
) -> float:
    """Position-aware soft boost for classic_magazine beat (non-LLM)."""
    profile = str(beat_profile or "flat").strip().lower()
    if profile in ("", "flat"):
        return 1.0
    n = max(1, chapter_screen_count)
    progress = screen_index / max(1, n - 1) if n > 1 else 0.0
    pid = str(pattern_id or "")
    if profile == "classic_magazine":
        # LTN D2 · peak band centered ~0.60–0.65 (PRD R-D2).
        if progress < 0.25 and (_is_hero_pattern(pid) or is_portrait_single_pattern(pid)):
            return 1.12
        if 0.55 <= progress <= 0.70 and _is_mosaic_dense(pid):
            return 1.12
        if 0.48 <= progress < 0.55 and _is_mosaic_dense(pid):
            return 1.06
        if 0.70 < progress <= 0.78 and _is_mosaic_dense(pid):
            return 1.06
        if progress > 0.78 and is_portrait_single_pattern(pid):
            return 1.06
    if profile == "dense_mid" and 0.55 <= progress <= 0.70 and _is_mosaic_dense(pid):
        return 1.10
    return 1.0
