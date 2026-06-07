"""W4: journal-screens.css LTE marker single authority (R-P16-14)."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.curation.mosaic.constants import (
    PATTERN_MOSAIC_5_2P3L_EQUAL,
    PATTERN_MOSAIC_5_HERO_3_2_PLUS_4,
)
from travelogue.layout_templates.css_gen import (
    LTE_MARKER_END,
    LTE_MARKER_START,
    OVERLAYS_MARKER_END,
    OVERLAYS_MARKER_START,
    lte_grid_classes_outside_marker,
)
from travelogue.layout_templates.registry import get_layout_template, reset_engine_cache_for_tests
from travelogue.paths import JOURNAL_SCREENS_CSS


@pytest.fixture(autouse=True)
def _fresh_lte_engine() -> None:
    reset_engine_cache_for_tests()


@pytest.fixture
def journal_css() -> str:
    return Path(JOURNAL_SCREENS_CSS).read_text(encoding="utf-8")


@pytest.mark.unit
def test_journal_has_lte_generated_marker(journal_css: str) -> None:
    assert LTE_MARKER_START in journal_css
    assert LTE_MARKER_END in journal_css
    assert journal_css.index(LTE_MARKER_START) < journal_css.index(LTE_MARKER_END)


@pytest.mark.unit
def test_flagship_and_hero_not_duplicated_outside_marker(journal_css: str) -> None:
    dupes = lte_grid_classes_outside_marker(journal_css)
    flagship = get_layout_template(PATTERN_MOSAIC_5_2P3L_EQUAL).render_grid_class
    hero = get_layout_template(PATTERN_MOSAIC_5_HERO_3_2_PLUS_4).render_grid_class
    assert flagship not in dupes
    assert hero not in dupes


@pytest.mark.unit
def test_flagship_and_hero_css_inside_marker(journal_css: str) -> None:
    start = journal_css.index(LTE_MARKER_START)
    end = journal_css.index(LTE_MARKER_END)
    inside = journal_css[start:end]
    flagship = get_layout_template(PATTERN_MOSAIC_5_2P3L_EQUAL).render_grid_class
    hero = get_layout_template(PATTERN_MOSAIC_5_HERO_3_2_PLUS_4).render_grid_class
    assert flagship in inside
    assert hero in inside


@pytest.mark.unit
def test_no_lte_grid_duplicates_outside_marker(journal_css: str) -> None:
    assert lte_grid_classes_outside_marker(journal_css) == []


@pytest.mark.unit
def test_journal_has_overlay_marker(journal_css: str) -> None:
    assert OVERLAYS_MARKER_START in journal_css
    assert OVERLAYS_MARKER_END in journal_css
    assert 'data-pattern="screen-portrait-2-landscape-2"' in journal_css


@pytest.mark.unit
def test_no_legacy_css_after_overlay_marker(journal_css: str) -> None:
    end = journal_css.index(OVERLAYS_MARKER_END) + len(OVERLAYS_MARKER_END)
    tail = journal_css[end:].strip()
    assert tail == ""


@pytest.mark.unit
def test_journal_css_handwritten_inventory_bounded() -> None:
    from scripts.lte_journal_css_audit import audit_journal_css

    report = audit_journal_css(Path(JOURNAL_SCREENS_CSS))
    assert report["duplicateGridClassesOutsideMarker"] == []
    assert report["outsideGeneratedGridClassCount"] == 0


@pytest.mark.unit
def test_journal_has_base_slot_image_containment(journal_css: str) -> None:
    """Regression: P16 sync must not drop universal slot img sizing (object-fit + 100%)."""
    assert ".layout-slot__img--cover" in journal_css
    assert "object-fit: cover" in journal_css
    assert "width: 100%" in journal_css
    assert "height: 100%" in journal_css
    start = journal_css.index(LTE_MARKER_START)
    preamble = journal_css[:start]
    assert ".layout-slot__img" in preamble
    assert "min-height: 0" in preamble
    assert "layout-slot--blurred-fill" in preamble


@pytest.mark.unit
def test_journal_has_portrait_stage_tokens_and_dense_grid_overlays(journal_css: str) -> None:
    """Regression: overlay block keeps portrait tokens + mosaic/2x2 slot fill rules."""
    ostart = journal_css.index(OVERLAYS_MARKER_START)
    oend = journal_css.index(OVERLAYS_MARKER_END)
    overlays = journal_css[ostart:oend]
    assert "--portrait-stage-vh:" in overlays
    assert "layout-screen__grid--mosaic-" in overlays
    assert "layout-screen__grid--2x2 .layout-slot__img--cover" in overlays
