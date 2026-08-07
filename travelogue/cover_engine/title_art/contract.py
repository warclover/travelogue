"""Title text contract (PRD §4 · BLK-CAL-02)."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

MAX_MAIN_CHARS = 8


@dataclass(frozen=True)
class TitleTextResult:
    main: str
    truncated: bool
    subtitle: str | None
    empty: bool


def resolve_title_text(trip: dict) -> TitleTextResult:
    """主串来源 ``meta.title``；≤8 字（NFC 规范化后计，截断记 truncated）；
    副标可选（``meta.titleArtSubtitle``），无则省略。截断后为空 → ``empty=True``
    （调用方 fail-open，不贴纸）。"""
    meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else {}
    raw = str(meta.get("title") or "").strip()
    normalized = unicodedata.normalize("NFC", raw)
    truncated = False
    if len(normalized) > MAX_MAIN_CHARS:
        normalized = normalized[:MAX_MAIN_CHARS]
        truncated = True
    subtitle_raw = str(meta.get("titleArtSubtitle") or "").strip()
    subtitle = subtitle_raw or None
    return TitleTextResult(
        main=normalized,
        truncated=truncated,
        subtitle=subtitle,
        empty=not normalized,
    )
