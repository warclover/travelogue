"""Phase 6 heuristic vector semantic encoding tests."""

from __future__ import annotations

import numpy as np

from travelogue.vision.clip_encoder import SUBJECT_CLASSES, ClipEncoder, _heuristic_vector


def test_heuristic_vector_uses_semantic_tone_and_subject() -> None:
    landscape = _heuristic_vector(
        {
            "width": 1200,
            "height": 800,
            "sharpness": 0.8,
            "meanLuma": 0.5,
            "dominantTone": "#ff0000",
            "subjectClass": "landscape",
        }
    )
    architecture = _heuristic_vector(
        {
            "width": 1200,
            "height": 800,
            "sharpness": 0.8,
            "meanLuma": 0.5,
            "dominantTone": "#00ff00",
            "subjectClass": "architecture",
        }
    )
    assert len(landscape) == 8
    assert landscape[3:5] != architecture[3:5]
    assert landscape[5] != architecture[5]


def test_similar_subjects_map_to_nearby_values() -> None:
    a = _heuristic_vector({"subjectClass": "landscape", "width": 1000, "height": 800})
    b = _heuristic_vector({"subjectClass": "architecture", "width": 1000, "height": 800})
    assert abs(a[5] - b[5]) < 0.5


def test_unknown_subject_maps_to_neutral_index() -> None:
    vec = _heuristic_vector({"subjectClass": "unknown-label", "width": 1000, "height": 800})
    assert vec[5] == 0.5


def test_clip_encoder_heuristic_vector_shape() -> None:
    assets = [
        {
            "id": "a1",
            "type": "image",
            "width": 1200,
            "height": 800,
            "sharpness": 0.7,
            "dominantTone": "#336699",
            "subjectClass": SUBJECT_CLASSES[0],
        }
    ]
    enc = ClipEncoder()
    result = enc.embed_assets(assets)
    assert result.vectors.shape == (1, 8)
    assert np.isfinite(result.vectors).all()
