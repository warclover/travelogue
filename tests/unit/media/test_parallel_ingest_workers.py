"""PRD-PIPELINE-PERF-V1 · R1.2 / MF-05: auto workers + memory cap."""

from __future__ import annotations

from unittest.mock import patch

from travelogue.config import AppConfig, PipelineConfig
from travelogue.media.ingest_parallel import (
    resolve_auto_ingest_workers,
    resolve_parallel_ingest_plan,
    workers_memory_cap,
)


def test_workers_memory_cap_by_long_edge() -> None:
    assert workers_memory_cap(median_long_edge_px=None) == 10
    assert workers_memory_cap(median_long_edge_px=8000) == 4
    assert workers_memory_cap(median_long_edge_px=5500) == 6
    assert workers_memory_cap(median_long_edge_px=4000) == 8
    assert workers_memory_cap(median_long_edge_px=2000) == 10


@patch("travelogue.media.ingest_parallel.os.cpu_count", return_value=18)
def test_auto_workers_cpu18_is_nine(_cpu) -> None:
    workers, downscaled = resolve_auto_ingest_workers()
    assert workers == 9  # max(2, min(18//2, 10))
    assert downscaled is False


@patch("travelogue.media.ingest_parallel.os.cpu_count", return_value=18)
def test_auto_workers_downscales_for_36mp(_cpu) -> None:
    workers, downscaled = resolve_auto_ingest_workers(median_long_edge_px=7360)
    assert workers == 4
    assert downscaled is True


@patch("travelogue.media.ingest_parallel.os.cpu_count", return_value=18)
def test_resolve_plan_auto_workers(_cpu) -> None:
    app = AppConfig(
        pipeline=PipelineConfig(
            parallel_ingest=True,
            parallel_ingest_workers=0,
            parallel_ingest_min_photos=12,
        )
    )
    use, workers, fallback, downscaled = resolve_parallel_ingest_plan(
        app, photo_count=24
    )
    assert use is True
    assert workers == 9
    assert fallback is False
    assert downscaled is False
