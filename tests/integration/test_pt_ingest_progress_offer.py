"""AC-PT-05 progress monotonicity · AC-PT-12 offer + L-embed NR profile."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from travelogue.config import AppConfig, IngestConfig, PipelineConfig, VisionConfig
from travelogue.media.ingest import ingest_into_trip
from travelogue.services.trip_factory import create_trip
from travelogue.vision.clip_encoder import _resolve_asset_path

pytestmark = pytest.mark.integration


def _album(tmp_path: Path, n: int = 6) -> Path:
    album = tmp_path / "album"
    album.mkdir()
    base_t = 1_700_000_000.0
    for i in range(n):
        img = Image.new("RGB", (900, 1200), (20 + i * 15, 50, 80))
        draw = ImageDraw.Draw(img)
        draw.rectangle((50 + i * 20, 80, 400, 600), fill=(180, 40 + i * 10, 40))
        path = album / f"p{i:02d}.jpg"
        img.save(path, quality=92)
        os.utime(path, (base_t + i * 180, base_t + i * 180))
    return album


def _cfg(*, parallel: bool) -> AppConfig:
    return AppConfig(
        pipeline=PipelineConfig(
            parallel_ingest=parallel,
            parallel_ingest_min_photos=2,
            parallel_ingest_workers=2 if parallel else 1,
        ),
        ingest=IngestConfig(webp_widths=(640,), generate_crops=False, detect_faces=False),
        vision=VisionConfig(enabled="false", prefer_web_derivative=False),
    )


def test_ac_pt_05_progress_completed_count_monotonic(tmp_path: Path) -> None:
    album = _album(tmp_path, 6)
    trips = tmp_path / "trips"
    trip_json = create_trip("pt-progress", trips, title="progress")
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    samples: list[tuple[int, int]] = []

    def on_progress(done: int, total: int) -> None:
        samples.append((int(done), int(total)))

    ingest_into_trip(
        trip,
        trip_json.parent,
        from_dir=album,
        dedupe=False,
        app_cfg=_cfg(parallel=True),
        resume_ingest=False,
        min_assets=1,
        on_progress=on_progress,
    )
    assert samples, "expected on_progress callbacks"
    totals = {t for _, t in samples}
    assert len(totals) == 1
    total = next(iter(totals))
    assert total == 6
    prev = 0
    for done, _ in samples:
        assert done >= prev
        assert done <= total
        prev = done
    assert samples[-1][0] == total


def test_ac_pt_12_offer_per_asset_ordered(tmp_path: Path) -> None:
    album = _album(tmp_path, 5)
    trips = tmp_path / "trips"
    trip_json = create_trip("pt-offer", trips, title="offer")
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    offered: list[str] = []

    def on_asset_added(entry: dict) -> None:
        offered.append(str(entry.get("id")))

    ingest_into_trip(
        trip,
        trip_json.parent,
        from_dir=album,
        dedupe=False,
        app_cfg=_cfg(parallel=True),
        resume_ingest=False,
        min_assets=1,
        on_asset_added=on_asset_added,
    )
    final_ids = [a["id"] for a in trip["assets"]]
    assert offered == final_ids
    assert len(offered) == len(set(offered))


def test_ac_pt_12_l_embed_prefer_web_false_subject_class_parity(tmp_path: Path) -> None:
    """NR profile: prefer_web_derivative=false → source path + label agree serial/parallel.

    Labels are derived from source JPEG bytes (not WebP) so CI does not need CLIP,
    matching L-embed intent under D-PT-07.
    """
    album = _album(tmp_path, 4)

    def _ingest_and_label(*, parallel: bool, slug: str) -> list[str]:
        trips = tmp_path / f"trips-{slug}"
        trip_json = create_trip(slug, trips, title=slug)
        trip_dir = trip_json.parent
        trip = json.loads(trip_json.read_text(encoding="utf-8"))
        ingest_into_trip(
            trip,
            trip_dir,
            from_dir=album,
            dedupe=False,
            app_cfg=_cfg(parallel=parallel),
            resume_ingest=False,
            min_assets=1,
        )
        labels: list[str] = []
        for asset in trip["assets"]:
            path, used_web = _resolve_asset_path(
                asset, trip_dir, prefer_web_derivative=False
            )
            assert path is not None and path.is_file(), asset.get("id")
            assert used_web is False
            assert "source" in path.parts
            digest = hashlib.md5(path.read_bytes()).hexdigest()[:10]
            asset["subjectClass"] = f"src-{digest}"
            labels.append(asset["subjectClass"])
        return labels

    serial_classes = _ingest_and_label(parallel=False, slug="embed-off")
    parallel_classes = _ingest_and_label(parallel=True, slug="embed-on")
    assert serial_classes == parallel_classes
    assert all(serial_classes)
