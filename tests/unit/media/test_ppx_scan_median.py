"""PRD-PIPELINE-PERF-EXECUTION-V1 · AC-PPX-04 scan median into the plan."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from travelogue.config import AppConfig, IngestConfig, PipelineConfig
from travelogue.media.ingest import ingest_into_trip, scan_image_paths
from travelogue.media.user_tier import scan_tiered_image_paths
from travelogue.services.trip_factory import create_trip


def _parallel_cfg() -> AppConfig:
    return AppConfig(
        pipeline=PipelineConfig(
            parallel_ingest=True,
            parallel_ingest_min_photos=2,
            parallel_ingest_workers=2,
            deferred_derivatives=True,
        ),
        ingest=IngestConfig(
            webp_widths=(800, 1600),
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


def test_scan_image_paths_writes_median_long_edge(tmp_path: Path) -> None:
    album = tmp_path / "album"
    album.mkdir()
    Image.new("RGB", (800, 600), (10, 20, 30)).save(album / "a.jpg", quality=90)
    Image.new("RGB", (800, 600), (10, 20, 30)).save(album / "b.jpg", quality=90)
    Image.new("RGB", (1600, 900), (10, 20, 30)).save(album / "c.jpg", quality=90)
    _files, stats = scan_image_paths(album, max_photos=10, min_edge_px=10)
    assert stats.get("medianLongEdgePx") == 800


def test_tier_scan_writes_median_long_edge(tmp_path: Path) -> None:
    album = _album(tmp_path, 3, size=(1200, 800))
    _files, stats = scan_tiered_image_paths(
        featured_dir=None,
        material_dir=None,
        single_dir=album,
        max_photos=10,
        min_edge_px=10,
    )
    assert stats.get("medianLongEdgePx") == 1200


def test_ingest_records_scan_median_on_trip_stats(tmp_path: Path) -> None:
    import json

    album = _album(tmp_path, 2)
    trips = tmp_path / "trips"
    trip_json = create_trip("ppx-median", trips, title="ppx")
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    result = ingest_into_trip(
        trip,
        trip_json.parent,
        from_dir=album,
        app_cfg=_parallel_cfg(),
        min_assets=1,
        dedupe=False,
    )
    assert result.stats.get("medianLongEdgePx") == 640
    assert result.stats.get("ingestMedianLongEdgePx") == 640
