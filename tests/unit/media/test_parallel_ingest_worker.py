"""WorkerResult in-process smoke (no ProcessPool)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from travelogue.media.ingest_worker import (
    WorkerIngestConfig,
    cleanup_provisional_files,
    process_ingest_photo_worker,
)


def test_worker_produces_provisional_blobs(tmp_path: Path) -> None:
    photo = tmp_path / "a.jpg"
    Image.new("RGB", (800, 1000), (12, 34, 56)).save(photo, quality=90)
    temp = tmp_path / "partial"
    temp.mkdir()
    cfg = WorkerIngestConfig(
        webp_widths=(800,),
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
    assert result.dhash
    assert result.provisional_source
    assert Path(result.provisional_source).is_file()
    assert result.provisional_files
    cleanup_provisional_files(result)
    assert not Path(result.provisional_source).exists()
