"""ACP §5.3 · accept layout suggestion → chapter-scoped screens replan.

Preserves chapter boundaries (does **not** call full ``apply_layout_to_trip``).
Fail-open: mark accepted even when replan cannot improve geometry.
"""

from __future__ import annotations

import logging
from typing import Any

from travelogue.config import AppConfig, get_config
from travelogue.layout_contract.chapter_items import (
    collect_screen_asset_ids,
    compact_chapter_items_for_screens,
)

_log = logging.getLogger(__name__)


def _aspect_kind(asset: dict[str, Any]) -> str:
    w = float(asset.get("width") or 0)
    h = float(asset.get("height") or 0)
    if w <= 0 or h <= 0:
        return "square"
    r = w / h
    if r >= 1.15:
        return "landscape"
    if r <= 0.87:
        return "portrait"
    return "square"


def _pattern_slot_hint(pattern_id: str) -> int | None:
    """Best-effort slot count from trailing digit (e.g. screen-portrait-3 → 3)."""
    pid = str(pattern_id or "").strip()
    if not pid:
        return None
    tail = pid.rsplit("-", 1)[-1]
    if tail.isdigit():
        n = int(tail)
        return n if 1 <= n <= 12 else None
    return None


def _prefer_pattern(
    screens: list[dict[str, Any]],
    preferred: str,
) -> bool:
    """If a planned screen has the right slot count, retarget its patternId."""
    want = _pattern_slot_hint(preferred)
    if not want:
        # Prefer exact id if already present
        for sc in screens:
            if str(sc.get("patternId") or "") == preferred:
                return True
        return False
    for sc in screens:
        slots = sc.get("slots") if isinstance(sc.get("slots"), list) else []
        if len(slots) == want:
            if str(sc.get("patternId") or "") != preferred:
                sc["patternId"] = preferred
            return True
    return any(str(sc.get("patternId") or "") == preferred for sc in screens)


def apply_accepted_suggestion_to_chapter(
    trip: dict[str, Any],
    *,
    chapter_id: str,
    suggested_pattern_id: str | None = None,
    cfg: AppConfig | None = None,
) -> dict[str, Any]:
    """Replan screens for one chapter; other chapters unchanged.

    Returns a small result dict: ok / screensChanged / preferredApplied / reason.
    """
    from travelogue.layout_engine.planner.screen_planner import plan_screens_for_chapter

    ch_id = str(chapter_id or "").strip()
    preferred = str(suggested_pattern_id or "").strip() or None
    chapters = trip.get("chapters") if isinstance(trip.get("chapters"), list) else []
    target: dict[str, Any] | None = None
    for ch in chapters:
        if isinstance(ch, dict) and str(ch.get("id") or "") == ch_id:
            target = ch
            break
    if target is None:
        return {
            "ok": False,
            "screensChanged": False,
            "preferredApplied": False,
            "reason": "chapter_not_found",
        }

    asset_ids = collect_screen_asset_ids(target)
    if len(asset_ids) < 1:
        return {
            "ok": False,
            "screensChanged": False,
            "preferredApplied": False,
            "reason": "empty_chapter",
        }

    assets_by_id: dict[str, dict[str, Any]] = {}
    for a in trip.get("assets") or []:
        if isinstance(a, dict) and a.get("id"):
            assets_by_id[str(a["id"])] = a
    aspects = {
        aid: _aspect_kind(assets_by_id[aid])  # type: ignore[arg-type]
        for aid in asset_ids
        if aid in assets_by_id
    }
    if len(aspects) < 1:
        return {
            "ok": False,
            "screensChanged": False,
            "preferredApplied": False,
            "reason": "no_aspects",
        }

    app = cfg or get_config()
    before = list(target.get("screens") or [])
    try:
        screens = plan_screens_for_chapter(
            asset_ids,
            aspects,  # type: ignore[arg-type]
            chapter_id=ch_id,
            assets=assets_by_id,
            trip=trip,
            app_config=app,
            trip_photo_total=len(trip.get("assets") or []),
        )
    except Exception as exc:  # noqa: BLE001
        _log.warning("layout accept replan failed chapter=%s: %s", ch_id, exc)
        return {
            "ok": False,
            "screensChanged": False,
            "preferredApplied": False,
            "reason": "replan_exception",
        }

    if not isinstance(screens, list) or not screens:
        return {
            "ok": False,
            "screensChanged": False,
            "preferredApplied": False,
            "reason": "empty_plan",
        }

    preferred_applied = False
    if preferred:
        preferred_applied = _prefer_pattern(screens, preferred)

    curation = target.setdefault("curation", {})
    if not isinstance(curation, dict):
        curation = {}
        target["curation"] = curation
    if preferred:
        curation["preferredPatternId"] = preferred
        curation["layoutSuggestionAccepted"] = True

    target["screens"] = screens
    compact_chapter_items_for_screens(chapters)
    changed = screens != before
    return {
        "ok": True,
        "screensChanged": bool(changed or preferred_applied),
        "preferredApplied": preferred_applied,
        "reason": "ok",
        "screenCount": len(screens),
    }
