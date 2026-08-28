"""LTE validator tests (W2 · AC-P16-03)."""

from __future__ import annotations

import pytest

from travelogue.layout_engine.mosaic.constants import PATTERN_MOSAIC_5_3P_2L_BALANCED
from travelogue.layout_templates.registry import LayoutTemplateEngine, reset_engine_cache_for_tests
from travelogue.layout_templates.validator import LayoutTemplateGeometryHook, validate_template_def


@pytest.fixture
def engine() -> LayoutTemplateEngine:
    reset_engine_cache_for_tests()
    return LayoutTemplateEngine.load(rebuild_cache=True)


@pytest.mark.unit
def test_3p2l_publish_gate_blocks_wide_landscape_slot(engine: LayoutTemplateEngine) -> None:
    t = engine.get(PATTERN_MOSAIC_5_3P_2L_BALANCED)
    report = validate_template_def(t, mode="publish")
    assert not report.ok
    codes = {i.code for i in report.issues}
    assert "V-P16-04" in codes


@pytest.mark.unit
def test_3p2l_ci_mode_allows_deprecated_with_warn(engine: LayoutTemplateEngine) -> None:
    t = engine.get(PATTERN_MOSAIC_5_3P_2L_BALANCED)
    report = validate_template_def(t, mode="ci")
    assert report.ok
    assert any(i.code == "V-P16-04" and i.level == "warn" for i in report.issues)


@pytest.mark.unit
def test_geometry_hook_validate_for_publish(engine: LayoutTemplateEngine) -> None:
    hook = LayoutTemplateGeometryHook()
    report = hook.validate_for_publish(PATTERN_MOSAIC_5_3P_2L_BALANCED)
    assert not report.ok


@pytest.mark.unit
def test_ga_template_passes_publish_gate(engine: LayoutTemplateEngine) -> None:
    t = engine.get("screen-portrait-3")
    report = validate_template_def(t, mode="publish")
    blocking = [i for i in report.issues if i.level in ("error", "block")]
    assert not blocking, blocking


@pytest.mark.unit
def test_main_off_ladder_blocks_publish_without_sign_off(engine: LayoutTemplateEngine) -> None:
    from dataclasses import replace

    hero = engine.get("screen-mosaic-5-hero-3-2-plus-4")
    unsigned = replace(hero, constraints={**hero.constraints, "arLadderSignOff": {}})
    report = validate_template_def(unsigned, mode="publish")
    assert not report.ok
    assert any(i.code == "V-P16-13" and i.level == "block" for i in report.issues)


@pytest.mark.unit
def test_main_off_ladder_passes_publish_with_sign_off(engine: LayoutTemplateEngine) -> None:
    hero = engine.get("screen-mosaic-5-hero-3-2-plus-4")
    report = validate_template_def(hero, mode="publish")
    blocking = [i for i in report.issues if i.level in ("error", "block")]
    assert not blocking, blocking


@pytest.mark.unit
def test_hero6_templates_declare_main_slot_policy(engine: LayoutTemplateEngine) -> None:
    from travelogue.layout_engine.mosaic.constants import (
        PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
        PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
        PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
    )

    for pid in (
        PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
        PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
        PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
    ):
        report = validate_template_def(engine.get(pid), mode="publish")
        blocking = [i for i in report.issues if i.level in ("error", "block")]
        assert not blocking, (pid, blocking)


@pytest.mark.unit
def test_main_slot_policy_missing_blocks_publish(engine: LayoutTemplateEngine) -> None:
    from dataclasses import replace

    from travelogue.layout_engine.mosaic.constants import PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5

    t = engine.get(PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5)
    stripped = replace(
        t,
        constraints={
            k: v
            for k, v in t.constraints.items()
            if k not in ("mainSlotPolicy", "eligibility")
        },
    )
    report = validate_template_def(stripped, mode="publish")
    assert not report.ok
    assert any(i.code == "V-P16-MAIN-01" for i in report.issues)


@pytest.mark.unit
def test_validator_blocks_more_than_nine_slots(engine: LayoutTemplateEngine) -> None:
    from dataclasses import replace

    from travelogue.layout_templates.models import TemplateSlot

    base = engine.get("screen-portrait-3")
    extra = tuple(
        TemplateSlot(index=i, rect=(1, 1, 1, 1), role="portrait", fit="cover")
        for i in range(3, 10)
    )
    t = replace(
        base,
        photo_count_min=10,
        photo_count_max=10,
        slots=base.slots + extra,
    )
    report = validate_template_def(t, mode="publish")
    assert not report.ok
    assert any(i.code == "V-P16-12" and i.level == "block" for i in report.issues)


@pytest.mark.unit
def test_validator_allows_ten_slots_on_page_faces(engine: LayoutTemplateEngine) -> None:
    t = engine.get("page-10-grid-port")
    report = validate_template_def(t, mode="publish")
    assert not any(i.code == "V-P16-12" for i in report.issues)
