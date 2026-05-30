"""Screen background tone helpers (shared by context + chapters)."""

from __future__ import annotations

DEFAULT_SCREEN_TONE = "#e8e4df"


def screen_tone_css(tone: dict | None) -> str | None:
    if not tone:
        return DEFAULT_SCREEN_TONE
    try:
        r = int(tone.get("r", 0))
        g = int(tone.get("g", 0))
        b = int(tone.get("b", 0))
    except (TypeError, ValueError):
        return DEFAULT_SCREEN_TONE
    return f"#{r:02x}{g:02x}{b:02x}"
