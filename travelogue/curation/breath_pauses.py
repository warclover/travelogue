"""P5-S5 / P5-T2 · breath pause screens (web curate) and longshot item interleave."""

from __future__ import annotations

import uuid

BREATH_PATTERN = "screen-breath-pause"
DEFAULT_INTERVAL = 4


def arc_breath_interval(arc_segment: str | None) -> int:
    """P6 / ART-E1 · shorter pauses after peak, longer during setup."""
    seg = (arc_segment or "").strip().lower()
    if seg == "peak":
        return 3
    if seg in ("climax", "resolution", "epilogue"):
        return 5
    if seg in ("setup", "hook"):
        return 6
    return DEFAULT_INTERVAL


def _screen_arc_segment(screen: dict) -> str | None:
    raw = screen.get("arcSegment")
    return str(raw).strip().lower() if raw else None


def _new_breath_screen(*, label: str = "") -> dict:
    return {
        "screenId": f"breath-{uuid.uuid4().hex[:8]}",
        "patternId": BREATH_PATTERN,
        "slots": [],
        "breathLabel": label or "···",
    }


def insert_breath_screens_in_chapters(
    chapters: list[dict],
    *,
    interval: int = DEFAULT_INTERVAL,
    arc_driven: bool = False,
) -> int:
    """Mutate chapters: insert breath pause screens every `interval` photo screens (path B)."""
    if interval < 2 and not arc_driven:
        return 0
    inserted = 0
    since_pause = 0
    next_interval = interval
    for ch in chapters:
        screens = ch.get("screens") or []
        if not screens:
            continue
        new_screens: list[dict] = []
        for sc in screens:
            if sc.get("patternId") == BREATH_PATTERN:
                new_screens.append(sc)
                continue
            if not any(s.get("assetId") for s in sc.get("slots") or []):
                continue
            new_screens.append(sc)
            if arc_driven:
                next_interval = max(2, arc_breath_interval(_screen_arc_segment(sc)))
            since_pause += 1
            if since_pause >= next_interval:
                tone = sc.get("tone") if isinstance(sc.get("tone"), dict) else None
                label = "···"
                if _screen_arc_segment(sc) == "peak":
                    label = "—"
                breath = _new_breath_screen(label=label)
                if tone:
                    breath["tone"] = dict(tone)
                new_screens.append(breath)
                inserted += 1
                since_pause = 0
        ch["screens"] = new_screens
    return inserted


def interleave_breath_items(
    items: list[dict],
    *,
    interval: int = DEFAULT_INTERVAL,
) -> list[dict]:
    """Path A longshot: insert breath-pause items between media cards."""
    if interval < 2:
        return items
    out: list[dict] = []
    since_pause = 0
    for it in items:
        if it.get("type") == "breath-pause":
            out.append(it)
            continue
        out.append(it)
        # LTN B2 · count group blocks (media-row) as media units, not only cards.
        if it.get("type") not in ("media-card", "media-row", "media-scroll"):
            continue
        since_pause += 1
        if since_pause >= interval:
            out.append({"type": "breath-pause", "label": "···"})
            since_pause = 0
    return out


def build_breath_pause_render_ctx(
    screen: dict,
    *,
    screen_index: int | None = None,
    chapter_index: str | None = None,
) -> dict:
    tone = screen.get("tone") or {}
    r = int(tone.get("r", 26))
    g = int(tone.get("g", 32))
    b = int(tone.get("b", 38))
    style = f"--breath-tone: rgb({r}, {g}, {b});"
    ctx: dict = {
        "isBreathPause": True,
        "breathLabel": screen.get("breathLabel") or "···",
        "screenStyle": style,
        "patternId": BREATH_PATTERN,
    }
    if screen_index is not None:
        ctx["screenIndex"] = screen_index
        ctx["hasScreenIndex"] = True
    if chapter_index:
        ctx["chapterIndex"] = chapter_index
        ctx["hasChapterIndex"] = True
    return ctx
