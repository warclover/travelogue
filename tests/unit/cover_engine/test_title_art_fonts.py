"""Unit tests · title_art font pool + glyph coverage (PRD §5.3/§4 · D-CAL-07)."""

from __future__ import annotations

import pytest

from travelogue.cover_engine.title_art.fonts import (
    FALLBACK_STACK,
    glyphs_covered,
    licensed_fonts,
    pick_default_font,
)

pytestmark = pytest.mark.unit


def test_licensed_fonts_excludes_unlicensed_entries() -> None:
    pool = licensed_fonts()
    assert all(f.licensed for f in pool)
    assert len(pool) >= 1


def test_pick_default_font_returns_licensed_entry() -> None:
    font = pick_default_font()
    assert font.licensed is True


def test_glyphs_covered_empty_text_is_true() -> None:
    assert glyphs_covered(FALLBACK_STACK, "") is True


def test_glyphs_covered_no_loadable_font_returns_false() -> None:
    # 全部候选字体文件名都不存在（构造场景） → 判定不可渲染，fail-open。
    assert glyphs_covered(("no-such-font-file.ttf",), "拾光") is False
