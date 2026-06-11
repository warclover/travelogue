"""P19 S3-05 · unified reject reason buckets in mosaic / beam decision logs."""

from __future__ import annotations

from travelogue.curation.mosaic.log import MosaicWindowLog, format_log_entry
from travelogue.curation.mosaic.reject_reasons import (
    REJECT_CONSECUTIVE_PATTERN,
    REJECT_GEOMETRY_INVALID,
    REJECT_HARD_INVALID,
    REJECT_MAIN_AR_INELIGIBLE,
    REJECT_ORDERING_FAILED,
    REJECT_PATTERN_DISABLED,
    REJECT_RHYTHM_STATE,
    make_rejection,
    partition_rejections,
)
from travelogue.layout_engine.decision_log import project_beam_bucket, project_mosaic_window


def test_partition_rejections_maps_all_p19_reasons() -> None:
    rejected = [
        make_rejection("a", REJECT_GEOMETRY_INVALID),
        make_rejection("b", REJECT_MAIN_AR_INELIGIBLE, detail="blocked"),
        make_rejection("c", REJECT_RHYTHM_STATE),
        make_rejection("d", REJECT_CONSECUTIVE_PATTERN),
        make_rejection("e", REJECT_PATTERN_DISABLED),
        make_rejection("f", REJECT_ORDERING_FAILED),
        make_rejection("g", REJECT_HARD_INVALID),
    ]
    buckets = partition_rejections(rejected)
    assert buckets["geometryRejectedTemplates"][0]["templateId"] == "a"
    assert buckets["mainArRejectedTemplates"][0]["detail"] == "blocked"
    assert len(buckets["rhythmRejectedTemplates"]) == 2
    assert len(buckets["constraintRejectedTemplates"]) == 3


def test_window_log_buckets_all_reject_reasons() -> None:
    raw = MosaicWindowLog(
        rejected_templates=[
            make_rejection("g1", REJECT_GEOMETRY_INVALID),
            make_rejection("m1", REJECT_MAIN_AR_INELIGIBLE, detail="x"),
            make_rejection("r1", REJECT_RHYTHM_STATE),
            make_rejection("c1", REJECT_CONSECUTIVE_PATTERN),
            make_rejection("p1", REJECT_PATTERN_DISABLED),
            make_rejection("o1", REJECT_ORDERING_FAILED),
            make_rejection("h1", REJECT_HARD_INVALID),
        ]
    ).to_dict()
    window = format_log_entry(raw, "window")
    assert "rejectedTemplates" not in window
    assert window["geometryRejectedTemplates"]
    assert window["mainArRejectedTemplates"]
    assert window["rhythmRejectedTemplates"]
    assert window["constraintRejectedTemplates"]
    assert window["rejectReasonCounts"][REJECT_RHYTHM_STATE] == 1
    assert window["rejectReasonCounts"][REJECT_CONSECUTIVE_PATTERN] == 1


def test_project_mosaic_window_includes_bucketed_rejections() -> None:
    window = format_log_entry(
        MosaicWindowLog(
            segment_id="ch-01",
            winner_pattern_id="screen-portrait-3",
            rejected_templates=[
                make_rejection("x", REJECT_RHYTHM_STATE),
                make_rejection("y", REJECT_PATTERN_DISABLED),
            ],
        ).to_dict(),
        "window",
    )
    event = project_mosaic_window(window, chapter_id="ch-01")
    reasons = {r["reason"] for r in event["rejected"]}
    assert REJECT_RHYTHM_STATE in reasons
    assert REJECT_PATTERN_DISABLED in reasons


def test_project_beam_bucket_includes_rejected_plans() -> None:
    raw = {
        "chapterId": "day-bucket-1",
        "events": [
            {
                "type": "beam_pick",
                "variant": "explicit_single",
                "plannerPath": "explicit_single",
                "fallbackReason": "EXPLICIT_SINGLE_RHYTHM",
                "rejectedPlans": [
                    {"variant": "violating", "reason": REJECT_CONSECUTIVE_PATTERN},
                ],
                "rejectReasonCounts": {REJECT_CONSECUTIVE_PATTERN: 1},
                "score": {"total": 0.5},
            }
        ],
    }
    events = project_beam_bucket(raw)
    assert len(events) == 1
    assert events[0]["rejected"][0]["reason"] == REJECT_CONSECUTIVE_PATTERN
    assert events[0]["meta"]["rejectReasonCounts"][REJECT_CONSECUTIVE_PATTERN] == 1
