"""W3: weighted-track hero composite (AC-P16-16)."""

from __future__ import annotations

import pytest

from travelogue.curation.mosaic.constants import PATTERN_MOSAIC_5_HERO_3_2_PLUS_4
from travelogue.curation.mosaic.grid_specs import EXPLICIT_GRID_SPECS, gap_cells
from travelogue.curation.mosaic.lte_adapter import mosaic_registry
from travelogue.curation.mosaic.pattern_catalog import patterns_for_window_size
from travelogue.layout_templates.css_gen import generate_grid_css, grid_templates_for
from travelogue.layout_templates.registry import reset_engine_cache_for_tests


@pytest.fixture(autouse=True)
def _fresh_lte_engine() -> None:
    reset_engine_cache_for_tests()


@pytest.mark.unit
def test_hero_pattern_in_lte_registry() -> None:
    reg = mosaic_registry()
    assert PATTERN_MOSAIC_5_HERO_3_2_PLUS_4 in reg
    pat = reg[PATTERN_MOSAIC_5_HERO_3_2_PLUS_4]
    assert pat.slot_count == 5


@pytest.mark.unit
def test_hero_in_registry_and_rollout_eligible_in_candidates() -> None:
    reg = mosaic_registry()
    assert PATTERN_MOSAIC_5_HERO_3_2_PLUS_4 in reg
    ids = [p.pattern_id for p in patterns_for_window_size(5, reg)]
    assert PATTERN_MOSAIC_5_HERO_3_2_PLUS_4 in ids


@pytest.mark.unit
def test_hero_rollout_percent_full() -> None:
    from travelogue.curation.mosaic.lte_adapter import lte_rollout_eligible
    from travelogue.layout_templates.registry import get_layout_template

    tpl = get_layout_template(PATTERN_MOSAIC_5_HERO_3_2_PLUS_4)
    assert tpl.status == "ga"
    assert tpl.version >= 3
    assert int((tpl.rollout or {}).get("percent", 0)) == 100
    assert lte_rollout_eligible(PATTERN_MOSAIC_5_HERO_3_2_PLUS_4) is True
    assert lte_rollout_eligible("screen-mosaic-5-2p3l-equal") is True


@pytest.mark.unit
def test_hero_weighted_track_css() -> None:
    from travelogue.layout_templates.registry import get_layout_template

    tpl = get_layout_template(PATTERN_MOSAIC_5_HERO_3_2_PLUS_4)
    cols, rows = grid_templates_for(tpl)
    assert "2fr" in cols
    assert "1fr" in cols
    css = generate_grid_css(tpl)
    assert "grid-row: 1 / span 2" in css
    assert tpl.render_grid_class in css


@pytest.mark.unit
def test_hero_grid_fills_3x2_stage() -> None:
    specs = EXPLICIT_GRID_SPECS[PATTERN_MOSAIC_5_HERO_3_2_PLUS_4]
    assert len(specs) == 5
    assert gap_cells(specs, cols=3, rows=2) == set()
