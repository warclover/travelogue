"""PT-A1…A4 algorithm fixtures · serial vs parallel structure / cull / focal."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.fixtures.pt_ingest.builders import (
    write_burst_album,
    write_cull_album,
    write_face_album,
    write_phash_album,
)
from travelogue.config import AppConfig, CullConfig, IngestConfig, PipelineConfig
from travelogue.curation.photo_cull import CULL_EXCLUDE_REASONS
from travelogue.media.ingest import ingest_into_trip
from travelogue.services.trip_factory import create_trip

pytestmark = pytest.mark.integration


def _structure(trip: dict) -> dict:
    assets = trip.get("assets") or []
    return {
        "ids": [a.get("id") for a in assets],
        "burst": [a.get("burstGroupId") for a in assets],
        "dedupe": [a.get("dedupeGroupId") for a in assets],
        "takenAt": [a.get("takenAt") for a in assets],
        "focal": [
            (round(float((a.get("focalPoint") or {}).get("x", 0.5)), 4),
             round(float((a.get("focalPoint") or {}).get("y", 0.45)), 4))
            for a in assets
        ],
        "faceCount": [int((a.get("quality") or {}).get("faceCount") or 0) for a in assets],
    }


def _cull_fingerprint(trip: dict) -> dict:
    assets = trip.get("assets") or []
    excluded = sorted(
        a["id"]
        for a in assets
        if not a.get("layoutEligible", True)
        and str(a.get("excludeReason") or "") in CULL_EXCLUDE_REASONS
    )
    curation = trip.get("curation") or {}
    return {
        "excluded": excluded,
        "excludedByCull": int((curation.get("cullSummary") or {}).get("excludedByCull") or 0),
        "eligible": sorted(a["id"] for a in assets if a.get("layoutEligible", True)),
    }


def _run(
    tmp_path: Path,
    album: Path,
    *,
    parallel: bool,
    slug: str,
    detect_faces: bool = False,
    cull: CullConfig | None = None,
    n_workers: int = 2,
) -> dict:
    trips = tmp_path / f"trips-{slug}"
    trip_json = create_trip(slug, trips, title=slug)
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    cfg = AppConfig(
        pipeline=PipelineConfig(
            parallel_ingest=parallel,
            parallel_ingest_min_photos=2,
            parallel_ingest_workers=n_workers if parallel else 1,
        ),
        ingest=IngestConfig(
            webp_widths=(640,),
            generate_crops=False,
            detect_faces=detect_faces,
            dedupe_burst=True,
            dedupe_phash=True,
            burst_seconds=3.0,
        ),
        cull=cull or CullConfig(enabled=False),
    )
    ingest_into_trip(
        trip,
        trip_json.parent,
        from_dir=album,
        dedupe=True,
        app_cfg=cfg,
        resume_ingest=False,
        min_assets=1,
    )
    return trip


def test_pt_a1_burst_keep_sharper_parity(tmp_path: Path) -> None:
    album = write_burst_album(tmp_path / "burst")
    serial = _run(tmp_path, album, parallel=False, slug="burst-off")
    parallel = _run(tmp_path, album, parallel=True, slug="burst-on")
    assert _structure(serial) == _structure(parallel)
    assert len(serial["assets"]) < 5


def test_pt_a2_phash_near_dup_parity(tmp_path: Path) -> None:
    album = write_phash_album(tmp_path / "phash")
    serial = _run(tmp_path, album, parallel=False, slug="phash-off")
    parallel = _run(tmp_path, album, parallel=True, slug="phash-on")
    assert _structure(serial) == _structure(parallel)
    assert len(serial["assets"]) == 2


def test_pt_a3_face_focal_parity(tmp_path: Path) -> None:
    """PT-A3: face/focal fields agree serial vs parallel (Haar optional)."""
    album = write_face_album(tmp_path / "face")
    serial = _run(tmp_path, album, parallel=False, slug="face-off", detect_faces=True)
    parallel = _run(tmp_path, album, parallel=True, slug="face-on", detect_faces=True)
    assert _structure(serial) == _structure(parallel)
    assert len(serial["assets"]) >= 1


def test_pt_a4_cull_global_parity(tmp_path: Path) -> None:
    """PT-A4: ≥30 photos → same cull exclude set serial vs parallel."""
    album = write_cull_album(tmp_path / "cull", n_good=28, n_flat=4)
    cull_cfg = CullConfig(
        enabled=True,
        min_keep=8,
        keep_ratio_floor=0.0,
        bucketed_blur_thresholds=True,
        bucketed_blur_min_samples=2,
        enable_cull_explain=True,
    )
    serial = _run(tmp_path, album, parallel=False, slug="cull-off", cull=cull_cfg)
    parallel = _run(
        tmp_path, album, parallel=True, slug="cull-on", cull=cull_cfg, n_workers=2
    )
    assert _structure(serial)["ids"] == _structure(parallel)["ids"]
    assert _cull_fingerprint(serial) == _cull_fingerprint(parallel)
    assert _cull_fingerprint(serial)["excludedByCull"] >= 1 or any(
        not a.get("layoutEligible", True) for a in serial["assets"]
    )
