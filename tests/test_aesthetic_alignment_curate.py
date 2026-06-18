"""M4 · AA alignment curate hook integration."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import patch

from travelogue.config import AppConfig
from travelogue.curation.aesthetic_score import apply_aesthetic_alignment


def test_apply_aesthetic_alignment_calls_mllm_when_enabled(tmp_path):
    asset = {
        "id": "a1",
        "displayFile": "photo.jpg",
        "quality": {"aesthetic": {"overall": 0.5, "dims": {}}},
    }
    cfg = replace(
        AppConfig(),
        aesthetic=replace(
            AppConfig().aesthetic,
            enabled=True,
            ml_calibrate=False,
            mllm=replace(AppConfig().aesthetic.mllm, enabled=True),
        ),
    )
    with patch(
        "travelogue.vision.aesthetic_mllm.apply_aesthetic_mllm_scores",
        return_value={"scored": 1},
    ) as mllm_mock:
        report = apply_aesthetic_alignment([asset], trip_dir=tmp_path, cfg=cfg)
    mllm_mock.assert_called_once()
    assert report["mllm"]["scored"] == 1
    assert "telemetry" in report


def test_apply_aesthetic_alignment_fail_open_without_ml(tmp_path):
    asset = {
        "id": "a1",
        "displayFile": "missing.jpg",
        "quality": {
            "aesthetic": {
                "overall": 0.55,
                "dims": {
                    "composition": 0.5,
                    "exposure": 0.5,
                    "color": 0.5,
                    "lighting": 0.5,
                    "subjectClarity": 0.5,
                },
            }
        },
    }
    cfg = replace(
        AppConfig(),
        aesthetic=replace(
            AppConfig().aesthetic,
            enabled=True,
            ml_calibrate=False,
            mllm=replace(AppConfig().aesthetic.mllm, enabled=False),
        ),
    )
    report = apply_aesthetic_alignment([asset], trip_dir=tmp_path, cfg=cfg)
    assert report["ml"] is False
    assert report["mllm"] is None
    assert report["telemetry"]["eligibleImages"] == 1
