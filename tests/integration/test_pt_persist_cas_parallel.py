"""AC-ARC-02-parallel · ingest persist_every_n × concurrent HTTP intent PATCH."""

from __future__ import annotations

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from PIL import Image

from travelogue.config import AppConfig, GeocodeConfig, IngestConfig, PipelineConfig
from travelogue.media.ingest import ingest_into_trip
from travelogue.media.ingest_persist import make_ingest_merge_mutator
from travelogue.services.trip import TripConflictError, TripSaveError, TripService, apply_intent
from travelogue.services.trip_factory import create_trip

pytestmark = pytest.mark.integration


def _album(tmp_path: Path, n: int = 8) -> Path:
    album = tmp_path / "album"
    album.mkdir()
    base_t = 1_700_000_000.0
    for i in range(n):
        Image.new("RGB", (800, 1000), (20 + i * 12, 40, 60)).save(
            album / f"p{i:02d}.jpg", quality=90
        )
        ts = base_t + i * 90
        os.utime(album / f"p{i:02d}.jpg", (ts, ts))
    return album


def test_ac_arc_02_parallel_intent_survives_ingest_persist(tmp_path: Path) -> None:
    """Import with persist_every_n=2 interleaved with HTTP intent PATCH.

    Expectation: final trip keeps HTTP intent title/places; assets complete.
    """
    album = _album(tmp_path, 8)
    trips = tmp_path / "trips"
    trip_json = create_trip("pt-cas", trips, title="初始")
    trip_dir = trip_json.parent
    svc = TripService()
    trip = svc.load(trip_json)
    apply_intent(trip, title="初始", places=["京都"], places_user_set=True)

    def seed(t: dict) -> None:
        t["intent"] = dict(trip.get("intent") or {})
        if "userNotes" in trip:
            t["userNotes"] = trip["userNotes"]
        meta = t.setdefault("meta", {})
        mem_meta = trip.get("meta") or {}
        for k in ("title", "places"):
            if k in mem_meta:
                meta[k] = mem_meta[k]

    svc.update(trip_json, seed)

    cfg = AppConfig(
        pipeline=PipelineConfig(
            parallel_ingest=True,
            parallel_ingest_min_photos=2,
            parallel_ingest_workers=2,
            persist_every_n=2,
        ),
        ingest=IngestConfig(webp_widths=(640,), generate_crops=False, detect_faces=False),
        geocode=GeocodeConfig(enabled=False),
    )

    stop = threading.Event()
    patch_ok = {"n": 0}
    patch_err = {"n": 0}

    def http_patch_intent() -> None:
        local = TripService()
        while not stop.is_set():
            try:

                def mutator(disk: dict) -> None:
                    apply_intent(
                        disk,
                        title="HTTP补丁标题",
                        places=["大阪"],
                        places_user_set=True,
                        user_notes="并发笔记",
                    )

                local.update(trip_json, mutator, max_retries=8)
                patch_ok["n"] += 1
            except (TripConflictError, TripSaveError):
                patch_err["n"] += 1
            time.sleep(0.01)

    def on_persist() -> None:
        # Mimic Studio mid-ingest persist (incremental merge, no revision bump).
        svc.update(
            trip_json,
            make_ingest_merge_mutator(trip),
            bump_revision=False,
            max_retries=8,
        )

    with ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(http_patch_intent)
        try:
            result = ingest_into_trip(
                trip,
                trip_dir,
                from_dir=album,
                dedupe=True,
                app_cfg=cfg,
                resume_ingest=False,
                min_assets=1,
                on_persist=on_persist,
            )
        finally:
            stop.set()
            fut.result(timeout=10)

    # Final stage-end style merge (same as tightened studio persist).
    from travelogue.media.ingest_persist import make_pipeline_persist_mutator

    svc.update(trip_json, make_pipeline_persist_mutator(trip), max_retries=8)
    loaded = svc.load(trip_json)

    assert result.added >= 1
    assert len(loaded.get("assets") or []) >= 1
    intent = loaded.get("intent") or {}
    assert intent.get("title") == "HTTP补丁标题", intent
    assert "大阪" in (intent.get("places") or [])
    assert loaded.get("userNotes") == "并发笔记"
    assert patch_ok["n"] >= 1
