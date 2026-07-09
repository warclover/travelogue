"""LSE-CAP-14 editorial hints writer (§4.5.12 · MVP write-only)."""

from __future__ import annotations

from typing import Any

from travelogue.layout_contract.rhythm import pattern_slot_count
from travelogue.layout_contract.scoring import screen_dominant_tone
from travelogue.media.color_metrics import delta_e_cie76


def _is_dense_screen(screen: dict) -> bool:
    pid = str(screen.get("patternId") or "")
    slots = pattern_slot_count(pid)
    if slots is not None and slots >= 3:
        return True
    return len(screen.get("slots") or []) >= 3


def _is_landscape_hero(screen: dict) -> bool:
    pid = str(screen.get("patternId") or "")
    if "hero" in pid or "main-hero" in pid:
        return True
    slots = screen.get("slots") or []
    if len(slots) == 1:
        da = slots[0].get("displayAspect")
        try:
            return float(da) >= 1.2
        except (TypeError, ValueError):
            pass
    return "landscape" in pid and len(slots) <= 2


def build_editorial_hints(
    chapters: list[dict],
    assets_by_id: dict[str, dict],
    *,
    breath_gap_threshold: int = 3,
    folio_tone_delta_max: float = 12.0,
) -> dict[str, Any]:
    """Analyze screens[] and emit trip.curation.editorialHints (does not mutate screens)."""
    out_chapters: list[dict[str, Any]] = []
    for ch in chapters:
        ch_id = str(ch.get("id") or "")
        screens = [s for s in (ch.get("screens") or []) if s.get("slots")]
        chapter_hint: dict[str, Any] = {"chapterId": ch_id}
        dense_run = 0
        breath_after: int | None = None
        for i, scr in enumerate(screens):
            if _is_dense_screen(scr):
                dense_run += 1
                if dense_run >= breath_gap_threshold and breath_after is None:
                    breath_after = i
            else:
                dense_run = 0
        if breath_after is not None:
            chapter_hint["breathHint"] = {
                "suggested": True,
                "afterScreenIndex": breath_after,
                "reason": "pace_valley",
                "viewportScope": ["web", "print", "mobile"],
            }

        folio_pair: list[int] | None = None
        for i in range(len(screens) - 1):
            a, b = screens[i], screens[i + 1]
            if not (_is_landscape_hero(a) and _is_landscape_hero(b)):
                continue
            ta = screen_dominant_tone(a, assets_by_id)
            tb = screen_dominant_tone(b, assets_by_id)
            if ta and tb:
                de = delta_e_cie76(ta, tb)
                if de <= folio_tone_delta_max:
                    folio_pair = [i, i + 1]
                    break
        if folio_pair is not None:
            chapter_hint["folioHint"] = {
                "suggested": True,
                "pairScreenIndices": folio_pair,
                "reason": "tone_cohesive",
                "viewportScope": ["web", "print"],
            }

        if len(chapter_hint) > 1:
            out_chapters.append(chapter_hint)

    if not out_chapters:
        return {"version": 1, "chapters": []}
    return {"version": 1, "chapters": out_chapters}


def editorial_hints_from_pack(pack_raw: dict[str, Any] | None) -> dict[str, Any]:
    raw = (pack_raw or {}).get("editorial_hints") if isinstance(pack_raw, dict) else {}
    if not isinstance(raw, dict):
        return {"enabled": False, "breath_gap_threshold": 3, "folio_tone_delta_max": 12.0}
    return {
        "enabled": bool(raw.get("enabled", False)),
        "breath_gap_threshold": int(raw.get("breath_gap_threshold", 3)),
        "folio_tone_delta_max": float(raw.get("folio_tone_delta_max", 12.0)),
    }
