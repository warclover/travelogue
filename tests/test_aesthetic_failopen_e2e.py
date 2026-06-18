"""AC-AA-04 · MLLM / ML unavailable must not break curate (fail-open E2E)."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import patch

from travelogue.config import AppConfig
from travelogue.curation.aesthetic_score import apply_aesthetic_alignment, persist_aesthetic_alignment
from travelogue.curation.curate import run_curate


def _image(aid: str, *, overall: float = 0.55) -> dict:
    return {
        "id": aid,
        "type": "image",
        "layoutEligible": True,
        "width": 1200,
        "height": 1600,
        "aspectKind": "portrait",
        "takenAt": "2025-04-01T10:00:00Z",
        "quality": {
            "sharpness": 150.0,
            "meanLuma": 0.5,
            "aesthetic": {
                "version": "pa-v0.1",
                "overall": overall,
                "source": "rules",
                "dims": {
                    "composition": overall,
                    "exposure": overall,
                    "color": overall,
                    "lighting": overall,
                    "subjectClarity": overall,
                },
                "signals": {},
            },
        },
        "dominantTone": "#4488cc",
    }


def test_apply_aesthetic_alignment_mllm_hook_fail_open_on_exception(tmp_path):
    asset = _image("a1")
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
        side_effect=RuntimeError("api down"),
    ):
        report = apply_aesthetic_alignment([asset], trip_dir=tmp_path, cfg=cfg)
    assert report["mllm"]["error"] == "api down"
    assert asset["quality"]["aesthetic"]["overall"] == 0.55


def test_apply_aesthetic_alignment_mllm_fail_open_returns_report(tmp_path):
    asset = _image("a1")
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
        return_value={"enabled": True, "scored": 0, "failed": 1, "calls": 1, "cached": 0},
    ):
        report = apply_aesthetic_alignment([asset], trip_dir=tmp_path, cfg=cfg)
    assert report["mllm"]["failed"] == 1
    assert asset["quality"]["aesthetic"]["overall"] == 0.55


def test_persist_aesthetic_alignment_writes_telemetry():
    trip: dict = {"assets": [_image("a1"), _image("a2")], "curation": {}}
    report = {
        "ml": False,
        "mllm": {"failed": 2, "calls": 2, "cached": 0, "scored": 0},
        "portraitLite": 0,
    }
    telemetry = persist_aesthetic_alignment(trip, report)
    assert trip["curation"]["aestheticAlignment"]["mllmFailed"] == 2
    assert trip["curation"]["algorithmProfile"]["aestheticMllmEnabled"] is False
    assert telemetry["eligibleImages"] == 2


def test_run_curate_succeeds_with_mllm_disabled_and_no_ml(tmp_path):
    trip = {
        "assets": [_image(f"a{i}") for i in range(1, 8)],
        "meta": {"title": "t", "dateStart": "2025-04-01", "dateEnd": "2025-04-07"},
        "curation": {},
        "pipeline": {},
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
    with patch(
        "travelogue.curation.aesthetic_score.apply_aesthetic_ml_calibration",
        return_value=False,
    ):
        result = run_curate(
            trip,
            export_layout="mobile",
            apply_layout=False,
            trip_dir=tmp_path,
            cfg=cfg,
        )
    assert result.chapter_count >= 1
    assert "aestheticAlignment" in trip.get("curation", {})


def test_run_curate_succeeds_when_mllm_hook_fail_open(tmp_path):
    trip = {
        "assets": [_image(f"a{i}") for i in range(1, 8)],
        "meta": {"title": "t", "dateStart": "2025-04-01", "dateEnd": "2025-04-07"},
        "curation": {},
        "pipeline": {},
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
        return_value={"enabled": True, "scored": 0, "failed": 1, "calls": 0, "cached": 0},
    ):
        result = run_curate(
            trip,
            export_layout="mobile",
            apply_layout=False,
            trip_dir=tmp_path,
            cfg=cfg,
        )
    assert result.chapter_count >= 1
    aa = trip["curation"]["aestheticAlignment"]
    assert aa["failOpen"]["mllmFailures"] == 1
