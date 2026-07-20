"""LTN D1 · per-screen rhythm gap hints (L0 slot-cohesion / L1 screen / L2 semantic).

Hints are written onto ``layoutScreen.rhythmGap`` and rendered as
``data-rhythm-gap``. L2 is for scene boundaries — never by stuffing breath screens.
"""

from __future__ import annotations

from typing import Any, Literal

from travelogue.domain.time_segments import asset_city

RhythmGap = Literal["L0", "L1", "L2"]


def _first_asset_id(screen: dict[str, Any]) -> str | None:
    for sl in screen.get("slots") or []:
        if isinstance(sl, dict) and sl.get("assetId"):
            return str(sl["assetId"])
    return None


def _screen_city(screen: dict[str, Any], assets_map: dict[str, dict]) -> str | None:
    aid = _first_asset_id(screen)
    if not aid:
        return None
    return asset_city(assets_map.get(aid, {}) or {})


def _is_mosaic_hero(screen: dict[str, Any]) -> bool:
    role = str(screen.get("narrativeRole") or "")
    if role == "mosaic_hero":
        return True
    pid = str(screen.get("patternId") or "")
    return "mosaic" in pid and ("hero" in pid or "main" in pid)


def _is_dense_group(screen: dict[str, Any]) -> bool:
    pid = str(screen.get("patternId") or "")
    role = str(screen.get("narrativeRole") or "")
    if role in ("mosaic_hero", "mosaic_flat", "stack", "pair"):
        return True
    return "mosaic" in pid or "portrait-3" in pid or "portrait-2" in pid


def assign_rhythm_gaps_on_append(
    screen: dict[str, Any],
    *,
    prev_screen: dict[str, Any] | None,
    assets_map: dict[str, dict] | None = None,
) -> None:
    """Mutate ``screen`` (and possibly ``prev_screen``) with rhythmGap.

    Call **before** appending ``screen`` to the chapter list so ``prev_screen``
    is the prior neighbor.
    """
    assets_map = assets_map or {}
    if str(screen.get("patternId") or "") == "screen-breath-pause":
        screen.setdefault("rhythmGap", "L1")
        return

    if "rhythmGap" not in screen:
        screen["rhythmGap"] = "L1"

    if not prev_screen:
        return

    # Semantic pause AFTER previous screen when city changes or climax ends.
    prev_city = _screen_city(prev_screen, assets_map)
    cur_city = _screen_city(screen, assets_map)
    if (
        prev_city
        and cur_city
        and prev_city != cur_city
        and prev_screen.get("rhythmGap") != "L2"
    ):
        prev_screen["rhythmGap"] = "L2"
    elif _is_mosaic_hero(prev_screen) and not _is_mosaic_hero(screen):
        prev_screen["rhythmGap"] = "L2"
    elif (
        _is_dense_group(prev_screen)
        and _is_dense_group(screen)
        and prev_screen.get("rhythmGap") not in ("L2",)
        and screen.get("preserveGroup") is not False
    ):
        # Cohesive group run → tighter screen gap after prev.
        prev_screen["rhythmGap"] = "L0"
