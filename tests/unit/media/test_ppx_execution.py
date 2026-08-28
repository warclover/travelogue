"""PRD-PIPELINE-PERF-EXECUTION-V1 · AC-PPX-02/03/06 structured ingest."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from travelogue.config import AppConfig, IngestConfig, PipelineConfig
from travelogue.demo.build import DemoError
from travelogue.media.ingest import ingest_into_trip
from travelogue.services.trip_factory import create_trip


def _parallel_cfg(*, min_photos: int = 2, workers: int = 2) -> AppConfig:
    return AppConfig(
        pipeline=PipelineConfig(
            parallel_ingest=True,
            parallel_ingest_min_photos=min_photos,
            parallel_ingest_workers=workers,
            deferred_derivatives=True,
        ),
        ingest=IngestConfig(
            webp_widths=(800, 1600, 2400),
            webp_ingest_widths=(800, 1600),
            detect_faces=False,
            generate_crops=False,
            webp_method=0,
        ),
    )


def _album(tmp_path: Path, n: int, *, size: tuple[int, int] = (640, 480)) -> Path:
    album = tmp_path / "album"
    album.mkdir()
    for i in range(n):
        Image.new("RGB", size, (20 * i, 40, 80)).save(album / f"p{i}.jpg", quality=90)
    return album


def test_pool_start_failed_writes_reason(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-PPX-02 · pool start failure is structured, not a silent False."""

    def _boom(*_a, **_k):
        raise OSError("cannot spawn")

    monkeypatch.setattr(
        "travelogue.media.ingest_parallel.ProcessPoolExecutor", _boom
    )
    album = _album(tmp_path, 2)
    trips = tmp_path / "trips"
    trip_json = create_trip("ppx-pool", trips, title="ppx")
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    result = ingest_into_trip(
        trip,
        trip_json.parent,
        from_dir=album,
        app_cfg=_parallel_cfg(),
        min_assets=1,
        dedupe=False,
    )
    assert result.stats.get("ingestParallelFallback") is True
    assert result.stats.get("ingestParallelFallbackReason") == "pool_start_failed"
    assert result.stats.get("ingestWorkers") == 1


def test_cancel_cleans_ingest_partial(tmp_path: Path) -> None:
    """AC-PPX-03 · cancel must not leave .ingest-partial."""
    album = _album(tmp_path, 2)
    trips = tmp_path / "trips"
    trip_json = create_trip("ppx-cancel", trips, title="ppx")
    trip = json.loads(trip_json.read_text(encoding="utf-8"))

    def _cancel(_done: int, _total: int) -> None:
        raise DemoError("E_STUDIO_CANCELLED", "cancelled")

    with pytest.raises(DemoError):
        ingest_into_trip(
            trip,
            trip_json.parent,
            from_dir=album,
            app_cfg=_parallel_cfg(),
            min_assets=1,
            dedupe=False,
            on_progress=_cancel,
        )
    assert not (trip_json.parent / ".ingest-partial").exists()


def test_parallel_ingest_writes_first_progress_ms(tmp_path: Path) -> None:
    """AC-PPX-06 · firstProgressMs is written without waiting for the full batch."""
    album = _album(tmp_path, 2)
    trips = tmp_path / "trips"
    trip_json = create_trip("ppx-fp", trips, title="ppx")
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    result = ingest_into_trip(
        trip,
        trip_json.parent,
        from_dir=album,
        app_cfg=_parallel_cfg(),
        min_assets=1,
        dedupe=False,
    )
    assert result.stats.get("ingestParallelFallback") is not True
    assert result.stats.get("ingestWorkers", 1) >= 2
    assert result.stats.get("ingestFirstProgressMs") is not None
    assert float(result.stats["ingestFirstProgressMs"]) >= 0
    assert float(result.stats.get("ingestPoolSpawnMs") or 0) >= 0
