"""Burst integrity vs cluster run ordering (F-CLU-CUR-05)."""

from __future__ import annotations

from travelogue.curation.cluster_run_sort import sort_bucket_asset_ids_run_aware


def _asset(aid: str, *, taken_at: str, burst: str | None = None, cluster: int | None = None) -> dict:
    out = {"id": aid, "takenAt": taken_at, "sharpness": 0.5}
    if burst:
        out["burstGroupId"] = burst
    if cluster is not None:
        out["sceneClusterId"] = cluster
    return out


def test_burst_group_stays_contiguous_despite_cluster_change() -> None:
    assets = {
        "a1": _asset("a1", taken_at="2025-01-01T10:00:00Z", burst="b1", cluster=1),
        "a2": _asset("a2", taken_at="2025-01-01T10:01:00Z", burst="b1", cluster=2),
        "a3": _asset("a3", taken_at="2025-01-01T10:02:00Z", burst="b1", cluster=2),
        "b1": _asset("b1", taken_at="2025-01-01T11:00:00Z", cluster=2),
        "b2": _asset("b2", taken_at="2025-01-01T11:01:00Z", cluster=1),
    }
    bucket = ["a1", "a2", "a3", "b1", "b2"]
    ordered = sort_bucket_asset_ids_run_aware(bucket, assets)
    assert ordered.index("a1") < ordered.index("a2") < ordered.index("a3")
    assert set(ordered[:3]) == {"a1", "a2", "a3"}


def test_cluster_run_groups_adjacent_same_cluster() -> None:
    assets = {
        "c1": _asset("c1", taken_at="2025-01-01T12:00:00Z", cluster=5),
        "c2": _asset("c2", taken_at="2025-01-01T12:01:00Z", cluster=5),
        "c3": _asset("c3", taken_at="2025-01-01T12:02:00Z", cluster=9),
    }
    ordered = sort_bucket_asset_ids_run_aware(["c1", "c2", "c3"], assets)
    assert ordered.index("c1") < ordered.index("c2")
    assert ordered.index("c2") < ordered.index("c3")
