"""Studio / 封面归因文案（PRD-COVER-CALLIGRAPHY-TITLE-V1 §10）。

路线 B/C 必须区分措辞：禁止路线 C 沿用「非 AI 绘图」掩盖生成事实。
"""

from __future__ import annotations

from travelogue.cover_engine.title_art.models import ENGINE_ROUTE_C

#: 与引擎无关的装帧承诺（永远成立：不替换封面实拍）。
ATTR_BASE = "使用你的照片装帧 · 未生成风景"
ATTR_ROUTE_B = "标题为程序化字库合成，非 AI 绘图"
ATTR_ROUTE_C = "标题字迹由 AI 书法风格生成"


def title_art_engine_detail(engine: str | None) -> str:
    """按实际 ``titleArt.engine`` 返回引擎归因句。"""
    if (engine or "").strip() == ENGINE_ROUTE_C:
        return ATTR_ROUTE_C
    return ATTR_ROUTE_B


def title_art_attribution_line(engine: str | None) -> str:
    """完整归因行：装帧承诺 + 引擎区分句。"""
    return f"{ATTR_BASE}。{title_art_engine_detail(engine)}"
