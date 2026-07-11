"""Windows / spawn smoke for parallel ingest (nightly · blocks G1).

Runs on any OS; CI nightly-windows-pt.yml executes it on windows-latest.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from PIL import Image

from travelogue.config import AppConfig, IngestConfig, PipelineConfig
from travelogue.media.ingest import ingest_into_trip
from travelogue.services.trip_factory import create_trip

pytestmark = [pytest.mark.integration, pytest.mark.pt_windows_spawn]


def test_pt_ingest_process_pool_spawn_smoke(tmp_path: Path) -> None:
    album = tmp_path / "album"
    album.mkdir()
    base_t = 1_700_000_000.0
    for i in range(4):
        Image.new("RGB", (640, 800), (10 + i * 20, 30, 50)).save(album / f"p{i}.jpg", quality=90)
        os.utime(album / f"p{i}.jpg", (base_t + i * 60, base_t + i * 60))

    trips = tmp_path / "trips"
    trip_json = create_trip("pt-spawn", trips, title="spawn")
    trip_dir = trips / "pt-spawn"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    cfg = AppConfig(
        pipeline=PipelineConfig(
            parallel_ingest=True,
            parallel_ingest_min_photos=2,
            parallel_ingest_workers=2,
            persist_every_n=2,
        ),
        ingest=IngestConfig(webp_widths=(640,), generate_crops=False, detect_faces=False),
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
    assert len(trip["assets"]) >= 1
    # Either parallel workers ran, or fail-open serial — must not crash / corrupt.
    workers = result.stats.get("ingestWorkers", 1)
    assert workers >= 1
    timings = (trip.get("pipeline") or {}).get("timings") or {}
    if "ingestWorkers" in timings:
        assert timings["ingestWorkers"] >= 1
