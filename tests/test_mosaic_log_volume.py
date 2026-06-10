"""Mosaic decision log volume guard (D-MCS-10)."""

from __future__ import annotations

import json

from travelogue.curation.mosaic.constants import PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5
from travelogue.curation.mosaic.hook import drain_mosaic_logs
from travelogue.curation.mosaic.log import MosaicWindowLog, format_log_entry


def test_window_log_omits_top3_scores():
    raw = MosaicWindowLog(
        winner_pattern_id="screen-portrait-3",
        winner_score=0.8,
        top3_patterns=["a", "b", "c"],
        top3_scores=[0.8, 0.7, 0.6],
    ).to_dict()
    slim = format_log_entry(raw, "window")
    assert "top3Patterns" in slim
    assert "top3Scores" not in slim


def test_window_log_omits_rejected_templates():
    raw = MosaicWindowLog(
        rejected_templates=[{"templateId": "x", "reason": "hard_invalid"}]
    ).to_dict()
    assert "rejectedTemplates" not in format_log_entry(raw, "window")
    assert "rejectedTemplates" in format_log_entry(raw, "debug")


def test_window_log_keeps_geometry_rejections_summary():
    hero_id = "screen-mosaic-5-hero-3-2-plus-4"
    raw = MosaicWindowLog(
        rejected_templates=[
            {"templateId": hero_id, "reason": "geometry_invalid"},
            {"templateId": "x", "reason": "ordering_failed"},
        ]
    ).to_dict()
    window = format_log_entry(raw, "window")
    assert "rejectedTemplates" not in window
    assert window["geometryRejectedTemplates"] == [
        {"templateId": hero_id, "reason": "geometry_invalid"}
    ]


def test_window_log_keeps_main_ar_rejections_summary():
    hero_id = PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5
    raw = MosaicWindowLog(
        rejected_templates=[
            {
                "templateId": hero_id,
                "reason": "main_ar_ineligible",
                "detail": "blocked_panorama",
            },
            {"templateId": "x", "reason": "ordering_failed"},
        ]
    ).to_dict()
    window = format_log_entry(raw, "window")
    assert "rejectedTemplates" not in window
    assert window["mainArRejectedTemplates"] == [
        {
            "templateId": hero_id,
            "reason": "main_ar_ineligible",
            "detail": "blocked_panorama",
        }
    ]


def test_200_window_logs_under_ci_budget():
    logs = [
        format_log_entry(
            MosaicWindowLog(
                segment_id=f"ch-{i // 25}",
                window_size=5,
                winner_pattern_id="screen-mosaic-5-main-portrait-3land",
                winner_score=0.72,
                top3_patterns=["p1", "p2", "p3"],
                top3_scores=[0.72, 0.65, 0.5],
                winner_reason_codes=["R_SHARP"],
            ).to_dict(),
            "window",
        )
        for i in range(200)
    ]
    payload = json.dumps(logs, ensure_ascii=False)
    assert len(payload) < 200_000
    drain_mosaic_logs()
