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


def window_has_shot_groups(
    asset_ids: list[str], assets_by_id: dict[str, dict]
) -> bool:
    """True when any asset in the window carries a shotGroupId (SSG active)."""
    for aid in asset_ids:
        if (assets_by_id.get(aid) or {}).get("shotGroupId"):
            return True
    return False


def vision_is_degraded(*, app_cfg=None) -> bool:
    """True when vision is explicitly off (not auto/true)."""
    try:
        from travelogue.config import get_config
        from travelogue.config._common import normalize_tri_state

        cfg = app_cfg or get_config()
        raw = getattr(getattr(cfg, "vision", None), "enabled", "false")
        state = normalize_tri_state(raw, default="false")
        return state == "false"
    except Exception:
        return True


def effective_clone_hard_gate(
    mosaic_cfg,
    *,
    asset_ids: list[str],
    assets_map: dict[str, dict],
    app_cfg=None,
) -> bool:
    """ALG-V3 B7 · when the near-scene clone hard gate should fire.

    - Explicit ``near_scene_clone_gate.enabled`` → always on.
    - Else conditional (default): ``ssg`` absent on window (off/empty) **or**
      vision degraded → on; healthy SSG+vision → off (today's default path).
    - VC-01 slice scope is enforced by the caller via ``is_slice_pattern``.
    """
    gate = getattr(mosaic_cfg, "near_scene_clone_gate", None)
    if gate is not None and getattr(gate, "enabled", False):
        return True
    # Force-off escape for A/B: conditional=false disables auto path.
    if gate is not None and getattr(gate, "conditional", True) is False:
        return False
    if not window_has_shot_groups(asset_ids, assets_map):
        return True
    if vision_is_degraded(app_cfg=app_cfg):
        return True
    return False


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

    Prefer ``shotGroupId`` when present (SSG): same-group tight windows keep the
    anti-slice penalty; cross-group mixes rely on candidate hard-reject instead.
    Without shot groups, fall back to the legacy time heuristic.
    """
    if len(asset_ids) < _MIN_ASSETS_FOR_CLONE:
        return 0.0
    prefers = template_prefers_burst(pattern_id)
    if prefers is True:
        return 0.0

    from travelogue.layout_contract.burst import parse_taken_ts
    from travelogue.layout_contract.subject import asset_has_person
    from travelogue.layout_engine.mosaic.shot_group_gate import distinct_shot_group_ids

    group_ids = distinct_shot_group_ids(asset_ids, assets_by_id)
    # Cross-group windows: do not apply same-walk time penalty (hard-reject owns it).
    if len(group_ids) >= 2:
        return 0.0

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
