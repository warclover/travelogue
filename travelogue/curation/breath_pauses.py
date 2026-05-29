"""P5-S5 / P5-T2 · breath pause screens (web curate) and longshot item interleave."""

from __future__ import annotations

import copy
import uuid

BREATH_PATTERN = "screen-breath-pause"
DEFAULT_INTERVAL = 4


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
) -> int:
    """Mutate chapters: insert breath pause screens every `interval` photo screens (path B)."""
    if interval < 2:
        return 0
    inserted = 0
    since_pause = 0
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
            since_pause += 1
            if since_pause >= interval:
                new_screens.append(_new_breath_screen())
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
        if it.get("type") != "media-card":
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
