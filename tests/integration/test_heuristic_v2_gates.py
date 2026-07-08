"""Phase C-B gates: heuristic-v2 embedding (C-M1 / C-M2)."""

from __future__ import annotations

import random

import numpy as np

from travelogue.vision.clip_encoder import (
    HEURISTIC_MODEL_V2,
    HEURISTIC_V2_DIM,
    SUBJECT_CLASSES,
    ClipEncoder,
    _heuristic_vector,
)


def _synthetic_asset(i: int, *, sharp: float) -> dict:
    rng = random.Random(i)
    w = rng.randint(800, 4000)
    h = rng.randint(800, 4000)
    subj = SUBJECT_CLASSES[i % len(SUBJECT_CLASSES)]
    return {
        "id": f"a{i}",
        "type": "image",
        "width": w,
        "height": h,
        "quality": {"sharpness": sharp},
        "meanLuma": rng.random(),
        "dominantTone": f"#{rng.randint(0, 0xFFFFFF):06x}",
        "subjectClass": subj,
        "faceCount": 1 if i % 7 == 0 else 0,
        "mediaClass": "photo",
    }


def test_c_m1_heuristic_v2_model_and_dimension(monkeypatch) -> None:
    from travelogue.vision import clip_encoder as mod

    monkeypatch.setattr(mod, "clip_torch_available", lambda: False)
    assets = [_synthetic_asset(i, sharp=50 + i * 30) for i in range(6)]
    result = ClipEncoder().embed_assets(assets)
    assert result.model == HEURISTIC_MODEL_V2
    assert result.vectors.shape == (6, HEURISTIC_V2_DIM)
    assert np.allclose(np.linalg.norm(result.vectors, axis=1), 1.0, atol=1e-5)


def test_heuristic_v2_one_hot_subject_not_ordinal() -> None:
    pool = [
        {"width": 1200, "height": 800, "subjectClass": "landscape"},
        {"width": 1200, "height": 800, "subjectClass": "architecture"},
    ]
    stats = None
    from travelogue.vision.clip_encoder import _trip_heuristic_stats

    stats = _trip_heuristic_stats(pool)
    landscape = _heuristic_vector(pool[0], pool=pool, stats=stats)
    architecture = _heuristic_vector(pool[1], pool=pool, stats=stats)
    assert len(landscape) == HEURISTIC_V2_DIM
    # one-hot block starts at index 6 (after ratio, sharp, luma, sin, cos, sat)
    assert landscape[6:14] != architecture[6:14]
    assert sum(landscape[6:14]) == 1.0
    assert sum(architecture[6:14]) == 1.0


def test_c_m2_sharp_dim_cosine_correlation_below_threshold() -> None:
    """|ρ(sharp_dim, cosine_to_mean)| < 0.7 on synthetic 100-asset trip."""
    assets = [_synthetic_asset(i, sharp=10 + (i * 17) % 500) for i in range(100)]
    stats = None
    from travelogue.vision.clip_encoder import _trip_heuristic_stats

    stats = _trip_heuristic_stats(assets)
    mat = np.array(
        [_heuristic_vector(a, pool=assets, stats=stats) for a in assets],
        dtype=np.float64,
    )
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    mat = mat / np.where(norms < 1e-8, 1.0, norms)
    mean_vec = mat.mean(axis=0)
    mean_vec /= max(np.linalg.norm(mean_vec), 1e-8)
    cosines = mat @ mean_vec
    sharp_col = mat[:, 1]
    if np.std(sharp_col) < 1e-8 or np.std(cosines) < 1e-8:
        return
    rho = float(np.corrcoef(sharp_col, cosines)[0, 1])
    assert abs(rho) < 0.7, f"sharp dominates cosine direction: |rho|={abs(rho):.3f}"
