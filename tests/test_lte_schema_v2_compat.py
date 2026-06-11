"""P19 S4-07 · Schema v2 loads with v1 templates unchanged."""

from __future__ import annotations

import json

import jsonschema
import pytest

from travelogue.layout_templates.registry import (
    LayoutTemplateEngine,
    reset_engine_cache_for_tests,
    schema_path,
)
from travelogue.layout_templates.validator import validate_template_def


@pytest.fixture(autouse=True)
def _fresh_engine() -> None:
    from travelogue.curation.mosaic.legacy_specs import reset_legacy_specs_cache_for_tests

    reset_engine_cache_for_tests()
    reset_legacy_specs_cache_for_tests()


@pytest.mark.unit
def test_schema_v2_json_schema_valid() -> None:
    schema = json.loads(schema_path().read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)


@pytest.mark.unit
def test_all_templates_pass_ci_validation() -> None:
    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    blocked: list[str] = []
    for tid in sorted(engine._templates):
        report = validate_template_def(engine.get(tid), mode="ci")
        if not report.ok:
            blocked.append(f"{tid}: {report.issues}")
    assert not blocked, blocked


@pytest.mark.unit
def test_v1_ga_templates_remain_rigid_photo_count() -> None:
    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    for t in engine._templates.values():
        if t.schema_version >= 2:
            continue
        if t.status not in ("ga", "beta"):
            continue
        assert t.photo_count_min == t.photo_count_max == len(t.slots), t.id


@pytest.mark.unit
def test_whitespace_hero_v2_template_loads() -> None:
    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    tpl = engine.get("screen-whitespace-hero")
    assert tpl.schema_version == 2
    assert tpl.max_fill_ratio == 0.62
    assert tpl.slots[0].aspect_range is not None
    report = validate_template_def(tpl, mode="ci")
    assert report.ok, report.issues


@pytest.mark.unit
def test_justified_row_v2_template_loads() -> None:
    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    tpl = engine.get("screen-justified-row")
    assert tpl.schema_version == 2
    assert tpl.kind == "justified"
    report = validate_template_def(tpl, mode="ci")
    assert report.ok, report.issues


@pytest.mark.unit
def test_designer_skus_load() -> None:
    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    for tid in ("screen-spread-folio", "screen-asymmetric-hero"):
        tpl = engine.get(tid)
        report = validate_template_def(tpl, mode="ci")
        assert report.ok, f"{tid}: {report.issues}"


@pytest.mark.unit
def test_full_frame_bsp_3_2_in_registry() -> None:
    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    tpl = engine.get("screen-full-frame-bsp-3-2")
    assert tpl.stage.aspect == "3:2"


@pytest.mark.unit
def test_stage_layout_css_variables_for_whitespace_hero() -> None:
    from travelogue.layout_templates.css_gen import stage_layout_css_variables

    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    tpl = engine.get("screen-whitespace-hero")
    vars = stage_layout_css_variables(tpl)
    assert vars["--stage-max-fill-ratio"] == "0.62"
    assert "--stage-margin-top" in vars
