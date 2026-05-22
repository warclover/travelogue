"""Time segment clustering."""

from __future__ import annotations

from datetime import date

from travelogue.curation.time_segments import cluster_time_segments


def _asset(aid: str, day: str) -> dict:
    return {"id": aid, "takenAt": f"{day}T12:00:00Z", "type": "image"}


def test_cluster_two_segments_gap_over_14_days() -> None:
    assets = [
        _asset("a1", "2025-03-10"),
        _asset("a2", "2025-03-12"),
        _asset("b1", "2025-10-20"),
        _asset("b2", "2025-10-22"),
    ]
    segs = cluster_time_segments(assets, gap_days=14, place="北京")
    assert len(segs) == 2
    assert segs[0].asset_ids == ["a1", "a2"]
    assert segs[1].asset_ids == ["b1", "b2"]
    assert "3月" in segs[0].label or "3" in segs[0].label


def test_cluster_single_segment_same_month() -> None:
    assets = [_asset("a1", "2025-04-01"), _asset("a2", "2025-04-05")]
    segs = cluster_time_segments(assets, place="京都")
    assert len(segs) == 1
    assert segs[0].date_start == date(2025, 4, 1)
