"""Scene sub-segment photo conservation (P0-1)."""

from __future__ import annotations

from datetime import date

from travelogue.curation.geo_events import GeoSegment
from travelogue.curation.scene_subsegments import (
    apply_scene_subsegments,
    split_geo_segment_by_scene,
)


def _asset(aid: str, cluster: int) -> dict:
    return {
        "id": aid,
        "sceneClusterId": cluster,
        "takenAt": f"2025-06-01T{int(aid[1:]):02d}:00:00Z",
    }


def test_small_scene_runs_are_coalesced_not_dropped():
    """Runs below min_photos merge into neighbors; no asset_ids lost."""
    segment = GeoSegment(
        id="evt-01",
        name="Day 1",
        start_date=date(2025, 6, 1),
        end_date=date(2025, 6, 1),
        location="Tokyo",
        asset_ids=["a1", "a2", "a3", "a4", "a5", "a6"],
    )
    # cluster runs: [1,1], [2] (orphan), [1,1,1] — orphan must merge, not drop
    assets_by_id = {
        "a1": _asset("a1", 1),
        "a2": _asset("a2", 1),
        "a3": _asset("a3", 2),
        "a4": _asset("a4", 1),
        "a5": _asset("a5", 1),
        "a6": _asset("a6", 1),
    }
    subs, _ = split_geo_segment_by_scene(
        segment, assets_by_id, min_photos_per_sub=3
    )
    assigned = {aid for s in subs for aid in s.asset_ids}
    assert assigned == set(segment.asset_ids)


def test_apply_scene_subsegments_preserves_all_assets():
    segments = [
        GeoSegment(
            id="evt-01",
            name="Day 1",
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 1),
            location="Tokyo",
            asset_ids=["a1", "a2", "a3", "a4", "a5"],
        )
    ]
    assets_by_id = {
        "a1": _asset("a1", 0),
        "a2": _asset("a2", 0),
        "a3": _asset("a3", 1),
        "a4": _asset("a4", 1),
        "a5": _asset("a5", 1),
    }
    refined, _meta = apply_scene_subsegments(
        segments, assets_by_id, min_photos_per_sub=2
    )
    before = {aid for s in segments for aid in s.asset_ids}
    after = {aid for s in refined for aid in s.asset_ids}
    assert before == after
