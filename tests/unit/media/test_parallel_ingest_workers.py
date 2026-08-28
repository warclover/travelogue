"""PRD-PIPELINE-PERF-V1 · R1.2 / MF-05 + PPX D-PPX-07/08."""

from __future__ import annotations

from unittest.mock import patch

from travelogue.config import AppConfig, PipelineConfig
from travelogue.media.ingest_parallel import (
    resolve_auto_ingest_workers,
    resolve_parallel_ingest_plan,
    workers_memory_cap,
    workers_ram_cap,
)


def test_workers_memory_cap_by_long_edge() -> None:
    assert workers_memory_cap(median_long_edge_px=None) == 6
    assert workers_memory_cap(median_long_edge_px=8000) == 4
    assert workers_memory_cap(median_long_edge_px=5500) == 6
    assert workers_memory_cap(median_long_edge_px=4000) == 8
    assert workers_memory_cap(median_long_edge_px=2000) == 10


@patch("travelogue.media.ingest_parallel.available_ram_mb", return_value=32000)
@patch("travelogue.media.ingest_parallel.os.cpu_count", return_value=18)
def test_auto_workers_unknown_edge_caps_at_six(_cpu, _ram) -> None:
    workers, downscaled = resolve_auto_ingest_workers()
    assert workers == 6
    assert downscaled is True


@patch("travelogue.media.ingest_parallel.available_ram_mb", return_value=32000)
@patch("travelogue.media.ingest_parallel.os.cpu_count", return_value=18)
def test_auto_workers_cpu18_known_edge_is_nine(_cpu, _ram) -> None:
    workers, downscaled = resolve_auto_ingest_workers(median_long_edge_px=2000)
    assert workers == 9
    assert downscaled is False


@patch("travelogue.media.ingest_parallel.available_ram_mb", return_value=64000)
@patch("travelogue.media.ingest_parallel.os.cpu_count", return_value=18)
def test_auto_workers_downscales_for_36mp(_cpu, _ram) -> None:
    workers, downscaled = resolve_auto_ingest_workers(median_long_edge_px=7360)
    assert workers == 4
    assert downscaled is True


@patch("travelogue.media.ingest_parallel.available_ram_mb", return_value=32000)
@patch("travelogue.media.ingest_parallel.os.cpu_count", return_value=18)
def test_resolve_plan_auto_workers(_cpu, _ram) -> None:
    app = AppConfig(
        pipeline=PipelineConfig(
            parallel_ingest=True,
            parallel_ingest_workers=0,
            parallel_ingest_min_photos=12,
        )
    )
    use, workers, fallback, downscaled = resolve_parallel_ingest_plan(
        app, photo_count=24, median_long_edge_px=2000
    )
    assert use is True
    assert workers == 9
    assert fallback is False
    assert downscaled is False


@patch("travelogue.media.ingest_parallel.available_ram_mb", return_value=32000)
@patch("travelogue.media.ingest_parallel.os.cpu_count", return_value=18)
def test_resolve_plan_uses_scan_median_7360(_cpu, _ram) -> None:
    """AC-PPX-04 · 7360 median → workers ≤ 4."""
    app = AppConfig(
        pipeline=PipelineConfig(
            parallel_ingest=True,
            parallel_ingest_workers=10,
            parallel_ingest_min_photos=12,
        )
    )
    use, workers, fallback, downscaled = resolve_parallel_ingest_plan(
        app, photo_count=24, median_long_edge_px=7360
    )
    assert use is True
    assert workers <= 4
    assert fallback is False
    assert downscaled is True


def test_ram_budget_can_press_ten_lower() -> None:
    """AC-PPX-05 · RAM budget can push a 10-cap plan below 10."""
    cap = workers_ram_cap(median_long_edge_px=2000, available_mb=2048)
    assert cap < 10
    assert cap >= 1
