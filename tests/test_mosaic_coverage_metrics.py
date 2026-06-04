"""eligible_to_screen_coverage + pattern_repeat_rate (PRD §7.1)."""

from __future__ import annotations

from travelogue.curation.layout_metrics import compute_layout_metrics, pattern_repeat_rate
from travelogue.curation.mosaic.coverage import compute_coverage_metrics

from tests._golden.helpers import build_mosaic_eligible_trip, plan_mosaic_screens


def test_pattern_repeat_rate_complements_diversity() -> None:
    chapters = [
        {
            "screens": [
                {"patternId": "screen-portrait-1"},
                {"patternId": "screen-portrait-1"},
            ]
        }
    ]
    assert pattern_repeat_rate(chapters) == 0.5


def test_coverage_metrics_from_displayed_and_eligible() -> None:
    cov = compute_coverage_metrics(
        displayed_asset_ids=["a1", "a2"],
        layout_eligible_assets=[
            {"id": "a1", "layoutEligible": True},
            {"id": "a2", "layoutEligible": True},
            {"id": "a3", "layoutEligible": True},
        ],
    )
    assert cov["eligible_to_screen_coverage"] == round(2 / 3, 6)


def test_coverage_planned_asset_ids_excludes_unbucketed() -> None:
    cov = compute_coverage_metrics(
        displayed_asset_ids=["a1", "a2"],
        layout_eligible_assets=[
            {"id": "a1", "layoutEligible": True},
            {"id": "a2", "layoutEligible": True},
            {"id": "cover-only", "layoutEligible": True},
        ],
        planned_asset_ids={"a1", "a2"},
    )
    assert cov["eligible_to_screen_coverage"] == 1.0
    assert cov["layoutEligibleCount"] == 2
    assert cov["layout.eligible_to_screen_coverage"] == cov["eligible_to_screen_coverage"]


def test_layout_metrics_include_repeat_rate_and_coverage() -> None:
    buckets, aspects, assets = build_mosaic_eligible_trip()
    chapters = plan_mosaic_screens(buckets[:1], aspects, assets)
    metrics = compute_layout_metrics(chapters, assets)
    assert "layout.pattern.repeat_rate" in metrics
    assert metrics["patternRepeatRate"] == metrics["layout.pattern.repeat_rate"]

    displayed = [aid for b in buckets[:1] for aid in b]
    metrics2 = compute_layout_metrics(
        chapters,
        assets,
    )
    cov = compute_coverage_metrics(
        displayed_asset_ids=displayed,
        layout_eligible_assets=assets,
    )
    metrics2.update(cov)
    assert metrics2["eligible_to_screen_coverage"] >= 0.0
