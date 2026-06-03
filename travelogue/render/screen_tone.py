"""Screen background tone helpers (shared by context + chapters)."""

from __future__ import annotations

DEFAULT_SCREEN_TONE = "#e8e4df"
_LIGHT_SEPARATOR_INK = "#f5f2ea"
_DARK_SEPARATOR_INK = "#1f1d1a"


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


def chapter_separator_style(tone: dict | None) -> str:
    """Build chapter-separator inline style with contrast-safe text color."""
    css = screen_tone_css(tone) or DEFAULT_SCREEN_TONE
    if not tone:
        return (
            f"background: {css}; "
            f"--chapter-separator-ink: {_DARK_SEPARATOR_INK}; "
            "--chapter-separator-overlay-start: rgba(14, 18, 24, 0.02); "
            "--chapter-separator-overlay-end: rgba(14, 18, 24, 0.08); "
            "--chapter-separator-title-tracking: 0.01em; "
            "--chapter-separator-title-shadow: none;"
        )
    try:
        r = int(tone.get("r", 232))
        g = int(tone.get("g", 228))
        b = int(tone.get("b", 223))
    except (TypeError, ValueError):
        return (
            f"background: {css}; "
            f"--chapter-separator-ink: {_DARK_SEPARATOR_INK}; "
            "--chapter-separator-overlay-start: rgba(14, 18, 24, 0.02); "
            "--chapter-separator-overlay-end: rgba(14, 18, 24, 0.08); "
            "--chapter-separator-title-tracking: 0.01em; "
            "--chapter-separator-title-shadow: none;"
        )
    # Relative luminance approximation for contrast fallback.
    luma = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
    if luma >= 0.64:
        return (
            f"background: {css}; "
            f"--chapter-separator-ink: {_DARK_SEPARATOR_INK}; "
            "--chapter-separator-overlay-start: rgba(14, 18, 24, 0.02); "
            "--chapter-separator-overlay-end: rgba(14, 18, 24, 0.08); "
            "--chapter-separator-title-tracking: 0.01em; "
            "--chapter-separator-title-shadow: none;"
        )
    return (
        f"background: {css}; "
        f"--chapter-separator-ink: {_LIGHT_SEPARATOR_INK}; "
        "--chapter-separator-overlay-start: rgba(14, 18, 24, 0.12); "
        "--chapter-separator-overlay-end: rgba(14, 18, 24, 0.28); "
        "--chapter-separator-title-tracking: 0.018em; "
        "--chapter-separator-title-shadow: 0 1px 12px rgba(0, 0, 0, 0.22);"
    )
