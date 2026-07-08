"""Curate scoring and bucket ordering."""

from __future__ import annotations

from travelogue.curation.curate_scoring import (
    cover_eligible_assets,
    cover_score,
    sort_bucket_asset_ids,
)
from travelogue.curation.time_segments import cluster_time_segments


def _asset(aid: str, *, w: int = 1200, h: int = 1600, sharp: float = 100.0, **extra) -> dict:
    a = {
        "id": aid,
        "type": "image",
        "width": w,
        "height": h,
        "quality": {"sharpness": sharp},
        "mediaClass": "photo",
        "dateConfidence": "high",
    }
    a.update(extra)
    return a


def test_cover_excludes_screenshot_when_alternative() -> None:
    assets = [
        _asset("shot", w=2400, h=1080, mediaClass="screenshot"),
        _asset("land", w=2400, h=1350),
    ]
    pool = cover_eligible_assets(assets)
    assert len(pool) == 1
    assert pool[0]["id"] == "land"


def test_sharpness_boosts_cover_score() -> None:
    dull = _asset("dull", sharp=50.0)
    sharp = _asset("sharp", sharp=500.0)
    pool = [dull, sharp]
    assert cover_score(sharp, "mobile", median_sharp=200.0, pool=pool) > cover_score(
        dull, "mobile", median_sharp=200.0, pool=pool
    )


def test_sort_bucket_keeps_burst_group() -> None:
    assets_by_id = {
        "a1": {"id": "a1", "takenAt": "2025-04-01T10:00:00Z", "burstGroupId": "burst-001", "quality": {"sharpness": 10}},
        "a2": {"id": "a2", "takenAt": "2025-04-01T10:01:00Z", "burstGroupId": "burst-001", "quality": {"sharpness": 90}},
        "a3": {"id": "a3", "takenAt": "2025-04-01T11:00:00Z"},
    }
    ordered = sort_bucket_asset_ids(["a1", "a2", "a3"], assets_by_id)
    assert ordered.index("a2") < ordered.index("a1")
    assert ordered == ["a2", "a1", "a3"]


def test_cluster_city_change_splits_segment() -> None:
    assets = [
        {
            "id": "a1",
            "takenAt": "2025-04-01T12:00:00Z",
            "place": {"city": "北京"},
            "dateConfidence": "high",
        },
        {
            "id": "a2",
            "takenAt": "2025-04-05T12:00:00Z",
            "place": {"city": "上海"},
            "dateConfidence": "high",
        },
    ]
    segs = cluster_time_segments(assets, gap_days=14, city_gap_days=3, place="旅途")
    assert len(segs) == 2
    assert segs[0].places == ["北京"]
    assert segs[1].places == ["上海"]
