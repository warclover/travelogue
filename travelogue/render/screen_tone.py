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
    """Build chapter-separator tokens; light chapters use paper + rule, dark use wash."""
    css = screen_tone_css(tone) or DEFAULT_SCREEN_TONE
    if not tone:
        return (
            f"--chapter-separator-accent: {css}; "
            f"--chapter-separator-ink: {_DARK_SEPARATOR_INK}; "
            "--chapter-separator-mode: light; "
            "--chapter-separator-overlay-start: rgba(14, 18, 24, 0.02); "
            "--chapter-separator-overlay-end: rgba(14, 18, 24, 0.08); "
            "--chapter-separator-title-tracking: 0.04em; "
            "--chapter-separator-title-shadow: none;"
        )
    try:
        r = int(tone.get("r", 232))
        g = int(tone.get("g", 228))
        b = int(tone.get("b", 223))
    except (TypeError, ValueError):
        return (
            f"--chapter-separator-accent: {css}; "
            f"--chapter-separator-ink: {_DARK_SEPARATOR_INK}; "
            "--chapter-separator-mode: light; "
            "--chapter-separator-overlay-start: rgba(14, 18, 24, 0.02); "
            "--chapter-separator-overlay-end: rgba(14, 18, 24, 0.08); "
            "--chapter-separator-title-tracking: 0.04em; "
            "--chapter-separator-title-shadow: none;"
        )
    luma = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
    if luma >= 0.64:
        return (
            f"--chapter-separator-accent: {css}; "
            f"--chapter-separator-ink: {_DARK_SEPARATOR_INK}; "
            "--chapter-separator-mode: light; "
            "--chapter-separator-overlay-start: rgba(14, 18, 24, 0.02); "
            "--chapter-separator-overlay-end: rgba(14, 18, 24, 0.08); "
            "--chapter-separator-title-tracking: 0.04em; "
            "--chapter-separator-title-shadow: none;"
        )
    return (
        f"--chapter-separator-accent: {css}; "
        f"--chapter-separator-ink: {_LIGHT_SEPARATOR_INK}; "
        "--chapter-separator-mode: dark; "
        "--chapter-separator-overlay-start: rgba(14, 18, 24, 0.12); "
        "--chapter-separator-overlay-end: rgba(14, 18, 24, 0.28); "
        "--chapter-separator-title-tracking: 0.018em; "
        "--chapter-separator-title-shadow: 0 1px 12px rgba(0, 0, 0, 0.22);"
    )


def chapter_progress_dots(current: int, total: int, *, max_dots: int = 8) -> list[dict[str, bool]]:
    count = min(max(total, 0), max_dots)
    return [{"active": (i + 1) <= current} for i in range(count)]


def _short_decor_tag(ch: dict) -> str:
    tag = str(ch.get("decorLine") or "").strip()
    if not tag or len(tag) > 8:
        return ""
    if any(c in tag for c in "。，,.!?；"):
        return ""
    return tag.upper() if tag.isascii() else tag


def _decor_pull_text(ch: dict, meta_tag: str) -> str:
    decor = str(ch.get("decorLine") or "").strip()
    if not decor:
        return ""
    if meta_tag and decor == meta_tag:
        return ""
    if len(decor) <= 8 and not any(c in decor for c in "。，,.!?；"):
        return ""
    return decor


def _chapter_meta_line(ch: dict, meta: dict | None, divider: dict) -> str:
    parts: list[str] = []
    place = str(divider.get("dividerPlace") or "").strip()
    if not place:
        title = str((meta or {}).get("title") or "").strip()
        if "·" in title:
            place = title.split("·", 1)[0].strip()
        elif "•" in title:
            place = title.split("•", 1)[0].strip()
        elif title:
            place = title
    if place:
        parts.append(place.upper() if place.isascii() else place)
    tag = _short_decor_tag(ch)
    if tag and tag not in parts:
        parts.append(tag)
    return " · ".join(parts)


def build_chapter_separator_ticket(
    ch: dict,
    index: int,
    total: int,
    *,
    meta: dict | None = None,
    divider: dict | None = None,
) -> dict:
    """Ticket-stub chapter separator fields (scheme B)."""
    idx = int(index)
    meta_line = _chapter_meta_line(ch, meta, divider or {})
    meta_tag = _short_decor_tag(ch)
    decor_pull = _decor_pull_text(ch, meta_tag)
    return {
        "hasChapterMeta": bool(meta_line),
        "chapterMeta": meta_line,
        "hasDecorPull": bool(decor_pull),
        "decorPull": decor_pull,
        "chapterProgressDots": chapter_progress_dots(idx, total),
        "hasChapterProgress": total > 1,
        "chapterProgressLabel": f"{idx:02d} / {total:02d}",
    }
