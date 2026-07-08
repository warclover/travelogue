"""M-B3 · pipeline.orchestration legacy vs unified."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from tests.studio_test_helpers import make_test_album
from travelogue.config import AppConfig, ClusteringConfig, PipelineConfig, VisionConfig
from travelogue.web.studio_pipeline import (
    _resolve_pipeline_orchestration,
    run_studio_pipeline,
)


def test_resolve_pipeline_orchestration_defaults_unified() -> None:
    cfg = AppConfig()
    assert _resolve_pipeline_orchestration(cfg) == "unified"


def test_resolve_pipeline_orchestration_legacy() -> None:
    cfg = AppConfig(pipeline=PipelineConfig(orchestration="legacy"))
    assert _resolve_pipeline_orchestration(cfg) == "legacy"


def test_legacy_and_unified_produce_same_trip_shape(tmp_path: Path) -> None:
    from scripts.arch_equivalence_check import diff_normalized, normalize_trip

    album = make_test_album(tmp_path, 6)
    base_cfg = AppConfig(
        clustering=ClusteringConfig(enabled="false"),
        vision=VisionConfig(enabled="false"),
        pipeline=PipelineConfig(parallel_embed=False, orchestration="legacy"),
    )
    legacy_cfg = replace(base_cfg, pipeline=replace(base_cfg.pipeline, orchestration="legacy"))
    unified_cfg = replace(base_cfg, pipeline=replace(base_cfg.pipeline, orchestration="unified"))

    legacy = run_studio_pipeline(
        album,
        trips_dir=tmp_path / "legacy-trips",
        dedupe=False,
        app_config=legacy_cfg,
    )
    unified = run_studio_pipeline(
        album,
        trips_dir=tmp_path / "unified-trips",
        dedupe=False,
        app_config=unified_cfg,
    )

    trip_legacy = normalize_trip(json.loads(legacy.trip_json.read_text(encoding="utf-8")))
    trip_unified = normalize_trip(json.loads(unified.trip_json.read_text(encoding="utf-8")))
    assert not diff_normalized(trip_legacy, trip_unified)
    assert legacy.photo_count == unified.photo_count
    assert legacy.tier_mode == unified.tier_mode
