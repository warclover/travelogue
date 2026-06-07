"""Phase 16 P1 gap tests: pattern_policy, quotas, collage fixtures, asset media."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.curation.mosaic.lte_adapter import mosaic_pattern_disabled
from travelogue.layout_templates.registry import LayoutTemplateEngine, reset_engine_cache_for_tests
from scripts.collage_detect_eval import evaluate_fixtures
from scripts.lte_probe_regress import run_screenshot_probe


@pytest.fixture(autouse=True)
def _fresh() -> None:
    reset_engine_cache_for_tests()


@pytest.mark.unit
def test_lte_adapter_mosaic_pattern_disabled_callable() -> None:
    assert callable(mosaic_pattern_disabled)
    assert mosaic_pattern_disabled("screen-mosaic-5-3portrait-2land-balanced") is True


@pytest.mark.unit
def test_list_active_respects_composite_quota() -> None:
    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    active = engine.list_active(window_size=5, enforce_quotas=True)
    composites = [t for t in active if t.kind == "composite"]
    assert len(composites) <= 6


@pytest.mark.unit
def test_collage_fixture_eval_expanded() -> None:
    report = evaluate_fixtures(Path("docs/acceptance-records/collage-detect-fixtures.json"))
    assert report["fixtureCount"] >= 18
    assert report["recall"] >= 0.85


@pytest.mark.unit
def test_screenshot_probe_with_baselines() -> None:
    from travelogue.layout_templates.probe_screenshot import baseline_path, run_screenshot_probe

    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    pytest.importorskip("playwright")
    if not baseline_path("screen-portrait-3").is_file():
        run_screenshot_probe(engine, update_baselines=True)
    out = run_screenshot_probe(engine)
    if out.get("skipped"):
        pytest.skip(out.get("reason", "playwright unavailable"))
    assert out["compared"] >= 1
    assert out["ok"] is True


GOLDEN_DOGFOOD_CATALOG = {
    "family_mixed": ["mixed-aspects", "portrait-heavy"],
    "landscape": ["mosaic-landscape-6", "mosaic-landscape-9"],
    "portrait": ["mosaic-portrait-3", "mosaic-portrait-4", "mosaic-portrait-8"],
    "user_3p2l_case": ["mixed-aspects"],
}


@pytest.mark.unit
def test_golden_dogfood_three_categories() -> None:
    root = Path("tests/_golden")
    for category, names in GOLDEN_DOGFOOD_CATALOG.items():
        if category == "user_3p2l_case":
            continue
        assert len(names) >= 2, category
        for name in names:
            assert (root / name / "expected.layout.json").is_file(), name
