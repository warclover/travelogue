"""PA · acceptance metrics (SRCC + blind export)."""

from __future__ import annotations

from travelogue.config import AestheticConfig
from travelogue.curation.aesthetic_score import purpose_overall
from travelogue.curation.pa_acceptance import (
    export_pa_blind_review,
    spearman_srcc,
    srcc_from_label_rows,
)


def test_spearman_srcc_perfect_monotonic():
    human = [0.2, 0.5, 0.8, 0.9]
    pred = [0.1, 0.4, 0.7, 0.95]
    srcc = spearman_srcc(human, pred)
    assert srcc is not None
    assert srcc > 0.99


def test_spearman_srcc_insufficient_samples():
    assert spearman_srcc([1.0, 2.0], [1.0, 2.0]) is None


def test_srcc_from_label_rows():
    rows = [
        {"humanScore": 0.2, "overall": 0.1},
        {"humanScore": 0.5, "overall": 0.4},
        {"humanScore": 0.9, "overall": 0.85},
    ]
    out = srcc_from_label_rows(rows)
    assert out["sampleCount"] == 3
    assert out["srcc"] is not None
    assert out["srcc"] > 0.9


def test_purpose_overall_differs_by_preset_when_dims_complete():
    asset = {
        "id": "a",
        "quality": {
            "aesthetic": {
                "overall": 0.5,
                "dims": {
                    "composition": 0.9,
                    "exposure": 0.5,
                    "color": 0.5,
                    "lighting": 0.2,
                    "subjectClarity": 0.5,
                },
            }
        },
    }
    cfg = AestheticConfig(use_purpose_presets=True)
    cover = purpose_overall(asset, "cover", cfg=cfg)
    solo = purpose_overall(asset, "solo", cfg=cfg)
    assert cover is not None and solo is not None
    assert cover != solo


def test_purpose_overall_falls_back_when_dims_incomplete():
    asset = {
        "id": "a",
        "quality": {"aesthetic": {"overall": 0.77, "dims": {"composition": 0.5}}},
    }
    cfg = AestheticConfig(use_purpose_presets=True)
    assert purpose_overall(asset, "cover", cfg=cfg) == 0.77


def test_export_pa_blind_review_structure():
    assets = [
        {
            "id": "p1",
            "type": "image",
            "width": 1200,
            "height": 1800,
            "layoutEligible": True,
            "quality": {
                "sharpness": 400,
                "aesthetic": {
                    "overall": 0.7,
                    "dims": {
                        "composition": 0.7,
                        "exposure": 0.6,
                        "color": 0.6,
                        "lighting": 0.5,
                        "subjectClarity": 0.8,
                    },
                },
            },
        },
        {
            "id": "l1",
            "type": "image",
            "width": 2400,
            "height": 1200,
            "layoutEligible": True,
            "quality": {
                "sharpness": 350,
                "aesthetic": {
                    "overall": 0.65,
                    "dims": {
                        "composition": 0.6,
                        "exposure": 0.6,
                        "color": 0.5,
                        "lighting": 0.55,
                        "subjectClarity": 0.7,
                    },
                },
            },
        },
    ]
    out = export_pa_blind_review(assets, export_layout="mobile")
    assert "cover" in out and "hero" in out and "solo" in out
    assert out["cover"].get("coverAssetId")
