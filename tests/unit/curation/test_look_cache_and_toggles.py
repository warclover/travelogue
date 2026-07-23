"""SSG M3 · AC-16 look cache + AC-17 toggles."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from travelogue.config.shot_grouping import shot_grouping_from_dict
from travelogue.curation.shot_grouping import run_shot_grouping_layer
from travelogue.media.face_embed import l2_normalize
from travelogue.vision.look_appearance import (
    load_look_appearance_cache,
    save_look_appearance_cache,
)


def _vec(*vals: float) -> np.ndarray:
    return l2_normalize(np.asarray(vals, dtype=np.float64))


def _trip_assets() -> list[dict]:
    return [
        {
            "id": "a1",
            "takenAt": "2025-01-01T10:00:00Z",
            "sceneClusterId": 1,
            "eventId": "e1",
            "sharpness": 0.5,
            "type": "photo",
        },
        {
            "id": "a2",
            "takenAt": "2025-01-01T10:01:00Z",
            "sceneClusterId": 1,
            "eventId": "e1",
            "sharpness": 0.5,
            "type": "photo",
        },
        {
            "id": "b1",
            "takenAt": "2025-01-01T10:02:00Z",
            "sceneClusterId": 1,
            "eventId": "e1",
            "sharpness": 0.5,
            "type": "photo",
        },
        {
            "id": "b2",
            "takenAt": "2025-01-01T10:03:00Z",
            "sceneClusterId": 1,
            "eventId": "e1",
            "sharpness": 0.5,
            "type": "photo",
        },
    ]


def test_look_appearance_cache_roundtrip(tmp_path: Path) -> None:
    """AC-SSG-16 · cache write/load without CLIP encode."""
    vectors = {"a1": _vec(1.0, 0.0), "a2": _vec(0.0, 1.0)}
    save_look_appearance_cache(tmp_path, vectors)
    loaded = load_look_appearance_cache(tmp_path)
    assert set(loaded) == {"a1", "a2"}
    assert float(np.dot(loaded["a1"], vectors["a1"])) > 0.99


def test_ac17_can_disable_look_only() -> None:
    a = _vec(1.0, 0.0, 0.0)
    b = _vec(0.0, 1.0, 0.0)
    vectors = {"a1": a, "a2": a, "b1": b, "b2": b}
    trip = {"assets": _trip_assets()}
    ssg = shot_grouping_from_dict(
        {"enabled": "true", "look": {"enabled": "false", "sustainFrames": 1}}
    )
    cfg = type("Cfg", (), {"shot_grouping": ssg})()
    run_shot_grouping_layer(trip, cfg=cfg, look_vectors=vectors)  # type: ignore[arg-type]
    assert all(x.get("shotGroupKind") == "scene" for x in trip["assets"])
    assert trip["assets"][0]["shotGroupId"] == trip["assets"][2]["shotGroupId"]


def test_ac17_can_disable_all_shot_grouping() -> None:
    trip = {"assets": _trip_assets()}
    on = shot_grouping_from_dict({"enabled": "true", "look": {"enabled": "false"}})
    cfg_on = type("Cfg", (), {"shot_grouping": on})()
    run_shot_grouping_layer(trip, cfg=cfg_on)  # type: ignore[arg-type]
    assert trip["assets"][0].get("shotGroupId")
    off = shot_grouping_from_dict({"enabled": "false"})
    cfg_off = type("Cfg", (), {"shot_grouping": off})()
    result = run_shot_grouping_layer(trip, cfg=cfg_off)  # type: ignore[arg-type]
    assert result.mode == "off"
    assert all(x.get("shotGroupId") is None for x in trip["assets"])
