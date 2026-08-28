"""PRD-PIPELINE-PERF-V1 · MF-07: flush must not wipe ingestWorkers."""

from __future__ import annotations

from travelogue.domain.pipeline_view import (
    absorb_pipeline_timing_keys,
    set_pipeline_timings,
)


def test_absorb_pipeline_timing_keys_preserves_ingest_workers() -> None:
    trip = {
        "pipeline": {
            "timings": {
                "ingestWorkers": 4.0,
                "ingestParallelFallback": 0.0,
            }
        }
    }
    local = {"ingestMs": 12000.0}
    absorb_pipeline_timing_keys(trip, local)
    local["totalMs"] = 12001.0
    set_pipeline_timings(trip, local)
    timings = trip["pipeline"]["timings"]
    assert timings["ingestWorkers"] == 4.0
    assert timings["ingestParallelFallback"] == 0.0
    assert timings["ingestMs"] == 12000.0
    assert timings["totalMs"] == 12001.0


def test_absorb_does_not_overwrite_local_stage_keys() -> None:
    trip = {"pipeline": {"timings": {"ingestMs": 1.0, "ingestWorkers": 2.0}}}
    local = {"ingestMs": 99.0}
    absorb_pipeline_timing_keys(trip, local)
    assert local["ingestMs"] == 99.0
    assert local["ingestWorkers"] == 2.0


def test_absorb_preserves_string_reason_keys() -> None:
    trip = {
        "pipeline": {
            "timings": {
                "ingestParallelFallbackReason": "pool_start_failed",
                "ingestWorkersDownscaleReason": "memory_cap_ram",
            }
        }
    }
    local: dict = {"ingestMs": 10.0}
    absorb_pipeline_timing_keys(trip, local)
    assert local["ingestParallelFallbackReason"] == "pool_start_failed"
    assert local["ingestWorkersDownscaleReason"] == "memory_cap_ram"


def test_flush_pattern_without_absorb_wipes_workers() -> None:
    """Document the pre-fix failure mode (regression guard)."""
    trip = {"pipeline": {"timings": {"ingestWorkers": 4.0}}}
    local = {"ingestMs": 100.0}
    # Old bug: set without absorb
    set_pipeline_timings(trip, {**local, "totalMs": 101.0})
    assert "ingestWorkers" not in trip["pipeline"]["timings"]
