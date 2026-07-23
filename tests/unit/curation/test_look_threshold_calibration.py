"""SSG PR-E · lock look deltaThreshold on synthetic outfit-change golden."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from travelogue.config.shot_grouping import ShotGroupingLookConfig, shot_grouping_from_dict
from travelogue.curation.look_metrics import look_boundary_f1
from travelogue.curation.look_split import split_look_segments
from travelogue.curation.shot_grouping import run_shot_grouping_layer
from travelogue.media.face_embed import l2_normalize

FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "shot-grouping"
    / "outfit-change-synthetic"
)


def _load_fixture() -> tuple[dict, dict[str, np.ndarray]]:
    gold = json.loads((FIXTURE / "shot-groups-golden.json").read_text(encoding="utf-8"))
    raw = json.loads((FIXTURE / "appearance-vectors.json").read_text(encoding="utf-8"))
    vectors = {
        aid: l2_normalize(np.asarray(vec, dtype=np.float64))
        for aid, vec in (raw.get("vectors") or {}).items()
    }
    return gold, vectors


def _ordered_assets(gold: dict) -> list[dict]:
    return sorted(
        gold["assets"],
        key=lambda a: (a["takenAt"], a["id"]),
    )


def _gold_map(gold: dict) -> dict[str, str]:
    return {a["id"]: a["goldLook"] for a in gold["assets"]}


def _pred_map_from_segments(segments: list[list[dict]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for i, seg in enumerate(segments):
        gid = f"pred-{i}"
        for a in seg:
            out[str(a["id"])] = gid
    return out


def test_locked_delta_threshold_meets_boundary_f1() -> None:
    gold, vectors = _load_fixture()
    thr = float(gold["lockedDeltaThreshold"])
    sustain = int(gold["sustainFrames"])
    min_f1 = float(gold["minBoundaryF1"])
    assets = _ordered_assets(gold)
    ordered_ids = [a["id"] for a in assets]

    segs = split_look_segments(
        assets, vectors, delta_threshold=thr, sustain_frames=sustain
    )
    metrics = look_boundary_f1(ordered_ids, _gold_map(gold), _pred_map_from_segments(segs))
    assert metrics["f1"] >= min_f1, metrics
    # Expect ≥3 looks (A/B/C); flash absorbed into A
    assert len(segs) >= 3
    assert any(a["id"] == "flash-1" for a in segs[0])


def test_threshold_sweep_prefers_locked_default() -> None:
    """PR-E · ±0.05 around 0.28; locked value must be among F1≥0.70 winners."""
    gold, vectors = _load_fixture()
    sustain = int(gold["sustainFrames"])
    min_f1 = float(gold["minBoundaryF1"])
    locked = float(gold["lockedDeltaThreshold"])
    assets = _ordered_assets(gold)
    ordered_ids = [a["id"] for a in assets]
    gold_map = _gold_map(gold)

    winners: list[tuple[float, float]] = []
    for i in range(-5, 6):
        thr = round(locked + i * 0.01, 2)
        segs = split_look_segments(
            assets, vectors, delta_threshold=thr, sustain_frames=sustain
        )
        f1 = look_boundary_f1(
            ordered_ids, gold_map, _pred_map_from_segments(segs)
        )["f1"]
        if f1 >= min_f1:
            winners.append((thr, f1))

    assert winners, "no threshold in ±0.05 met F1 gate"
    winner_thrs = {t for t, _ in winners}
    assert locked in winner_thrs
    # Default config matches locked fixture
    assert ShotGroupingLookConfig().delta_threshold == pytest.approx(locked)


def test_end_to_end_shot_grouping_on_synthetic_outfit() -> None:
    gold, vectors = _load_fixture()
    assets = []
    for row in gold["assets"]:
        assets.append(
            {
                "id": row["id"],
                "takenAt": row["takenAt"],
                "sceneClusterId": gold["sceneClusterId"],
                "eventId": gold["eventId"],
                "sharpness": 0.5,
                "type": "photo",
            }
        )
    trip = {"assets": assets}
    ssg = shot_grouping_from_dict(
        {
            "enabled": "true",
            "look": {
                "enabled": "true",
                "deltaThreshold": gold["lockedDeltaThreshold"],
                "sustainFrames": gold["sustainFrames"],
            },
        }
    )
    cfg = type("Cfg", (), {"shot_grouping": ssg})()
    result = run_shot_grouping_layer(
        trip, cfg=cfg, look_vectors=vectors  # type: ignore[arg-type]
    )
    assert result.look_group_count >= 3
    ordered_ids = [a["id"] for a in sorted(assets, key=lambda x: x["takenAt"])]
    pred = {a["id"]: str(a.get("shotGroupId")) for a in trip["assets"]}
    metrics = look_boundary_f1(ordered_ids, _gold_map(gold), pred)
    assert metrics["f1"] >= float(gold["minBoundaryF1"]), metrics
