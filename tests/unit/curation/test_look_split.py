"""SSG M2 · look boundary pure logic + injection into shot_grouping."""

from __future__ import annotations

import numpy as np

from travelogue.config.shot_grouping import shot_grouping_from_dict
from travelogue.curation.look_split import split_look_segments
from travelogue.curation.shot_grouping import run_shot_grouping_layer
from travelogue.media.face_embed import l2_normalize


def _vec(*vals: float) -> np.ndarray:
    return l2_normalize(np.asarray(vals, dtype=np.float64))


def _asset(
    aid: str,
    *,
    taken_at: str,
    cluster: int = 1,
    event: str = "evt-01",
) -> dict:
    return {
        "id": aid,
        "takenAt": taken_at,
        "sceneClusterId": cluster,
        "eventId": event,
        "sharpness": 0.5,
        "type": "photo",
    }


def test_split_look_segments_sustain_frames() -> None:
    # sustain=2: need two frames far from current look ref before committing
    a = _vec(1.0, 0.0, 0.0)
    b = _vec(0.0, 1.0, 0.0)
    assets = [
        {"id": "a1", "takenAt": "2025-01-01T10:00:00Z"},
        {"id": "a2", "takenAt": "2025-01-01T10:01:00Z"},
        {"id": "b1", "takenAt": "2025-01-01T10:02:00Z"},
        {"id": "b2", "takenAt": "2025-01-01T10:03:00Z"},
    ]
    vectors = {"a1": a, "a2": a, "b1": b, "b2": b}
    segs = split_look_segments(
        assets, vectors, delta_threshold=0.28, sustain_frames=2
    )
    assert len(segs) == 2
    assert [x["id"] for x in segs[0]] == ["a1", "a2"]
    assert [x["id"] for x in segs[1]] == ["b1", "b2"]


def test_split_look_segments_absorb_single_flash() -> None:
    a = _vec(1.0, 0.0, 0.0)
    flash = _vec(0.0, 0.0, 1.0)
    assets = [
        {"id": "a1", "takenAt": "2025-01-01T10:00:00Z"},
        {"id": "flash", "takenAt": "2025-01-01T10:01:00Z"},
        {"id": "a2", "takenAt": "2025-01-01T10:02:00Z"},
    ]
    segs = split_look_segments(
        assets,
        {"a1": a, "flash": flash, "a2": a},
        delta_threshold=0.28,
        sustain_frames=2,
    )
    assert len(segs) == 1
    assert [x["id"] for x in segs[0]] == ["a1", "flash", "a2"]


def test_split_look_segments_sustain_one_splits_immediately() -> None:
    a = _vec(1.0, 0.0)
    b = _vec(0.0, 1.0)
    assets = [
        {"id": "a1", "takenAt": "2025-01-01T10:00:00Z"},
        {"id": "b1", "takenAt": "2025-01-01T10:01:00Z"},
    ]
    segs = split_look_segments(
        assets,
        {"a1": a, "b1": b},
        delta_threshold=0.28,
        sustain_frames=1,
    )
    assert len(segs) == 2


def test_look_overrides_same_cluster_outfit_change() -> None:
    trip = {
        "assets": [
            _asset("a1", taken_at="2025-01-01T10:00:00Z"),
            _asset("a2", taken_at="2025-01-01T10:01:00Z"),
            _asset("b1", taken_at="2025-01-01T10:02:00Z"),
            _asset("b2", taken_at="2025-01-01T10:03:00Z"),
        ]
    }
    a = _vec(1.0, 0.0, 0.0)
    b = _vec(0.0, 1.0, 0.0)
    vectors = {"a1": a, "a2": a, "b1": b, "b2": b}
    ssg = shot_grouping_from_dict(
        {
            "enabled": "true",
            "look": {"enabled": "true", "deltaThreshold": 0.28, "sustainFrames": 1},
        }
    )
    cfg = type("Cfg", (), {"shot_grouping": ssg})()
    result = run_shot_grouping_layer(
        trip, cfg=cfg, look_vectors=vectors  # type: ignore[arg-type]
    )
    assert result.look_group_count >= 2
    kinds = {a.get("shotGroupKind") for a in trip["assets"]}
    assert kinds == {"look"}
    gids = {a.get("shotGroupId") for a in trip["assets"]}
    assert len(gids) >= 2
    assert trip["assets"][0]["shotGroupId"] != trip["assets"][2]["shotGroupId"]
    stats = (trip.get("curation") or {}).get("shotGrouping", {}).get("stats") or {}
    assert stats.get("lookGroupCount", 0) >= 2


