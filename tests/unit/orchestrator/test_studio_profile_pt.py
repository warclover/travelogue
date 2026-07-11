"""P1 · timings TypedDict + Studio profile PT defaults."""

from __future__ import annotations

from travelogue.config import PipelineConfig
from travelogue.orchestrator.studio_profile import StudioProfile
from travelogue.types.trip_telemetry import PipelineTimingsDict


def test_pipeline_timings_dict_includes_pt_fields() -> None:
    sample: PipelineTimingsDict = {
        "ingestMs": 1.0,
        "ingestWorkers": 2.0,
        "ingestParallelFallback": 0.0,
        "narrateConcurrency": 1.0,
        "narrateCacheHits": 0.0,
        "narrateCacheMisses": 3.0,
        "narrateProviderBackoffCount": 0.0,
    }
    assert sample["ingestWorkers"] == 2.0
    assert "narrateProviderBackoffCount" in sample


def test_studio_default_profile_keeps_p7_embed_not_pt_ingest() -> None:
    profile = StudioProfile.studio_default()
    assert profile.ingest.use_parallel_embed is True
    assert profile.ingest.resume_ingest is True
    # Product PT acceleration remains off at config defaults (G1 not flipped).
    assert PipelineConfig().parallel_ingest is False
