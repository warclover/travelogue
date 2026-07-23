"""SSG M1 · scene → shotGroup projection."""

from __future__ import annotations

from travelogue.config.shot_grouping import (
    resolve_shot_grouping_enabled,
    shot_grouping_from_dict,
)
from travelogue.curation.shot_grouping import run_shot_grouping_layer


def _asset(
    aid: str,
    *,
    taken_at: str,
    cluster: int | None,
    event: str | None = "evt-01",
) -> dict:
    out: dict = {
        "id": aid,
        "takenAt": taken_at,
        "sharpness": 0.5,
        "type": "photo",
    }
    if cluster is not None:
        out["sceneClusterId"] = cluster
    if event:
        out["eventId"] = event
    return out


def test_soft_split_same_cluster_across_hours() -> None:
    trip = {
        "assets": [
            _asset("a1", taken_at="2025-01-01T10:00:00Z", cluster=1),
            _asset("a2", taken_at="2025-01-01T10:30:00Z", cluster=1),
            _asset("b1", taken_at="2025-01-01T20:00:00Z", cluster=1),
            _asset("c1", taken_at="2025-01-01T11:00:00Z", cluster=2),
            _asset("c2", taken_at="2025-01-01T11:10:00Z", cluster=2),
        ]
    }
    cfg = type(
        "Cfg",
        (),
        {"shot_grouping": shot_grouping_from_dict({"enabled": "true"})},
    )()
    result = run_shot_grouping_layer(trip, cfg=cfg)  # type: ignore[arg-type]
    assert result.mode == "scene"
    assert result.soft_split_count >= 1
    gids = {a.get("shotGroupId") for a in trip["assets"] if a.get("sceneClusterId") == 1}
    assert len(gids) >= 2
    assert trip["assets"][3]["shotGroupId"] == trip["assets"][4]["shotGroupId"]


def test_absent_scene_cluster_not_grouped() -> None:
    trip = {
        "assets": [
            _asset("a1", taken_at="2025-01-01T10:00:00Z", cluster=1),
            _asset("x1", taken_at="2025-01-01T10:05:00Z", cluster=None),
        ]
    }
    assert "sceneClusterId" not in trip["assets"][1]
    cfg = type(
        "Cfg",
        (),
        {"shot_grouping": shot_grouping_from_dict({"enabled": "true"})},
    )()
    run_shot_grouping_layer(trip, cfg=cfg)  # type: ignore[arg-type]
    assert trip["assets"][0].get("shotGroupId")
    assert trip["assets"][1].get("shotGroupId") is None


def test_enabled_false_clears_groups() -> None:
    trip = {
        "assets": [
            _asset("a1", taken_at="2025-01-01T10:00:00Z", cluster=1),
            _asset("a2", taken_at="2025-01-01T10:05:00Z", cluster=1),
        ]
    }
    on = type(
        "Cfg",
        (),
        {"shot_grouping": shot_grouping_from_dict({"enabled": "true"})},
    )()
    run_shot_grouping_layer(trip, cfg=on)  # type: ignore[arg-type]
    assert trip["assets"][0].get("shotGroupId")
    off = type(
        "Cfg",
        (),
        {"shot_grouping": shot_grouping_from_dict({"enabled": "false"})},
    )()
    result = run_shot_grouping_layer(trip, cfg=off)  # type: ignore[arg-type]
    assert result.mode == "off"
    assert trip["assets"][0].get("shotGroupId") is None
    assert "shotGrouping" not in (trip.get("curation") or {})


def test_shot_group_run_sort_before_scene_cluster() -> None:
    from travelogue.curation.cluster_run_sort import sort_bucket_asset_ids_run_aware

    assets = {
        "a1": {
            "id": "a1",
            "takenAt": "2025-01-01T10:00:00Z",
            "shotGroupId": "sg-a",
            "sceneClusterId": 1,
            "sharpness": 0.5,
        },
        "a2": {
            "id": "a2",
            "takenAt": "2025-01-01T10:01:00Z",
            "shotGroupId": "sg-a",
            "sceneClusterId": 9,
            "sharpness": 0.5,
        },
        "b1": {
            "id": "b1",
            "takenAt": "2025-01-01T10:02:00Z",
            "shotGroupId": "sg-b",
            "sceneClusterId": 1,
            "sharpness": 0.5,
        },
    }
    ordered = sort_bucket_asset_ids_run_aware(["a1", "a2", "b1"], assets)
    assert ordered.index("a1") < ordered.index("a2")
    assert set(ordered[:2]) == {"a1", "a2"}


def test_burst_outranks_shot_group_run() -> None:
    """AC-SSG-06 · burst contiguous even when shotGroupId differs."""
    from travelogue.curation.cluster_run_sort import sort_bucket_asset_ids_run_aware

    assets = {
        "a1": {
            "id": "a1",
            "takenAt": "2025-01-01T10:00:00Z",
            "burstGroupId": "burst-1",
            "shotGroupId": "sg-a",
            "sceneClusterId": 1,
        },
        "a2": {
            "id": "a2",
            "takenAt": "2025-01-01T10:01:00Z",
            "burstGroupId": "burst-1",
            "shotGroupId": "sg-b",
            "sceneClusterId": 2,
        },
        "x1": {
            "id": "x1",
            "takenAt": "2025-01-01T10:02:00Z",
            "shotGroupId": "sg-a",
            "sceneClusterId": 1,
        },
    }
    ordered = sort_bucket_asset_ids_run_aware(["a1", "x1", "a2"], assets)
    assert ordered.index("a1") < ordered.index("a2")
    assert abs(ordered.index("a1") - ordered.index("a2")) == 1


def test_auto_requires_vision_and_clusters() -> None:
    """D-SSG-11 · auto = vision ∧ scene clusters."""
    cfg = shot_grouping_from_dict({"enabled": "auto"})
    assert resolve_shot_grouping_enabled(
        cfg, has_scene_clusters=True, vision_available=True
    )
    assert not resolve_shot_grouping_enabled(
        cfg, has_scene_clusters=True, vision_available=False
    )
    assert not resolve_shot_grouping_enabled(
        cfg, has_scene_clusters=False, vision_available=True
    )


def test_ac07_auto_vision_off_clears_strong_groups(monkeypatch) -> None:
    monkeypatch.setattr(
        "travelogue.vision.clip_encoder.clip_torch_available", lambda: False
    )
    trip = {
        "assets": [
            _asset("a1", taken_at="2025-01-01T10:00:00Z", cluster=1),
            _asset("a2", taken_at="2025-01-01T10:05:00Z", cluster=1),
        ]
    }
    # Seed then clear via auto + vision off
    on = type(
        "Cfg",
        (),
        {"shot_grouping": shot_grouping_from_dict({"enabled": "true"})},
    )()
    run_shot_grouping_layer(trip, cfg=on)  # type: ignore[arg-type]
    assert trip["assets"][0].get("shotGroupId")
    auto = type(
        "Cfg",
        (),
        {"shot_grouping": shot_grouping_from_dict({"enabled": "auto"})},
    )()
    result = run_shot_grouping_layer(trip, cfg=auto)  # type: ignore[arg-type]
    assert result.mode == "off"
    assert trip["assets"][0].get("shotGroupId") is None
