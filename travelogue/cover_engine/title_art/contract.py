"""Title text contract (PRD §4 · BLK-CAL-02 · OQ-CAL-10)."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

MAX_MAIN_CHARS = 8

#: 与封面 ``<h1>`` / ``img alt`` 同源：走 ``resolve_display_title``（OQ-CAL-10）。
MAIN_SOURCE = "displayTitle"


@dataclass(frozen=True)
class TitleTextResult:
    main: str
    truncated: bool
    subtitle: str | None
    empty: bool
    main_source: str = MAIN_SOURCE


def resolve_title_text(trip: dict) -> TitleTextResult:
    """主串来源与封面 DOM 一致：``resolve_display_title(meta)``（OQ-CAL-10）。

    不再直接读 ``meta.title`` 原文——封面 ``<h1>`` / ``titleArtAlt`` 早已绑定
    展示名（会剥尾部序号噪音等），贴纸若仍忠实渲染原文会跟可见标题不一致
    （真实 trip「夏睿彤年度精选2」→ 贴纸留「2」、h1 去掉「2」）。

    ``meta.title`` 与 ``displayTitle`` 皆空时仍 fail-open（不贴纸），不消费
    ``resolve_display_title`` 的地点兜底文案——那是封面展示层的降级，不是
    艺术字主串合同。

    ≤8 字（NFC 规范化后计，截断记 truncated）；副标可选
    （``meta.titleArtSubtitle``），无则省略。截断后为空 → ``empty=True``
    （调用方 fail-open，不贴纸）。
    """
    from travelogue.domain.title_humanize import resolve_display_title

    meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else {}
    raw_title = str(meta.get("title") or "").strip()
    stored_display = str(meta.get("displayTitle") or "").strip()
    subtitle_raw = str(meta.get("titleArtSubtitle") or "").strip()
    subtitle = subtitle_raw or None
    if not raw_title and not stored_display:
        return TitleTextResult(
            main="",
            truncated=False,
            subtitle=subtitle,
            empty=True,
            main_source=MAIN_SOURCE,
        )

    raw = resolve_display_title(meta).strip()
    normalized = unicodedata.normalize("NFC", raw)
    truncated = False
    if len(normalized) > MAX_MAIN_CHARS:
        normalized = normalized[:MAX_MAIN_CHARS]
        truncated = True
    return TitleTextResult(
        main=normalized,
        truncated=truncated,
        subtitle=subtitle,
        empty=not normalized,
        main_source=MAIN_SOURCE,
    )
