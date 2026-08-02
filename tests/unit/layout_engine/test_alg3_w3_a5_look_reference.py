"""ALG-V3 W3-A5 · Look reference_mode opt-in (PL-A5)."""

from __future__ import annotations

import numpy as np

from travelogue.config.shot_grouping import shot_grouping_from_dict
from travelogue.curation.look_split import (
    normalize_look_reference_mode,
    split_look_segments,
)
from travelogue.media.face_embed import l2_normalize


def _vec(*vals: float) -> np.ndarray:
    return l2_normalize(np.asarray(vals, dtype=np.float64))


def test_normalize_unknown_mode_falls_back_to_first() -> None:
    mode, reason = normalize_look_reference_mode("nope")
    assert mode == "first"
    assert reason and "unknown_look_reference_mode" in reason


def test_default_first_matches_historical_split() -> None:
    a = _vec(1.0, 0.0, 0.0)
    b = _vec(0.0, 1.0, 0.0)
    assets = [
        {"id": "a1", "takenAt": "2025-01-01T10:00:00Z"},
        {"id": "a2", "takenAt": "2025-01-01T10:01:00Z"},
        {"id": "b1", "takenAt": "2025-01-01T10:02:00Z"},
        {"id": "b2", "takenAt": "2025-01-01T10:03:00Z"},
    ]
    vectors = {"a1": a, "a2": a, "b1": b, "b2": b}
    meta: dict = {}
    segs = split_look_segments(
        assets,
        vectors,
        delta_threshold=0.28,
        sustain_frames=2,
        reference_mode="first",
        meta_out=meta,
    )
    assert len(segs) == 2
    assert [x["id"] for x in segs[0]] == ["a1", "a2"]
    assert [x["id"] for x in segs[1]] == ["b1", "b2"]
    assert meta["lookReferenceMode"] == "first"
    assert "lookReferenceSkipReason" not in meta


def test_loader_defaults_reference_mode_first() -> None:
    ssg = shot_grouping_from_dict({"look": {}})
    assert ssg.look.reference_mode == "first"
    ssg2 = shot_grouping_from_dict({"look": {"referenceMode": "ema", "emaAlpha": 0.5}})
    assert ssg2.look.reference_mode == "ema"
    assert abs(ssg2.look.ema_alpha - 0.5) < 1e-9


def test_ema_mode_runs_and_records_meta() -> None:
    a = _vec(1.0, 0.0, 0.0)
    near = _vec(0.95, 0.05, 0.0)
    assets = [
        {"id": "a1", "takenAt": "2025-01-01T10:00:00Z"},
        {"id": "a2", "takenAt": "2025-01-01T10:01:00Z"},
        {"id": "a3", "takenAt": "2025-01-01T10:02:00Z"},
    ]
    meta: dict = {}
    segs = split_look_segments(
        assets,
        {"a1": a, "a2": near, "a3": near},
        delta_threshold=0.28,
        sustain_frames=2,
        reference_mode="ema",
        ema_alpha=0.4,
        meta_out=meta,
    )
    assert len(segs) == 1
    assert meta["lookReferenceMode"] == "ema"


def test_medoid_mode_runs() -> None:
    a = _vec(1.0, 0.0, 0.0)
    b = _vec(0.9, 0.1, 0.0)
    c = _vec(0.85, 0.15, 0.0)
    assets = [
        {"id": "a1", "takenAt": "2025-01-01T10:00:00Z"},
        {"id": "a2", "takenAt": "2025-01-01T10:01:00Z"},
        {"id": "a3", "takenAt": "2025-01-01T10:02:00Z"},
    ]
    meta: dict = {}
    segs = split_look_segments(
        assets,
        {"a1": a, "a2": b, "a3": c},
        delta_threshold=0.5,
        sustain_frames=2,
        reference_mode="medoid",
        meta_out=meta,
    )
    assert len(segs) >= 1
    assert meta["lookReferenceMode"] == "medoid"
