"""SSG mosaic hard-reject helpers · PRD D-SSG-05/17b/21/22."""

from __future__ import annotations

from typing import Any

from travelogue.layout_engine.mosaic.clone_detection import template_prefers_burst

# Align with clone_detection tight window (假切条 / same-walk).
_SAME_GROUP_ANTI_SLICE_SPAN_S = 90.0

# Pattern-prefix equivalents when full screen ctx is unavailable (SUP-01).
_EXEMPT_PATTERN_PREFIXES = (
    "screen-full-frame",
    "screen-bookend",
    "bookend-",
    "screen-opening",
    "screen-closing",
)


def is_slice_pattern(pattern_id: str) -> bool:
    """D-SSG-21 · slice scope == prefers_burst is not True."""
    return template_prefers_burst(pattern_id) is not True


def pattern_exempt_from_cross_group_reject(pattern_id: str) -> bool:
    """Solo/bookend-like patterns never take multi-group slice hard-reject."""
    if not pattern_id:
        return False
    pid = pattern_id.lower()
    return any(pid.startswith(p) for p in _EXEMPT_PATTERN_PREFIXES)


def screen_exempt_from_shot_group_hard_reject(
    *,
    pattern_id: str | None = None,
    slot_count: int | None = None,
    screen_kind: str | None = None,
    purpose: str | None = None,
) -> bool:
    """D-SSG-17b · screen-level exempt (NOT LTE slot.role)."""
    kind = (screen_kind or "").lower()
    purp = (purpose or "").lower()
    if kind in ("cover", "opening", "moment", "bookend", "closing") or purp in (
        "cover",
        "moment",
        "solo",
        "bookend",
        "chapter_hero",
        "chapterhero",
    ):
        return True
    if slot_count is not None and slot_count <= 1:
        return True
    if pattern_id and pattern_exempt_from_cross_group_reject(pattern_id):
        return True
    return False


def distinct_shot_group_ids(
    asset_ids: list[str], assets_by_id: dict[str, dict]
) -> set[str]:
    out: set[str] = set()
    for aid in asset_ids:
        gid = (assets_by_id.get(aid) or {}).get("shotGroupId")
        if gid:
            out.add(str(gid))
    return out


def hard_reject_cross_shot_group(
    pattern_id: str,
    asset_ids: list[str],
    assets_by_id: dict[str, dict],
    *,
    slice_cross_group_hard_reject: bool = True,
    exempt: bool | None = None,
) -> bool:
    """True when candidate window must be rejected for cross-shotGroup mix."""
    if not slice_cross_group_hard_reject:
        return False
    if len(asset_ids) < 2:
        return False
    if exempt is None:
        exempt = screen_exempt_from_shot_group_hard_reject(pattern_id=pattern_id)
    if exempt:
        return False
    if not is_slice_pattern(pattern_id):
        return False
    return len(distinct_shot_group_ids(asset_ids, assets_by_id)) >= 2


def hard_reject_same_shot_group_anti_slice(
    pattern_id: str,
    asset_ids: list[str],
    assets_by_id: dict[str, dict],
    *,
    same_group_anti_slice: bool = True,
    span_tight_s: float = _SAME_GROUP_ANTI_SLICE_SPAN_S,
    exempt: bool | None = None,
) -> bool:
    """D-SSG-05 · same-group tight window on slice pattern = 假切条 → hard reject."""
    if not same_group_anti_slice:
        return False
    if len(asset_ids) < 3:
        return False
    if exempt is None:
        exempt = screen_exempt_from_shot_group_hard_reject(pattern_id=pattern_id)
    if exempt:
        return False
    if not is_slice_pattern(pattern_id):
        return False
    gids = distinct_shot_group_ids(asset_ids, assets_by_id)
    if len(gids) != 1:
        return False
    if not all((assets_by_id.get(aid) or {}).get("shotGroupId") for aid in asset_ids):
        return False
    from travelogue.layout_contract.burst import parse_taken_ts

    stamps = [parse_taken_ts(assets_by_id.get(aid) or {}) for aid in asset_ids]
    valid = [t for t in stamps if t is not None]
    if len(valid) < 2:
        return False
    return (max(valid) - min(valid)) <= float(span_tight_s)


def ssg_hard_reject_active(cfg: Any) -> bool:
    """D-SSG-22 · cross-shotGroup hard-reject follows shotGrouping.mosaic knobs.

    Independent of ``near_scene_clone_gate.enabled`` (which still gates the
    legacy time-heuristic hard reject).

    Prefer :func:`resolve_shot_group_mosaic_policy` + explicit policy in
    candidates (PLAN P0). Passing ``MosaicConfig`` here returns False.
    """
    from travelogue.config.shot_grouping import ShotGroupMosaicPolicy

    if isinstance(cfg, ShotGroupMosaicPolicy):
        return bool(cfg.cross_group_hard_reject or cfg.same_group_anti_slice)
    ssg = getattr(cfg, "shot_grouping", None)
    if ssg is None:
        return False
    if getattr(ssg, "enabled", "auto") == "false":
        return False
    mosaic = getattr(ssg, "mosaic", None)
    if mosaic is None:
        return True
    cross = getattr(mosaic, "slice_cross_group_hard_reject", True)
    same = getattr(mosaic, "same_group_anti_slice", True)
    return bool(cross or same)


def ssg_same_group_anti_slice_active(cfg: Any) -> bool:
    from travelogue.config.shot_grouping import ShotGroupMosaicPolicy

    if isinstance(cfg, ShotGroupMosaicPolicy):
        return bool(cfg.same_group_anti_slice)
    if not ssg_hard_reject_active(cfg):
        return False
    mosaic = getattr(getattr(cfg, "shot_grouping", None), "mosaic", None)
    if mosaic is None:
        return True
    return bool(getattr(mosaic, "same_group_anti_slice", True))


def ssg_cross_group_hard_reject_active(cfg: Any) -> bool:
    from travelogue.config.shot_grouping import ShotGroupMosaicPolicy

    if isinstance(cfg, ShotGroupMosaicPolicy):
        return bool(cfg.cross_group_hard_reject)
    if not ssg_hard_reject_active(cfg):
        return False
    mosaic = getattr(getattr(cfg, "shot_grouping", None), "mosaic", None)
    if mosaic is None:
        return True
    return bool(getattr(mosaic, "slice_cross_group_hard_reject", True))
