"""Unit tests · title_art font pool + glyph coverage (PRD §5.3/§4 · D-CAL-07)."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.cover_engine.title_art.fonts import (
    FALLBACK_STACK,
    FONT_VOICE_BY_STYLE,
    glyphs_covered,
    licensed_fonts,
    pick_default_font,
    pick_font_for_style,
    resolve_font_source,
)

pytestmark = pytest.mark.unit


def test_licensed_fonts_excludes_unlicensed_entries() -> None:
    pool = licensed_fonts()
    assert all(f.licensed for f in pool)
    assert len(pool) >= 1


def test_pick_default_font_returns_licensed_entry() -> None:
    font = pick_default_font()
    assert font.licensed is True


def test_licensed_fonts_are_bundled_as_assets() -> None:
    """D-CAL-07：licensed=True 必须随包有真实文件，避免静默退化到系统字体。"""
    for font in licensed_fonts():
        src = Path(resolve_font_source(font.filename))
        assert src.is_file(), f"missing bundled font asset: {font.filename}"


def test_glyphs_covered_empty_text_is_true() -> None:
    assert glyphs_covered(FALLBACK_STACK, "") is True


def test_glyphs_covered_no_loadable_font_returns_false() -> None:
    # 全部候选字体文件名都不存在（构造场景） → 判定不可渲染，fail-open。
    assert glyphs_covered(("no-such-font-file.ttf",), "拾光") is False


# ---- D-CAL-25 Typeface Voice Matrix ----------------------------------------


def test_font_voice_matrix_only_maps_licensed_fonts() -> None:
    """映射表里的每个字体名都必须真实存在于已授权候选池，避免配错名静默漂移。"""
    licensed_names = {f.name for f in licensed_fonts()}
    for style_id, font_name in FONT_VOICE_BY_STYLE.items():
        assert font_name in licensed_names, f"{style_id} 映射到未授权/不存在的字体 {font_name!r}"


@pytest.mark.parametrize(
    ("style_id", "expected_name"),
    [
        ("veil-footer", "ZhiMangXing-Regular"),
        ("band-cut", "ZhiMangXing-Regular"),
        ("contact-stamp", "鸿雷板书体（简+繁）3.001"),
        ("folio-overlap", "鸿雷板书体（简+繁）3.001"),
    ],
)
def test_pick_font_for_style_matches_voice_matrix(style_id: str, expected_name: str) -> None:
    assert pick_font_for_style(style_id).name == expected_name


@pytest.mark.parametrize("style_id", [None, "", "type-monument", "scroll-head", "unknown-id"])
def test_pick_font_for_style_unknown_falls_back_to_default(style_id: str | None) -> None:
    assert pick_font_for_style(style_id).name == pick_default_font().name
