"""Pipeline Throughput · parallel ingest short-circuit + serial parity."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from PIL import Image

from travelogue.config import AppConfig, IngestConfig, PipelineConfig
from travelogue.media.ingest import ingest_into_trip
from travelogue.media.ingest_parallel import resolve_parallel_ingest_plan
from travelogue.services.trip_factory import create_trip

pytestmark = pytest.mark.integration


def _album(tmp_path: Path, n: int, *, size: tuple[int, int] = (1200, 1600)) -> Path:
    album = tmp_path / "album"
    album.mkdir()
    base_t = 1_700_000_000.0
    for i in range(n):
        Image.new("RGB", size, (20 + i * 10, 40 + i * 8, 60 + i * 6)).save(
            album / f"p{i:02d}.jpg", quality=92
        )
        ts = base_t + i * 120
        os.utime(album / f"p{i:02d}.jpg", (ts, ts))
    return album


def _structure_fingerprint(trip: dict) -> dict:
    assets = trip.get("assets") or []
    return {
        "ids": [a.get("id") for a in assets],
        "takenAt": [a.get("takenAt") for a in assets],
        "burst": [a.get("burstGroupId") for a in assets],
        "dedupe": [a.get("dedupeGroupId") for a in assets],
        "contentSig": [a.get("contentSig") for a in assets],
    }


def test_resolve_parallel_short_circuit_min_photos() -> None:
    app = AppConfig(
        pipeline=PipelineConfig(parallel_ingest=True, parallel_ingest_min_photos=12, parallel_ingest_workers=4)
    )
    use, workers, fallback, downscaled = resolve_parallel_ingest_plan(app, photo_count=5)
    assert use is False
    assert workers == 1
    assert fallback is True
    assert downscaled is False


def test_resolve_parallel_short_circuit_workers_one() -> None:
    app = AppConfig(
        pipeline=PipelineConfig(parallel_ingest=True, parallel_ingest_min_photos=2, parallel_ingest_workers=1)
    )
    use, workers, fallback, downscaled = resolve_parallel_ingest_plan(app, photo_count=20)
    assert use is False
    assert workers == 1
    # workers=1 is an explicit serial choice, not a parallel→serial fallback.
    assert fallback is False
    assert downscaled is False


def test_parallel_ingest_false_uses_serial_path(tmp_path: Path) -> None:
    """AC-PT-01 direction: default/off path remains serial (no ingestWorkers>1)."""
    trips = tmp_path / "trips"
    trip_json = create_trip("pt-serial", trips, title="serial")
    trip_dir = trips / "pt-serial"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    album = _album(tmp_path, 4)
    cfg = AppConfig(
        pipeline=PipelineConfig(parallel_ingest=False),
        ingest=IngestConfig(webp_widths=(800,), generate_crops=False, detect_faces=False),
    )
    result = ingest_into_trip(
        trip,
        trip_dir,
        from_dir=album,
        dedupe=True,
        app_cfg=cfg,
        resume_ingest=False,
        min_assets=1,
    )
    assert result.added >= 1
    assert trip["assets"]
    assert result.stats.get("ingestWorkers", 1) == 1


def test_parallel_ingest_min_photos_short_circuit(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("pt-min", trips, title="min")
    trip_dir = trips / "pt-min"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    album = _album(tmp_path, 3)
    cfg = AppConfig(
        pipeline=PipelineConfig(
            parallel_ingest=True,
            parallel_ingest_min_photos=12,
            parallel_ingest_workers=2,
        ),
        ingest=IngestConfig(webp_widths=(800,), generate_crops=False, detect_faces=False),
    )
    result = ingest_into_trip(
        trip,
        trip_dir,
        from_dir=album,
        dedupe=True,
        app_cfg=cfg,
        resume_ingest=False,
        min_assets=1,
    )
    assert result.stats.get("ingestWorkers", 1) == 1


def test_parallel_vs_serial_structure_parity(tmp_path: Path) -> None:
    """AC-PT-03 direction: same album → same assetId / takenAt / burst / dedupe ids."""
    album = _album(tmp_path, 6)

    def _run(*, parallel: bool, slug: str) -> tuple[dict, dict]:
        trips = tmp_path / f"trips-{slug}"
        trip_json = create_trip(slug, trips, title=slug)
        trip_dir = trips / slug
        trip = json.loads(trip_json.read_text(encoding="utf-8"))
        cfg = AppConfig(
            pipeline=PipelineConfig(
                parallel_ingest=parallel,
                parallel_ingest_min_photos=2,
                parallel_ingest_workers=2 if parallel else 0,
                persist_every_n=2,
            ),
            ingest=IngestConfig(
                webp_widths=(800,),
                generate_crops=False,
                detect_faces=False,
                dedupe_burst=True,
                dedupe_phash=True,
            ),
        )
        offered: list[str] = []

        def on_asset_added(entry: dict) -> None:
            offered.append(str(entry.get("id")))

        result = ingest_into_trip(
            trip,
            trip_dir,
            from_dir=album,
            dedupe=True,
            app_cfg=cfg,
            resume_ingest=False,
            min_assets=1,
            on_asset_added=on_asset_added,
        )
        trip["_offered"] = offered
        return trip, result.stats

    serial, _ = _run(parallel=False, slug="pt-off")
    parallel, pstats = _run(parallel=True, slug="pt-on")
    assert _structure_fingerprint(serial) == _structure_fingerprint(parallel)
    # D-PT-12: offer happens per kept asset (same count as assets)
    assert serial["_offered"] == [a["id"] for a in serial["assets"]]
    assert parallel["_offered"] == [a["id"] for a in parallel["assets"]]
    assert pstats.get("ingestWorkers", 1) >= 2
    assert pstats.get("ingestParallelFallback") is False