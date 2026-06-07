"""Layout template lifecycle admission (AC-P16-09 / GitOps path)."""

from __future__ import annotations

import json

import pytest

from travelogue.curation.mosaic.constants import (
    PATTERN_MOSAIC_5_2P3L_EQUAL,
    PATTERN_MOSAIC_5_HERO_3_2_PLUS_4,
)
from travelogue.layout_templates.admission import run_layout_template_admission
from travelogue.layout_templates.registry import get_engine, reset_engine_cache_for_tests
from travelogue.templating.review import approve_review, submit_for_review


@pytest.fixture(autouse=True)
def _fresh_lte_engine(tmp_path, monkeypatch) -> None:
    reset_engine_cache_for_tests()
    state = tmp_path / "template_admin_state.json"
    state.write_text(
        json.dumps({"revision": 1, "templates": {}, "audit": [], "runtime": {}}),
        encoding="utf-8",
    )
    monkeypatch.setattr("travelogue.templating.admin_store._STATE_PATH", state)


@pytest.mark.unit
def test_flagship_yaml_status_ga() -> None:
    tpl = get_engine().get(PATTERN_MOSAIC_5_2P3L_EQUAL)
    assert tpl.status == "ga"
    assert tpl.version >= 2
    assert int((tpl.rollout or {}).get("percent", 0)) == 100


@pytest.mark.unit
def test_flagship_admission_beta_and_ga() -> None:
    beta = run_layout_template_admission(PATTERN_MOSAIC_5_2P3L_EQUAL, target="beta")
    assert beta["ok"] is True
    submit_for_review(PATTERN_MOSAIC_5_2P3L_EQUAL, operator="test")
    approve_review(PATTERN_MOSAIC_5_2P3L_EQUAL, reviewer="admin")
    ga = run_layout_template_admission(PATTERN_MOSAIC_5_2P3L_EQUAL, target="ga")
    assert ga["ok"] is True
    assert any(s["name"] == "geometry_publish" for s in ga["steps"])
    assert any(s["name"] == "review_gate" and s["ok"] for s in ga["steps"])


@pytest.mark.unit
def test_hero_admission_beta_passes_geometry() -> None:
    report = run_layout_template_admission(PATTERN_MOSAIC_5_HERO_3_2_PLUS_4, target="beta")
    assert report["ok"] is True


@pytest.mark.unit
def test_hero_yaml_status_ga() -> None:
    tpl = get_engine().get(PATTERN_MOSAIC_5_HERO_3_2_PLUS_4)
    assert tpl.status == "ga"
    assert tpl.version >= 3
    assert int((tpl.rollout or {}).get("percent", 0)) == 100


@pytest.mark.unit
def test_hero_admission_ga() -> None:
    submit_for_review(PATTERN_MOSAIC_5_HERO_3_2_PLUS_4, operator="test")
    approve_review(PATTERN_MOSAIC_5_HERO_3_2_PLUS_4, reviewer="admin")
    report = run_layout_template_admission(PATTERN_MOSAIC_5_HERO_3_2_PLUS_4, target="ga")
    assert report["ok"] is True
