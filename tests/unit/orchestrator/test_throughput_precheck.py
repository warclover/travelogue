"""M3 · throughput precheck warnings."""

from __future__ import annotations

import logging

from travelogue.config import AppConfig, ClusteringConfig, PipelineConfig, VisionConfig
from travelogue.orchestrator.studio_profile import StudioProfile
from travelogue.orchestrator.throughput_precheck import (
    collect_throughput_precheck_warnings,
    emit_throughput_precheck_warnings,
)


def test_precheck_warns_when_vision_on_but_parallel_embed_off() -> None:
    cfg = AppConfig(
        vision=VisionConfig(enabled="auto"),
        pipeline=PipelineConfig(parallel_embed=False),
    )
    warns = collect_throughput_precheck_warnings(cfg)
    assert any("parallel_embed=false" in w for w in warns)


def test_precheck_silent_on_aligned_fast_path() -> None:
    cfg = AppConfig(
        vision=VisionConfig(enabled="auto", session_singleton=True),
        pipeline=PipelineConfig(parallel_embed=True),
        clustering=ClusteringConfig(force_recluster=False),
    )
    # layout_scoring defaults already skip_duplicate_signatures=True
    assert collect_throughput_precheck_warnings(cfg) == []


def test_precheck_warns_on_force_recluster() -> None:
    cfg = AppConfig(
        vision=VisionConfig(enabled="false"),
        clustering=ClusteringConfig(force_recluster=True),
    )
    warns = collect_throughput_precheck_warnings(cfg)
    assert any("force_recluster" in w for w in warns)


def test_emit_logs_warnings(caplog) -> None:
    cfg = AppConfig(
        vision=VisionConfig(enabled="true"),
        pipeline=PipelineConfig(parallel_embed=False),
    )
    with caplog.at_level(logging.WARNING):
        out = emit_throughput_precheck_warnings(cfg)
    assert out
    assert any("parallel_embed" in r.message for r in caplog.records)


def test_studio_default_profile_keeps_parallel_embed_intent() -> None:
    """Studio profile still requests parallel_embed; product PT ingest default stays off."""
    profile = StudioProfile.studio_default()
    assert profile.ingest.use_parallel_embed is True
    assert profile.ingest.resume_ingest is True
    from travelogue.config import PipelineConfig

    assert PipelineConfig().parallel_ingest is False
