"""Mosaic decision log volume guard (D-MCS-10) + LTN H2 Top3 rejects."""

from __future__ import annotations

import json

from travelogue.layout_engine.mosaic.constants import PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5
from travelogue.layout_engine.mosaic.hook import drain_mosaic_logs
from travelogue.layout_engine.mosaic.log import (
    MosaicWindowLog,
    annotate_winner_plan_logs,
    format_log_entry,
)


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


def test_ega_observability_kept_in_summary_and_window():
    """EGA SHD-01 · ega shorts survive summary + window formatting."""
    raw = MosaicWindowLog(
        winner_pattern_id="screen-landscape-4",
        winner_score=0.7,
        winner_reason_codes=["R_EGA_FLAT_BONUS"],
        ega_enabled=True,
        ega_equal_six_kept=True,
        ega_anti_slice_mode="exempt",
        ega_clone_mode="soft_penalty",
    ).to_dict()
    summary = format_log_entry(raw, "summary")
    window = format_log_entry(raw, "window")
    for view in (summary, window):
        assert view.get("egaEnabled") is True
        assert view.get("egaEqualSixKept") is True
        assert view.get("egaAntiSliceMode") == "exempt"
        assert view.get("egaCloneMode") == "soft_penalty"
    assert "R_EGA_FLAT_BONUS" in (summary.get("winnerReasonCodes") or [])


def test_window_log_keeps_rejected_templates_top3():
    rejected = [
        {"templateId": f"t{i}", "reason": "hard_invalid"} for i in range(5)
    ]
    raw = MosaicWindowLog(rejected_templates=rejected).to_dict()
    window = format_log_entry(raw, "window")
    assert len(window["rejectedTemplates"]) == 3
    assert [r["templateId"] for r in window["rejectedTemplates"]] == ["t0", "t1", "t2"]
    debug = format_log_entry(raw, "debug")
    assert len(debug["rejectedTemplates"]) == 5


def test_window_log_keeps_geometry_rejections_summary():
    hero_id = "screen-mosaic-5-hero-3-2-plus-4"
    raw = MosaicWindowLog(
        rejected_templates=[
            {"templateId": hero_id, "reason": "geometry_invalid"},
            {"templateId": "x", "reason": "ordering_failed"},
        ]
    ).to_dict()
    window = format_log_entry(raw, "window")
    assert window["geometryRejectedTemplates"] == [
        {"templateId": hero_id, "reason": "geometry_invalid"}
    ]
    assert any(r["templateId"] == hero_id for r in window["rejectedTemplates"])


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
    assert window["mainArRejectedTemplates"] == [
        {
            "templateId": hero_id,
            "reason": "main_ar_ineligible",
            "detail": "blocked_panorama",
        }
    ]


def test_annotate_winner_plan_marks_on_screen_patterns():
    logs = [
        {"segmentId": "ch-01", "winnerPatternId": "screen-portrait-3"},
        {"segmentId": "ch-01", "winnerPatternId": "screen-landscape-9"},
    ]
    chapters = [
        {
            "id": "ch-01",
            "curation": {"segmentId": "ch-01"},
            "screens": [{"patternId": "screen-portrait-3"}],
        }
    ]
    out = annotate_winner_plan_logs(logs, chapters)
    assert out[0]["isWinnerPlan"] is True
    assert out[1]["isWinnerPlan"] is False
    assert out[0]["planPhase"] == "pass1"


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
                rejected_templates=[
                    {"templateId": "a", "reason": "hard_invalid"},
                    {"templateId": "b", "reason": "ordering_failed"},
                    {"templateId": "c", "reason": "usage_rule:UR-01"},
                ],
            ).to_dict(),
            "window",
        )
        for i in range(200)
    ]
    payload = json.dumps(logs, ensure_ascii=False)
    assert len(payload) < 200_000
    drain_mosaic_logs()
