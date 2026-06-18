"""Tests for portrait_analyze (PC-M1)."""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from travelogue.config.portrait import PortraitConfig
from travelogue.curation.portrait_subject_clarity import (
    compute_portrait_subject_clarity,
    norm_face_sharpness,
    penalty_eyes_closed,
    portrait_has_signal,
)
from travelogue.media.portrait_analyze import (
    aggregate_portrait_faces,
    analyze_portrait,
    laplacian_variance,
    pad_bbox,
)
from travelogue.media.portrait_backends import FaceLandmarks, NullBackend, map_ear_to_eyes_open


def test_pad_bbox_clamps_to_image():
    x0, y0, w, h = pad_bbox(10, 10, 50, 50, img_w=100, img_h=100, pad_ratio=0.2)
    assert x0 >= 0 and y0 >= 0
    assert x0 + w <= 100
    assert y0 + h <= 100


def test_map_ear_monotonic():
    low = map_ear_to_eyes_open(0.1)
    high = map_ear_to_eyes_open(0.5)
    assert high > low
    assert 0.0 <= low <= 1.0
    assert 0.0 <= high <= 1.0


def test_penalty_eyes_closed_increases_when_eyes_low():
    assert penalty_eyes_closed(0.2) > penalty_eyes_closed(0.8)


def test_penalty_blur_face_increases_when_sharpness_low():
    from travelogue.curation.portrait_subject_clarity import penalty_blur_face

    assert penalty_blur_face(0.15) > penalty_blur_face(0.7)


def test_portrait_has_signal_requires_confidence():
    asset = {
        "quality": {
            "portrait": {"confidence": 0.2, "eyesOpenScore": 0.9, "faceSharpness": 100.0}
        }
    }
    assert not portrait_has_signal(asset, min_confidence=0.5)
    asset["quality"]["portrait"]["confidence"] = 0.8
    assert portrait_has_signal(asset, min_confidence=0.5)


def test_compute_portrait_subject_clarity_open_beats_closed():
    cfg = PortraitConfig()
    open_score, _ = compute_portrait_subject_clarity(
        norm_sharp=0.6,
        portrait={"eyesOpenScore": 0.9, "faceSharpness": 900.0},
        cfg=cfg,
    )
    closed_score, _ = compute_portrait_subject_clarity(
        norm_sharp=0.6,
        portrait={"eyesOpenScore": 0.15, "faceSharpness": 900.0},
        cfg=cfg,
    )
    assert open_score > closed_score


def test_analyze_portrait_no_faces_returns_zero_confidence():
    img = Image.new("RGB", (200, 200), color=(128, 128, 128))
    result = analyze_portrait(img, [], cfg=PortraitConfig(), backend=NullBackend())
    assert result.confidence == 0.0


def test_laplacian_variance_on_sharp_patch():
    pytest.importorskip("cv2")
    arr = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
    arr[20:44, 20:44] = np.random.randint(0, 256, (24, 24, 3), dtype=np.uint8)
    img = Image.fromarray(arr)
    flat = Image.new("RGB", (64, 64), color=(100, 100, 100))
    assert laplacian_variance(img) >= laplacian_variance(flat)


def test_aggregate_multi_face_eyes_blend():
    from travelogue.media.portrait_analyze import PerFacePortrait

    primary = PerFacePortrait((0, 0, 100, 100), 0.9, 500.0, 200.0, 0.8)
    secondary = PerFacePortrait((120, 0, 80, 80), 0.3, 400.0, 100.0, 0.7)
    agg = aggregate_portrait_faces((primary, secondary), primary_blend=0.7)
    assert agg.eyes_open_score is not None
    assert 0.3 < agg.eyes_open_score < 0.9
