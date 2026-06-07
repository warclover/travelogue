"""LSE decision log projection."""

from __future__ import annotations

from travelogue.layout_engine.decision_log import (
    ingest_beam_logs,
    ingest_mosaic_logs,
    project_mosaic_window,
    strategy_trace_from_pack,
)
from travelogue.layout_engine.registry import get_strategy_pack


def test_project_mosaic_window_maps_winner() -> None:
    raw = {
        "segmentId": "ch-01",
        "windowSize": 5,
        "windowStart": 3,
        "winnerPatternId": "screen-portrait-3",
        "winnerScore": 0.81,
        "winnerReasonCodes": ["R_RHYTHM_OK"],
        "plannerPath": "mosaic",
        "geometryRejectedTemplates": [
            {"templateId": "screen-portrait-5", "reason": "geometry_invalid"}
        ],
    }
    ev = project_mosaic_window(raw)
    assert ev["picked"]["patternId"] == "screen-portrait-3"
    assert ev["window"] == {"start": 3, "size": 5}
    assert ev["rejected"][0]["patternId"] == "screen-portrait-5"
    assert ev["explain"] == {"topFactors": [], "penalties": []}


def test_ingest_beam_logs() -> None:
    logs = [
        {
            "chapterId": "day-bucket-1",
            "events": [
                {
                    "type": "beam_pick",
                    "variant": "with_hero",
                    "plannerPath": "beam",
                    "score": {"total": 0.77},
                    "candidateCount": 4,
                }
            ],
        }
    ]
    events = ingest_beam_logs(logs)
    assert len(events) == 1
    assert events[0]["meta"]["source"] == "beam_bucket"


def test_ingest_mosaic_with_strategy_trace() -> None:
    pack = get_strategy_pack("lse-default-2026-06")
    trace = strategy_trace_from_pack(pack)
    events = ingest_mosaic_logs(
        [
            {
                "segmentId": "ch",
                "windowSize": 3,
                "windowStart": 0,
                "winnerPatternId": "screen-portrait-3",
                "winnerScore": 0.5,
            }
        ],
        trace=trace,
    )
    assert events[0]["strategyId"] == "lse-default-2026-06"
    assert events[0]["weightsHash"].startswith("sha256:")
