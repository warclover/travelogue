"""Phase 16 dogfood template eval script (AC-P16-08/15)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.curation.layout_metrics import (
    chapter_distinct_pattern_counts,
    pattern_diversity_p50,
)
from travelogue.curation.mosaic.metrics import mixed_layout_exposure_rate
from scripts.phase16_template_eval import (
    compare_baseline,
    evaluate_dogfood_trips,
    evaluate_registry,
)
from travelogue.layout_templates.registry import reset_engine_cache_for_tests


@pytest.fixture(autouse=True)
def _fresh_lte_engine() -> None:
    reset_engine_cache_for_tests()


@pytest.mark.unit
def test_pattern_diversity_p50_median() -> None:
    chapters = [
        {
            "screens": [
                {"patternId": "a"},
                {"patternId": "b"},
                {"patternId": "a"},
            ]
        },
        {
            "screens": [
                {"patternId": "x"},
                {"patternId": "y"},
                {"patternId": "z"},
            ]
        },
    ]
    assert chapter_distinct_pattern_counts(chapters) == [2, 3]
    assert pattern_diversity_p50(chapters) == 2.5


@pytest.mark.unit
def test_mixed_layout_exposure_rate() -> None:
    chapters = [
        {"screens": [{"patternId": "screen-portrait-3"}]},
        {"screens": [{"patternId": "screen-mosaic-5-2p3l-equal"}]},
    ]
    assert mixed_layout_exposure_rate(chapters) == 0.5


@pytest.mark.unit
def test_evaluate_registry_shape() -> None:
    report = evaluate_registry()
    assert report["readTemplatesFromLte"] is True
    assert report["flagshipPresent"] is True
    assert report["heroPresent"] is True
    assert "templateExposureCount" in report
    assert "dogfood" in report
    assert "aggregate" in report["dogfood"]
    assert "exposureDebtProposals" in report
    assert isinstance(report["exposureDebtProposals"], list)
    assert report.get("templateRegistryVersion")


@pytest.mark.unit
def test_exposure_debt_proposals_shape() -> None:
    from scripts.phase16_template_eval import compute_exposure_debt_proposals
    from travelogue.layout_templates.registry import LayoutTemplateEngine

    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    proposals = compute_exposure_debt_proposals(
        {"screen-portrait-3": 0.9, "screen-mosaic-5-2p3l-equal": 0.01},
        engine,
    )
    assert proposals
    low = next(p for p in proposals if p["templateId"] == "screen-mosaic-5-2p3l-equal")
    assert low["suggestedBaseWeight"] > low["currentBaseWeight"]
    assert low["approvalRequired"] is True


@pytest.mark.unit
def test_compare_baseline_missing_skips(tmp_path: Path) -> None:
    drift = compare_baseline({"dogfood": {"aggregate": {}}}, tmp_path / "missing.json")
    assert drift["ok"] is True
    assert drift.get("skipped") is True


@pytest.mark.unit
def test_evaluate_dogfood_empty_dir(tmp_path: Path) -> None:
    out = evaluate_dogfood_trips(tmp_path)
    assert out["tripCount"] == 0
    assert out["aggregate"]["layout.chapter.pattern_diversity_p50"] is None
