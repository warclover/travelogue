"""Geo bucket recovery: layout assets outside segment spans join nearest bucket."""

from __future__ import annotations

from travelogue.curation.clustering_buckets import (
    recover_uncovered_geo_bucket_assets,
    segments_to_buckets,
)
from travelogue.curation.mosaic.coverage import compute_coverage_metrics


def _asset(aid: str, taken_at: str) -> dict:
    return {"id": aid, "takenAt": taken_at, "layoutEligible": True}


def test_recover_uncovered_assets_to_nearest_segment_by_date() -> None:
    segments = [
        {
            "id": "evt-01",
            "startDate": "2025-06-05",
            "endDate": "2025-06-10",
            "assetIds": ["g1", "g2", "g3"],
        },
        {
            "id": "evt-02",
            "startDate": "2025-06-15",
            "endDate": "2025-06-20",
            "assetIds": ["g4", "g5", "g6"],
        },
    ]
    layout_assets = [
        _asset("g1", "2025-06-05T10:00:00Z"),
        _asset("g2", "2025-06-06T10:00:00Z"),
        _asset("g3", "2025-06-07T10:00:00Z"),
        _asset("g4", "2025-06-15T10:00:00Z"),
        _asset("g5", "2025-06-16T10:00:00Z"),
        _asset("g6", "2025-06-17T10:00:00Z"),
        _asset("orphan-early", "2025-06-01T10:00:00Z"),
        _asset("orphan-mid", "2025-06-12T10:00:00Z"),
        _asset("orphan-late", "2025-06-25T10:00:00Z"),
        _asset("orphan-nodate", ""),
    ]
    buckets, seg_ids = segments_to_buckets(segments, layout_assets, cover_id="")
    segments, buckets, seg_ids, recovered = recover_uncovered_geo_bucket_assets(
        segments,
        buckets,
        seg_ids,
        layout_assets,
        cover_id="",
    )

    assert set(recovered) == {
        "orphan-early",
        "orphan-mid",
        "orphan-late",
        "orphan-nodate",
    }
    assert "orphan-early" in buckets[0]
    assert "orphan-mid" in buckets[0]
    assert "orphan-late" in buckets[1]
    assert "orphan-nodate" in buckets[1]
    assert "orphan-early" in segments[0]["assetIds"]
    assert segments[0]["startDate"] == "2025-06-01"


def test_compute_coverage_metrics_reports_geo_recovery() -> None:
    cov = compute_coverage_metrics(
        displayed_asset_ids=["a1"],
        layout_eligible_assets=[{"id": "a1"}, {"id": "a2"}],
        geo_recovered_asset_ids=["a2"],
    )
    assert cov["geoRecoveredCount"] == 1
    assert cov["geoRecoveredAssetIds"] == ["a2"]
