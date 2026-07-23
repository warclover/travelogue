"""SSG mosaic hard-reject helpers · PRD D-SSG-05/17b/21/22."""

from __future__ import annotations

from typing import Any

from travelogue.layout_engine.mosaic.clone_detection import template_prefers_burst

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


def ssg_hard_reject_active(cfg: Any) -> bool:
    """D-SSG-22 · cross-shotGroup hard-reject follows shotGrouping.mosaic knobs.

    Independent of ``near_scene_clone_gate.enabled`` (which still gates the
    legacy time-heuristic hard reject).
    """
    ssg = getattr(cfg, "shot_grouping", None)
    if ssg is None:
        return False
    if getattr(ssg, "enabled", "auto") == "false":
        return False
    mosaic = getattr(ssg, "mosaic", None)
    if mosaic is not None and not getattr(mosaic, "slice_cross_group_hard_reject", True):
        return False
    return True
