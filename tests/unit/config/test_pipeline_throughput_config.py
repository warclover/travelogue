"""Pipeline Throughput · config defaults (Phase A)."""

from __future__ import annotations

from travelogue.config import AppConfig, LlmConfig, PipelineConfig
from travelogue.config.misc import pipeline_from_dict


def test_pipeline_throughput_defaults_off() -> None:
    cfg = PipelineConfig()
    assert cfg.parallel_ingest is False
    assert cfg.parallel_ingest_workers == 0
    assert cfg.parallel_ingest_min_photos == 12
    assert cfg.persist_every_n == 8


def test_llm_narrate_concurrency_defaults() -> None:
    cfg = LlmConfig()
    assert cfg.narrate_concurrency == 1
    assert cfg.narrate_concurrency_backoff is True


def test_app_config_defaults_include_pt_keys() -> None:
    app = AppConfig()
    assert app.pipeline.parallel_ingest is False
    assert app.llm.narrate_concurrency == 1


def test_pipeline_from_dict_reads_pt_keys() -> None:
    cfg = pipeline_from_dict(
        {
            "parallelIngest": True,
            "parallelIngestWorkers": 3,
            "parallelIngestMinPhotos": 24,
            "persistEveryN": 2,
        }
    )
    assert cfg.parallel_ingest is True
    assert cfg.parallel_ingest_workers == 3
    assert cfg.parallel_ingest_min_photos == 24
    assert cfg.persist_every_n == 2
