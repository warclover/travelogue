"""P19 S4-06 · BSP 3:2 stage aspect (DQ-05)."""

from __future__ import annotations

import pytest

from travelogue.layout_templates.geometry import parse_aspect_ratio, slot_display_aspect
from travelogue.layout_templates.probe_screenshot import (
    BSP_STAGE_3_2_TEMPLATE_IDS,
    build_probe_html,
    measure_probe_stage_aspect,
    run_bsp_stage_aspect_probe,
)
from travelogue.layout_templates.registry import LayoutTemplateEngine, reset_engine_cache_for_tests
from travelogue.layout_templates.validator import validate_template_def


@pytest.fixture(autouse=True)
def _fresh_engine() -> None:
    reset_engine_cache_for_tests()


@pytest.mark.unit
def test_full_frame_bsp_3_2_template_loads() -> None:
    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    tpl = engine.get("screen-full-frame-bsp-3-2")
    assert tpl.schema_version == 2
    assert tpl.stage.aspect == "3:2"
    report = validate_template_def(tpl, mode="ci")
    assert report.ok, report.issues


@pytest.mark.unit
def test_bsp_3_2_slot_display_aspect_matches_stage() -> None:
    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    tpl = engine.get("screen-full-frame-bsp-3-2")
    slot = tpl.slots[0]
    da = slot_display_aspect(slot.rect, tpl.stage)
    assert abs(da - parse_aspect_ratio("3:2")) < 0.01


@pytest.mark.unit
def test_build_probe_html_declares_3_2_aspect_ratio() -> None:
    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    tpl = engine.get("screen-full-frame-bsp-3-2")
    html = build_probe_html(tpl)
    assert "aspect-ratio: 3 / 2" in html


@pytest.mark.unit
def test_bsp_stage_aspect_probe_at_p0_viewport() -> None:
    pytest.importorskip("playwright")
    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    tpl = engine.get("screen-full-frame-bsp-3-2")
    html = build_probe_html(tpl)
    out = measure_probe_stage_aspect(html)
    if out.get("skipped"):
        pytest.skip(out.get("reason", "playwright unavailable"))
    assert out["ok"], out


@pytest.mark.unit
def test_run_bsp_stage_aspect_probe_all_templates() -> None:
    pytest.importorskip("playwright")
    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    out = run_bsp_stage_aspect_probe(engine, template_ids=BSP_STAGE_3_2_TEMPLATE_IDS)
    if out.get("skipped"):
        pytest.skip(out.get("reason", "playwright unavailable"))
    assert out["ok"], out.get("warnings")

