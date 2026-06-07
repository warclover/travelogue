"""Phase 16 dogfood template eval script (AC-P16-08/15)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.phase16_template_eval import (
    approve_exposure_proposal,
    compare_baseline,
    evaluate_dogfood_trips,
    evaluate_registry,
    submit_exposure_proposals,
)
from travelogue.curation.layout_metrics import (
    chapter_distinct_pattern_counts,
    pattern_diversity_p50,
)
from travelogue.curation.mosaic.metrics import mixed_layout_exposure_rate
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


@pytest.mark.unit
def test_submit_exposure_proposals_cli_flow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from travelogue.templating import admin_store

    state_path = tmp_path / "template_admin_state.json"
    monkeypatch.setattr(admin_store, "_STATE_PATH", state_path)

    report = evaluate_registry()
    proposals = report.get("exposureDebtProposals") or []
    if not proposals:
        pytest.skip("no exposure debt proposals in current dogfood data")

    pending = submit_exposure_proposals(report, operator="cli-test")
    assert pending["status"] == "pending"

    approve_exposure_proposal(pending["id"], approver="cli-a")
    result = approve_exposure_proposal(pending["id"], approver="cli-b")
    assert result["status"] == "approved"

    boosted = next(p for p in proposals if p["suggestedBaseWeight"] > p["currentBaseWeight"])
    from travelogue.curation.mosaic.lte_adapter import template_base_weight

    assert template_base_weight(boosted["templateId"]) == pytest.approx(boosted["suggestedBaseWeight"])


@pytest.mark.unit
def test_evaluate_dogfood_fixture_trips() -> None:
    from scripts.phase16_template_eval import (
        compare_ac15_thresholds,
        evaluate_dogfood_trips,
    )

    root = Path("tests/fixtures/phase16-dogfood")
    out = evaluate_dogfood_trips(root)
    assert out["tripCount"] >= 3
    assert out["aggregate"]["layout.chapter.pattern_diversity_p50"] is not None
    ac15 = compare_ac15_thresholds({"dogfood": out})
    assert ac15["ok"] is True


@pytest.mark.unit
def test_ac15_strict_on_dogfood_fixtures() -> None:
    from scripts.phase16_template_eval import (
        DEFAULT_DOGFOOD_DIR,
        compare_ac15_thresholds,
        evaluate_registry,
    )

    report = evaluate_registry(trips_dir=DEFAULT_DOGFOOD_DIR)
    ac15 = compare_ac15_thresholds(report)
    assert report["dogfood"]["tripCount"] == 6
    assert ac15["ok"] is True


@pytest.mark.unit
def test_propose_cli_empty_proposals(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.phase16_template_eval import compute_exposure_debt_proposals
    from travelogue.layout_templates.registry import LayoutTemplateEngine
    from travelogue.templating import admin_store

    state_path = tmp_path / "template_admin_state.json"
    monkeypatch.setattr(admin_store, "_STATE_PATH", state_path)

    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    target = 1.0 / len(engine.list_active())
    balanced = {t.id: target for t in engine.list_active()}
    flat = compute_exposure_debt_proposals(balanced, engine)
    assert flat == []

    report = {"exposureDebtProposals": flat, "templateRegistryVersion": engine._content_hash}
    with pytest.raises(ValueError, match="E_EXPOSURE_PROPOSALS_EMPTY"):
        submit_exposure_proposals(report)
