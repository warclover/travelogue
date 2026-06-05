"""Heuristic embedding vector tests (v2 · Phase C-B)."""

from __future__ import annotations

import numpy as np

from travelogue.vision.clip_encoder import (
    HEURISTIC_V2_DIM,
    SUBJECT_CLASSES,
    ClipEncoder,
    _heuristic_vector,
    _trip_heuristic_stats,
)


def test_heuristic_vector_uses_semantic_tone_and_subject() -> None:
    pool = [
        {
            "width": 1200,
            "height": 800,
            "meanLuma": 0.5,
            "dominantTone": "#ff0000",
            "subjectClass": "landscape",
            "quality": {"sharpness": 200},
        },
        {
            "width": 1200,
            "height": 800,
            "meanLuma": 0.5,
            "dominantTone": "#00ff00",
            "subjectClass": "architecture",
            "quality": {"sharpness": 200},
        },
    ]
    stats = _trip_heuristic_stats(pool)
    landscape = _heuristic_vector(pool[0], pool=pool, stats=stats)
    architecture = _heuristic_vector(pool[1], pool=pool, stats=stats)
    assert len(landscape) == HEURISTIC_V2_DIM
    assert landscape[3:6] != architecture[3:6]
    assert landscape[6:14] != architecture[6:14]


def test_different_subjects_use_one_hot_not_ordinal() -> None:
    pool = [
        {"subjectClass": "landscape", "width": 1000, "height": 800, "quality": {"sharpness": 100}},
        {"subjectClass": "architecture", "width": 1000, "height": 800, "quality": {"sharpness": 100}},
    ]
    stats = _trip_heuristic_stats(pool)
    a = _heuristic_vector(pool[0], pool=pool, stats=stats)
    b = _heuristic_vector(pool[1], pool=pool, stats=stats)
    assert a[6:14] != b[6:14]


def test_unknown_subject_maps_to_zero_one_hot() -> None:
    pool = [{"subjectClass": "unknown-label", "width": 1000, "height": 800, "quality": {"sharpness": 100}}]
    stats = _trip_heuristic_stats(pool)
    vec = _heuristic_vector(pool[0], pool=pool, stats=stats)
    assert sum(vec[6:14]) == 0.0


def test_clip_encoder_heuristic_vector_shape() -> None:
    assets = [
        {
            "id": "a1",
            "type": "image",
            "width": 1200,
            "height": 800,
            "quality": {"sharpness": 120},
            "dominantTone": "#336699",
            "subjectClass": SUBJECT_CLASSES[0],
        }
    ]
    enc = ClipEncoder()
    result = enc.embed_assets(assets)
    assert result.vectors.shape == (1, HEURISTIC_V2_DIM)
    assert np.isfinite(result.vectors).all()
