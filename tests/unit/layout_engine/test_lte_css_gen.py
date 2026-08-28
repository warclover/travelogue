"""LTE CSS generation tests (W2 · V-P16-05/06)."""

from __future__ import annotations

import pytest

from travelogue.layout_templates.css_gen import (
    LTE_MARKER_END,
    LTE_MARKER_START,
    generate_bundle_css,
    generate_grid_css,
    grid_templates_for,
    validate_css_bundle,
)
from travelogue.layout_templates.registry import LayoutTemplateEngine, reset_engine_cache_for_tests


@pytest.fixture
def engine() -> LayoutTemplateEngine:
    reset_engine_cache_for_tests()
    return LayoutTemplateEngine.load(rebuild_cache=True)


@pytest.mark.unit
def test_page_hero_primitives_emit_gutter_slot_placement(
    engine: LayoutTemplateEngine,
) -> None:
    """page-1-hero-* use margin tracks; slot 0 must sit in the content cell."""
    t = engine.get("page-1-hero-land-wide")
    css = generate_grid_css(t)
    assert 'data-slot="0"' in css
    assert "grid-column: 2;" in css
    assert "grid-row: 2;" in css
    for tid in (
        "page-1-hero-land-right",
        "page-1-hero-land-ultra",
        "page-1-hero-port",
        "page-1-hero-square-right",
    ):
        hero = engine.get(tid)
        hero_css = generate_grid_css(hero)
        assert f".{hero.render_grid_class} .layout-slot[data-slot=\"0\"]" in hero_css


@pytest.mark.unit
def test_generate_grid_css_for_mosaic_composite(engine: LayoutTemplateEngine) -> None:
    t = engine.get("screen-mosaic-5-main-portrait-3land")
    css = generate_grid_css(t)
    assert t.render_grid_class in css
    assert "grid-template-columns" in css
    assert "data-slot=\"0\"" in css


@pytest.mark.unit
def test_validate_css_bundle_matches_journal(engine: LayoutTemplateEngine) -> None:
    t = engine.get("screen-portrait-3")
    issues = validate_css_bundle(t)
    assert issues == []


@pytest.mark.unit
def test_validate_css_bundle_matches_portfolio(engine: LayoutTemplateEngine) -> None:
    t = engine.get("page-1-hero-port")
    issues = validate_css_bundle(t)
    assert issues == []


@pytest.mark.unit
def test_journal_one_slot_primitive_omits_placement(engine: LayoutTemplateEngine) -> None:
    t = engine.get("screen-portrait-1")
    css = generate_grid_css(t)
    assert 'data-slot="0"' not in css


@pytest.mark.unit
def test_generate_bundle_family_split(engine: LayoutTemplateEngine) -> None:
    journal = generate_bundle_css(engine._templates, family="journal")
    portfolio = generate_bundle_css(engine._templates, family="portfolio")
    assert "/* page-" not in journal
    assert "/* screen-" not in portfolio
    assert "/* screen-portrait-1 */" in journal
    assert "/* page-1-hero-port */" in portfolio


@pytest.mark.unit
def test_ac_dpi_19_wrong_portfolio_track_fails(engine: LayoutTemplateEngine) -> None:
    t = engine.get("page-1-hero-port")
    cols, _rows = grid_templates_for(t)
    css = f"{LTE_MARKER_START}\n{generate_grid_css(t)}\n{LTE_MARKER_END}"
    assert validate_css_bundle(t, css_text=css) == []
    tampered = css.replace(cols, "1fr 99fr 1fr", 1)
    issues = validate_css_bundle(t, css_text=tampered)
    assert issues
    assert any("grid-template-columns" in msg for msg in issues)


@pytest.mark.unit
def test_validate_css_bundle_missing_class_is_error(engine: LayoutTemplateEngine) -> None:
    t = engine.get("page-1-hero-port")
    empty = f"{LTE_MARKER_START}\n/* empty */\n{LTE_MARKER_END}"
    issues = validate_css_bundle(t, css_text=empty)
    assert any("missing" in msg for msg in issues)


@pytest.mark.unit
def test_generate_bundle_non_empty(engine: LayoutTemplateEngine) -> None:
    bundle = generate_bundle_css(engine._templates)
    assert "Phase 16 LTE generated" in bundle
    assert len(bundle) > 1000


@pytest.mark.unit
def test_portrait_left_weighted_tracks(engine: LayoutTemplateEngine) -> None:
    # Equal columns (YAML comment): portrait ~0.89, each landscape ~16:9.
    t = engine.get("screen-portrait-1-landscape-2")
    cols, rows = grid_templates_for(t)
    assert cols == "repeat(2, 1fr)"
    assert rows == "repeat(2, 1fr)"
