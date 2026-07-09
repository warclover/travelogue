"""Phase 16 P0 gap closure: review, geometry_diff, rejectedTemplates, CI hooks."""

from __future__ import annotations

import json

import pytest
import yaml

from travelogue.layout_engine.mosaic.constants import PATTERN_MOSAIC_5_2P3L_EQUAL
from travelogue.layout_engine.mosaic.log import MosaicWindowLog
from travelogue.layout_templates.admission import run_layout_template_admission
from travelogue.layout_templates.geometry_diff import (
    geometry_diff,
    geometry_snapshot,
    save_version_snapshot,
)
from travelogue.layout_templates.layout_admin import layout_template_promotion_plan
from travelogue.layout_templates.promotion import apply_layout_template_yaml_patch
from travelogue.layout_templates.registry import get_engine, reset_engine_cache_for_tests
from travelogue.templating.review import approve_review, get_review_status, submit_for_review


@pytest.fixture(autouse=True)
def _fresh_lte_engine(tmp_path, monkeypatch) -> None:
    reset_engine_cache_for_tests()
    state = tmp_path / "template_admin_state.json"
    state.write_text(
        json.dumps({"revision": 1, "templates": {}, "audit": [], "runtime": {}}),
        encoding="utf-8",
    )
    monkeypatch.setattr("travelogue.templating.admin_store._STATE_PATH", state)
    monkeypatch.setattr("travelogue.domain.template_admin_state._ADMIN_STATE_PATH", state)
    monkeypatch.setattr("travelogue.domain.template_admin_state._RUNTIME_CACHE", None)


@pytest.mark.unit
def test_layout_admission_ga_requires_review_gate() -> None:
    report = run_layout_template_admission(PATTERN_MOSAIC_5_2P3L_EQUAL, target="ga")
    step_names = [s["name"] for s in report["steps"]]
    assert "review_gate" in step_names
    review_step = next(s for s in report["steps"] if s["name"] == "review_gate")
    assert review_step["ok"] is False


@pytest.mark.unit
def test_layout_admission_ga_passes_with_approved_review(tmp_path, monkeypatch) -> None:
    state = tmp_path / "template_admin_state.json"
    state.write_text(
        '{"revision": 1, "templates": {}, "audit": [], "runtime": {}}',
        encoding="utf-8",
    )
    monkeypatch.setattr("travelogue.templating.admin_store._STATE_PATH", state)
    monkeypatch.setattr("travelogue.domain.template_admin_state._ADMIN_STATE_PATH", state)
    monkeypatch.setattr("travelogue.domain.template_admin_state._RUNTIME_CACHE", None)
    submit_for_review(PATTERN_MOSAIC_5_2P3L_EQUAL, operator="test")
    approve_review(PATTERN_MOSAIC_5_2P3L_EQUAL, reviewer="admin")
    report = run_layout_template_admission(PATTERN_MOSAIC_5_2P3L_EQUAL, target="ga")
    review_step = next(s for s in report["steps"] if s["name"] == "review_gate")
    assert review_step["ok"] is True
    assert report["ok"] is True
    assert get_review_status(PATTERN_MOSAIC_5_2P3L_EQUAL)["status"] == "approved"


@pytest.mark.unit
def test_geometry_diff_between_snapshots(tmp_path) -> None:
    engine = get_engine()
    tpl = engine.get(PATTERN_MOSAIC_5_2P3L_EQUAL)
    v1_doc = dict(tpl.raw)
    v1_doc["version"] = 1
    v1_doc["stage"] = dict(v1_doc["stage"])
    v1_doc["stage"]["gap"] = "2px"
    save_version_snapshot(PATTERN_MOSAIC_5_2P3L_EQUAL, yaml_doc=v1_doc)
    diff = geometry_diff(PATTERN_MOSAIC_5_2P3L_EQUAL, 1, tpl.version)
    assert diff["ok"] is True
    assert diff["diff"]["changed"] is True
    assert diff["diff"]["changeCount"] >= 1


@pytest.mark.unit
def test_geometry_snapshot_roundtrip() -> None:
    tpl = get_engine().get(PATTERN_MOSAIC_5_2P3L_EQUAL)
    snap = geometry_snapshot(tpl)
    assert snap["version"] == tpl.version
    assert len(snap["slots"]) == len(tpl.slots)


@pytest.mark.unit
def test_promotion_plan_blocks_skip_transition() -> None:
    plan = layout_template_promotion_plan(PATTERN_MOSAIC_5_2P3L_EQUAL, target="beta")
    assert plan["transitionError"] is not None
    assert plan["canPromote"] is False


@pytest.mark.unit
def test_mosaic_log_includes_rejected_templates() -> None:
    log = MosaicWindowLog(rejected_templates=[{"templateId": "x", "reason": "pattern_disabled"}])
    raw = log.to_dict()
    assert raw["rejectedTemplates"][0]["reason"] == "pattern_disabled"


@pytest.mark.unit
def test_apply_patch_saves_version_history(tmp_path, monkeypatch) -> None:
    src = tmp_path / "screen-test-promo.yaml"
    doc = {
        "id": "screen-test-promo",
        "version": 1,
        "status": "experimental",
        "kind": "composite",
        "displayName": "test",
        "stage": {"aspect": "16:9", "grid": [3, 3]},
        "photoCount": {"min": 5, "max": 5},
        "slots": [
            {"index": i, "rect": [1, 1, 1, 1], "role": "any", "fit": "auto"}
            for i in range(5)
        ],
        "render": {"gridClass": "layout-screen__grid--test", "cssBundle": "journal-screens.css"},
    }
    src.write_text(yaml.safe_dump(doc), encoding="utf-8")
    from travelogue.layout_templates import geometry_diff as gd_mod

    hist_dir = tmp_path / ".version_history"
    monkeypatch.setattr(gd_mod, "VERSION_HISTORY_DIR", hist_dir)
    out = apply_layout_template_yaml_patch(
        "screen-test-promo",
        {"status": "beta", "version": 2},
        templates_dir=tmp_path,
    )
    assert out["before"]["version"] == 1
    assert (hist_dir / "screen-test-promo" / "v1.yaml").is_file()
