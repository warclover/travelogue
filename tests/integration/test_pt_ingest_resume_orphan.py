"""AC-PT-04 · resume / orphan provisional WebP cleanup."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest
from PIL import Image

from travelogue.config import AppConfig, IngestConfig, PipelineConfig
from travelogue.media.ingest import ingest_into_trip
from travelogue.media.ingest_checkpoint import checkpoint_path, save_ingest_checkpoint
from travelogue.media.ingest_worker import (
    WorkerIngestConfig,
    WorkerResult,
    cleanup_provisional_files,
    process_ingest_photo_worker,
)
from travelogue.services.trip_factory import create_trip

pytestmark = pytest.mark.integration


def _album(tmp_path: Path, n: int) -> Path:
    album = tmp_path / "album"
    album.mkdir(exist_ok=True)
    base_t = 1_700_000_000.0
    for i in range(n):
        Image.new("RGB", (720, 960), (15 + i * 18, 40, 70)).save(
            album / f"p{i:02d}.jpg", quality=90
        )
        os.utime(album / f"p{i:02d}.jpg", (base_t + i * 75, base_t + i * 75))
    return album


def test_cleanup_provisional_files_removes_orphan_webp(tmp_path: Path) -> None:
    photo = tmp_path / "src.jpg"
    Image.new("RGB", (640, 800), (1, 2, 3)).save(photo, quality=90)
    temp = tmp_path / "partial"
    temp.mkdir()
    cfg = WorkerIngestConfig(
        webp_widths=(640,),
        generate_crops=False,
        detect_faces=False,
        portrait_analyze=False,
        exif_camera=False,
    )
    result = process_ingest_photo_worker(
        index=0,
        source_path=str(photo),
        user_tier="material",
        provisional_id="prov-00000",
        temp_dir=str(temp),
        worker_cfg=cfg,
    )
    assert result.error is None
    assert result.provisional_files
    for p in result.provisional_files:
        assert Path(p).is_file()
    cleanup_provisional_files(result)
    for p in result.provisional_files:
        assert not Path(p).exists()
    if result.provisional_dir:
        assert not Path(result.provisional_dir).exists()


def test_discarded_worker_result_cleans_provisional(tmp_path: Path) -> None:
    """Simulate dedupe discard path leaving no orphan blobs."""
    prov = tmp_path / "prov-x"
    (prov / "assets").mkdir(parents=True)
    orphan = prov / "assets" / "prov-x-w640.webp"
    orphan.write_bytes(b"fake")
    result = WorkerResult(
        index=0,
        source_path=str(tmp_path / "a.jpg"),
        user_tier="material",
        provisional_id="prov-x",
        provisional_dir=str(prov),
        provisional_files=[str(orphan)],
    )
    cleanup_provisional_files(result)
    assert not orphan.exists()


def test_parallel_ingest_resume_no_duplicate_asset_ids(tmp_path: Path) -> None:
    album = _album(tmp_path, 6)
    trips = tmp_path / "trips"
    trip_json = create_trip("pt-resume", trips, title="resume")
    trip_dir = trip_json.parent
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

    # First pass: only half the album
    partial = tmp_path / "partial"
    partial.mkdir()
    for name in ("p00.jpg", "p01.jpg", "p02.jpg"):
        shutil.copy(album / name, partial / name)
    ingest_into_trip(
        trip,
        trip_dir,
        from_dir=partial,
        dedupe=False,
        app_cfg=cfg,
        resume_ingest=False,
        min_assets=0,
    )
    first_ids = [a["id"] for a in trip["assets"]]
    assert len(first_ids) == 3

    save_ingest_checkpoint(
        trip_dir,
        source_root=str(album.resolve()),
        processed_rel_paths=["p00.jpg", "p01.jpg", "p02.jpg"],
        total=6,
    )

    result = ingest_into_trip(
        trip,
        trip_dir,
        from_dir=album,
        dedupe=False,
        app_cfg=cfg,
        resume_ingest=True,
        min_assets=1,
    )
    ids = [a["id"] for a in trip["assets"]]
    assert len(ids) == len(set(ids)), "duplicate assetId after resume"
    assert len(ids) == 6
    assert result.stats.get("ingestSkippedCheckpoint") == 3
    assert not checkpoint_path(trip_dir).is_file()
    # No leftover provisional tree
    assert not (trip_dir / ".ingest-partial").exists() or not any(
        (trip_dir / ".ingest-partial").rglob("*")
    )
