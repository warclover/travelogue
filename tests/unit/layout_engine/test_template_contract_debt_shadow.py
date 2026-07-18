"""TPC · debt caption/geometry + shadow harnessFp (gap closeout)."""

from __future__ import annotations

from travelogue.layout_engine.contract.debt import (
    build_trip_debt_report,
    caption_coverage,
    merge_debt_reports,
    raw_geometry_percentiles,
)
from travelogue.layout_engine.contract.shadow import MixShadowDiff, compute_mix_shadow_diff


def test_raw_geometry_percentiles_from_logs() -> None:
    logs = [
        {
            "heroProminenceRatio": 0.2,
            "heroCoverageRatio": 0.3,
            "cellAreaCv": 0.1,
        },
        {
            "heroProminenceRatio": 0.8,
            "heroCoverageRatio": 0.7,
            "cellAreaCv": 0.5,
        },
    ]
    out = raw_geometry_percentiles(logs)
    assert out["sampleCount"] == 2
    assert out["heroProminenceRatio"]["n"] == 2
    assert out["heroProminenceRatio"]["p50"] is not None


def test_build_trip_debt_includes_new_fields() -> None:
    rep = build_trip_debt_report(
        trip_id="t1",
        mosaic_logs=[{"plannerPath": "mcs", "windowSize": 4, "heroProminenceRatio": 0.4}],
        chapters=[],
        assets=[],
    )
    assert "captionCoverage" in rep
    assert "rawGeometryPercentiles" in rep
    merged = merge_debt_reports([rep])
    assert "captionCoverage" in merged
    assert "rawGeometryPercentiles" in merged


def test_caption_coverage_counts_flags() -> None:
    logs = [{"captionActive": True}, {"plannerPath": "mcs"}]
    cov = caption_coverage(logs, templates=None)
    assert cov["captionActiveWindows"] == 1


def test_committed_pattern_marks_harness_fp() -> None:
    """Committed pattern in index is merged into live (harnessFp) when try_order misses it."""
    from travelogue.layout_engine.contract.mix_index import mix_key_from_aspects

    aids = ["a1", "a2", "a3", "a4"]
    aspects = {
        "a1": "landscape",
        "a2": "landscape",
        "a3": "portrait",
        "a4": "portrait",
    }
    assets = {aid: {"id": aid} for aid in aids}
    key = mix_key_from_aspects(aids, aspects)
    committed = "screen-mosaic-fake-committed"
    idx = {key: [committed]}
    without = compute_mix_shadow_diff(aids, aspects, assets, mix_index=idx)
    assert committed in without.only_in_index
    with_commit = compute_mix_shadow_diff(
        aids,
        aspects,
        assets,
        mix_index=idx,
        committed_pattern_id=committed,
    )
    assert isinstance(with_commit, MixShadowDiff)
    assert with_commit.harness_fp is True
    assert committed in with_commit.live_pattern_ids
    assert committed not in with_commit.only_in_index
