"""P19 S5-01/02 · spread-folio and asymmetric-hero designer SKUs."""

from __future__ import annotations

import pytest

from travelogue.curation.mosaic.lte_adapter import mosaic_registry
from travelogue.curation.mosaic.pattern_catalog import patterns_for_window_size
from travelogue.layout_templates.geometry import slot_display_aspect
from travelogue.layout_templates.registry import LayoutTemplateEngine, reset_engine_cache_for_tests
from travelogue.layout_templates.validator import validate_template_def


@pytest.fixture(autouse=True)
def _fresh_engine() -> None:
    from travelogue.curation.mosaic.legacy_specs import reset_legacy_specs_cache_for_tests
    from travelogue.curation.mosaic.trip_context import set_mosaic_trip_id

    reset_engine_cache_for_tests()
    reset_legacy_specs_cache_for_tests()
    set_mosaic_trip_id(None)


@pytest.mark.unit
def test_spread_folio_template_loads() -> None:
    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    tpl = engine.get("screen-spread-folio")
    assert tpl.schema_version == 2
    assert tpl.photo_count_min == tpl.photo_count_max == 2
    report = validate_template_def(tpl, mode="ci")
    assert report.ok, report.issues


@pytest.mark.unit
def test_asymmetric_hero_template_loads() -> None:
    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    tpl = engine.get("screen-asymmetric-hero")
    assert tpl.kind == "composite"
    assert len(tpl.slots) == 4
    report = validate_template_def(tpl, mode="ci")
    assert report.ok, report.issues


@pytest.mark.unit
def test_designer_skus_in_mosaic_registry_for_window_sizes() -> None:
    reg = mosaic_registry()
    assert "screen-spread-folio" in reg
    assert "screen-asymmetric-hero" in reg
    spread_pats = patterns_for_window_size(2, reg)
    assert any(p.pattern_id == "screen-spread-folio" for p in spread_pats)
    asym_pats = patterns_for_window_size(4, reg)
    assert any(p.pattern_id == "screen-asymmetric-hero" for p in asym_pats)


@pytest.mark.unit
def test_asymmetric_hero_main_slot_is_wide() -> None:
    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    tpl = engine.get("screen-asymmetric-hero")
    main = tpl.slots[0]
    da = slot_display_aspect(main.rect, tpl.stage)
    assert da > 1.0
