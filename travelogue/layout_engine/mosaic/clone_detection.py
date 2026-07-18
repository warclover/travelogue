"""Near-scene clone detection (AC-TPC-15).

Public helpers shared by the mosaic scorer (soft penalty) and the candidate
generator (hard gate). Kept in a dedicated module so ``candidates`` never has to
import scorer-private functions.
"""

from __future__ import annotations

# Temporal windows (seconds) that make a non-burst mosaic look like a sliced
# one-take / same-walk clone. Tuned against demo-2025 weighted/rail/5-main.
_SPAN_TIGHT_S = 90
_SPAN_NEAR_S = 300
_SPAN_WALK_S = 900
_SPAN_LOOSE_S = 1800

# Penalty magnitudes per window bucket (multiplicative penalty scale 0..1).
_PEN_TIGHT_MULTI_PERSON = 0.95
_PEN_TIGHT = 0.75
_PEN_NEAR_MULTI_PERSON = 0.85
_PEN_NEAR = 0.55
_PEN_WALK = 0.8
_PEN_LOOSE = 0.75

# Candidate-path hard-reject threshold (only applied when the gate is enabled).
NEAR_SCENE_CLONE_REJECT_THRESHOLD = 0.75

_MIN_ASSETS_FOR_CLONE = 3


def template_prefers_burst(pattern_id: str) -> bool | None:
    """None when LTE unavailable; True/False from compatibilityHints.prefers_burst."""
    if not pattern_id:
        return None
    # Chessboard editorial shares the same anti-clone policy as W3 weighted
    if pattern_id == "screen-editorial-4mix":
        return False
    try:
        from travelogue.layout_templates.registry import get_engine

        hints = get_engine().get(pattern_id).compatibility_hints or {}
    except (KeyError, AttributeError, TypeError):
        return None
    if "prefers_burst" not in hints:
        return None
    return bool(hints.get("prefers_burst"))


def near_scene_clone_penalty(
    pattern_id: str,
    asset_ids: list[str],
    assets_by_id: dict[str, dict],
) -> float:
    """Penalize same-scene clones on non-burst mosaics (fake「切条拼图」).

    Ingest often assigns unique burstGroupId per frame; time span still reveals
    a walking burst. Patterns with prefers_burst:false must not absorb them.
    """
    if len(asset_ids) < _MIN_ASSETS_FOR_CLONE:
        return 0.0
    prefers = template_prefers_burst(pattern_id)
    if prefers is True:
        return 0.0

    from travelogue.layout_contract.burst import parse_taken_ts
    from travelogue.layout_contract.subject import asset_has_person

    stamps = [parse_taken_ts(assets_by_id.get(aid) or {}) for aid in asset_ids]
    valid = [t for t in stamps if t is not None]
    if len(valid) < 2:
        return 0.0
    span = max(valid) - min(valid)
    person_n = sum(
        1 for aid in asset_ids if asset_has_person(assets_by_id.get(aid) or {})
    )
    # Tight temporal window → looks like sliced one take / same walk
    if span <= _SPAN_TIGHT_S:
        return _PEN_TIGHT_MULTI_PERSON if person_n >= 2 else _PEN_TIGHT
    if span <= _SPAN_NEAR_S:
        return _PEN_NEAR_MULTI_PERSON if person_n >= 3 else _PEN_NEAR
    if span <= _SPAN_WALK_S and person_n >= 3:
        return _PEN_WALK
    if prefers is False and span <= _SPAN_LOOSE_S and person_n >= len(asset_ids) - 1:
        return _PEN_LOOSE
    return 0.0
