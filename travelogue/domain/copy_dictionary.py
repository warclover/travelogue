"""Frozen Studio UI terms (COPY-DICTIONARY-V1 · Sprint 0)."""

from __future__ import annotations

from typing import Final

ACTION: Final = "导出"

PRODUCT_LONGSHOT: Final = "长图"
PRODUCT_CARD: Final = "卡片"
PRODUCT_ALBUM: Final = "画册"
PRODUCTS: Final = (PRODUCT_LONGSHOT, PRODUCT_CARD, PRODUCT_ALBUM)

INTENT_DAILY_SHARE: Final = "日常分享"
INTENT_CREATOR: Final = "内容创作"
INTENT_ALBUM_PREVIEW: Final = "画册跨页"
INTENTS: Final = (INTENT_DAILY_SHARE, INTENT_CREATOR, INTENT_ALBUM_PREVIEW)

JOURNAL_EXPORT_LABEL: Final = "长图"
JOURNAL_EXPORT_ARIA: Final = "导出长图"
PORTFOLIO_EXPORT_LABEL: Final = "导出作品集"
PORTFOLIO_EXPORT_ARIA: Final = "导出作品集"

SUCCESS_VERB: Final = "已导出"
SHELF_READY: Final = "长图已就绪"
SHELF_STALE: Final = "长图需更新"

FORBIDDEN_UMBRELLA: Final = ("分享图",)
FORBIDDEN_ACTION_ALIAS: Final = ("发微信群",)
FORBIDDEN_POSITION_COPY: Final = ("验货", "灰色按钮", "右上角")

HELP_SEARCH_ALIASES: Final = ("微信", "长图", "分享图", "发微信群", "验货")

VERTICAL_SLICE_SURFACES: Final = (
    "templates/studio/js/help-onboarding.js",
    "templates/studio/preview-toolbar/longshot.js",
    "templates/studio/js/longshot-client.js",
)


def export_label(edition: str) -> str:
    if str(edition or "").strip().lower() == "portfolio":
        return PORTFOLIO_EXPORT_LABEL
    return JOURNAL_EXPORT_LABEL


def export_aria(edition: str) -> str:
    if str(edition or "").strip().lower() == "portfolio":
        return PORTFOLIO_EXPORT_ARIA
    return JOURNAL_EXPORT_ARIA


def success_line(*, count: int, purpose: str, product: str) -> str:
    """Human success sentence. Never use 分享图 as the product."""
    if product not in PRODUCTS:
        raise ValueError(f"unknown product: {product}")
    n = max(0, int(count))
    purpose_text = str(purpose or "").strip()
    if purpose_text:
        return f"{SUCCESS_VERB} {n} 张{purpose_text}{product}"
    return f"{SUCCESS_VERB} {n} 张{product}"
