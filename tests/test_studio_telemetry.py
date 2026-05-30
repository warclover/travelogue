"""Studio / trip telemetry summary tests."""

from __future__ import annotations

from travelogue.web.studio_entry import build_entry
from travelogue.web.studio_telemetry import (
    build_pipeline_telemetry_summary,
    format_telemetry_lines,
)


def test_build_pipeline_telemetry_summary_from_trip() -> None:
    trip = {
        "pipeline": {
            "status": "rendered",
            "timings": {"ingestMs": 100.5, "renderMs": 200.0, "totalMs": 350.0},
        },
        "curation": {
            "clustering": {
                "embedStats": {"elapsedMs": 42.0, "batchSize": 16, "cacheHitRatio": 0.75},
                "embedSkipped": False,
                "vision": {"source": "clip"},
            }
        },
        "ingestStats": {"elapsedMs": {"decode": 10.0, "total": 99.0}},
    }
    summary = build_pipeline_telemetry_summary(trip)
    assert summary["pipelineStatus"] == "rendered"
    assert summary["timingsMs"]["totalMs"] == 350.0
    assert summary["embed"]["batchSize"] == 16
    assert summary["visionSource"] == "clip"
    assert summary["ingestElapsedMs"]["decode"] == 10.0


def test_format_telemetry_lines() -> None:
    lines = format_telemetry_lines(
        {
            "pipelineStatus": "rendered",
            "timingsMs": {"totalMs": 100.0},
            "embed": {"elapsedMs": 5.0},
        }
    )
    assert any("pipeline.status=" in line for line in lines)
    assert any("totalMs=" in line for line in lines)


def test_build_entry_includes_telemetry() -> None:
    trip = {
        "meta": {"title": "测试"},
        "chapters": [],
        "assets": [],
        "pipeline": {"status": "structure_draft", "timings": {"ingestMs": 1.0}},
    }
    entry = build_entry(trip, "demo")
    assert "telemetry" in entry
    assert entry["telemetry"]["timingsMs"]["ingestMs"] == 1.0
