"""SSG M1 · scene → shotGroup projection."""

from __future__ import annotations

from travelogue.config.shot_grouping import ShotGroupingConfig, shot_grouping_from_dict
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
    cfg = type("Cfg", (), {"shot_grouping": ShotGroupingConfig()})()
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
    cfg = type("Cfg", (), {"shot_grouping": ShotGroupingConfig()})()
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
    on = type("Cfg", (), {"shot_grouping": ShotGroupingConfig()})()
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