def test_look_disabled_keeps_scene() -> None:
    trip = {
        "assets": [
            _asset("a1", taken_at="2025-01-01T10:00:00Z"),
            _asset("b1", taken_at="2025-01-01T10:01:00Z"),
        ]
    }
    a = _vec(1.0, 0.0)
    b = _vec(0.0, 1.0)
    ssg = shot_grouping_from_dict(
        {"enabled": "true", "look": {"enabled": "false"}}
    )
    cfg = type("Cfg", (), {"shot_grouping": ssg})()
    run_shot_grouping_layer(
        trip, cfg=cfg, look_vectors={"a1": a, "b1": b}  # type: ignore[arg-type]
    )
    assert all(a.get("shotGroupKind") == "scene" for a in trip["assets"])
    assert trip["assets"][0]["shotGroupId"] == trip["assets"][1]["shotGroupId"]


def test_no_face_vectors_keeps_scene() -> None:
    """AC-SSG-13 · no appearance → scene groups remain."""
    trip = {
        "assets": [
            _asset("a1", taken_at="2025-01-01T10:00:00Z"),
            _asset("a2", taken_at="2025-01-01T10:01:00Z"),
        ]
    }
    ssg = shot_grouping_from_dict(
        {"enabled": "true", "look": {"enabled": "true"}}
    )
    cfg = type("Cfg", (), {"shot_grouping": ssg})()
    run_shot_grouping_layer(trip, cfg=cfg, look_vectors={})  # type: ignore[arg-type]
    assert all(a.get("shotGroupKind") == "scene" for a in trip["assets"])


def test_look_does_not_merge_across_scene_clusters() -> None:
    trip = {
        "assets": [
            _asset("a1", taken_at="2025-01-01T10:00:00Z", cluster=1),
            _asset("a2", taken_at="2025-01-01T10:01:00Z", cluster=1),
            _asset("c1", taken_at="2025-01-01T10:02:00Z", cluster=2),
            _asset("c2", taken_at="2025-01-01T10:03:00Z", cluster=2),
        ]
    }
    # Same appearance across clusters — must stay separate look groups
    v = _vec(1.0, 0.0, 0.0)
    vectors = {aid: v for aid in ("a1", "a2", "c1", "c2")}
    ssg = shot_grouping_from_dict(
        {"enabled": "true", "look": {"enabled": "true", "sustainFrames": 1}}
    )
    cfg = type("Cfg", (), {"shot_grouping": ssg})()
    run_shot_grouping_layer(
        trip, cfg=cfg, look_vectors=vectors  # type: ignore[arg-type]
    )
    assert trip["assets"][0]["shotGroupId"] != trip["assets"][2]["shotGroupId"]
    assert all(a.get("shotGroupKind") == "look" for a in trip["assets"])


def test_upper_body_crop_and_main_face() -> None:
    from travelogue.vision.look_appearance import select_main_face, upper_body_crop_box

    faces = [(10, 10, 40, 40), (100, 100, 10, 10)]
    main = select_main_face(faces, img_w=200, img_h=200, min_area_ratio=0.01, max_faces=4)
    assert main == (10, 10, 40, 40)
    assert select_main_face(faces, img_w=200, img_h=200, min_area_ratio=0.15, max_faces=4) is None
    assert select_main_face(faces, img_w=200, img_h=200, min_area_ratio=0.01, max_faces=2) is None
    box = upper_body_crop_box((50, 40, 20, 20), img_w=200, img_h=200)
    assert box[2] > 20 and box[3] > 20
