"""Cross-process trip.json CAS (AC-ARC-02)."""

from __future__ import annotations

import multiprocessing as mp
import sys
import time
from pathlib import Path

import pytest

from travelogue.services.trip import TripConflictError, TripSaveError, TripService, meta_revision


def _minimal_trip() -> dict:
    return {
        "version": "0.2",
        "tripId": "cross-proc",
        "templateId": "visual-journal",
        "exportLayout": "auto",
        "meta": {
            "title": "测试",
            "dateStart": "2025-01-01",
            "dateEnd": "2025-01-02",
            "places": ["测试"],
            "tone": "relaxed",
        },
        "assets": [],
        "chapters": [],
        "pipeline": {"status": "draft"},
        "createdAt": "2025-01-01T00:00:00Z",
        "updatedAt": "2025-01-01T00:00:00Z",
    }


def _worker(path_str: str, stop: mp.Event, errors: mp.Queue) -> None:
    svc = TripService()
    path = Path(path_str)
    seq = 0
    while not stop.is_set():
        try:

            def mutator(trip: dict) -> None:
                bucket = trip.setdefault("pipeline", {}).setdefault("ingestProgress", {})
                bucket[f"worker.{seq}"] = True

            svc.update(path, mutator, max_retries=5)
            seq += 1
        except (TripConflictError, TripSaveError):
            continue
        except Exception as exc:  # pragma: no cover - surfaced via queue
            errors.put(str(exc))
            return
        time.sleep(0.001)


@pytest.mark.integration
@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="Windows spawn CAS flake (PRD-ARCH-OPT-WS1-MERGE-FIX M-F4 · D-FIX-05); Linux CI covers AC-ARC-02",
)
def test_subprocess_worker_and_main_both_persist(tmp_path: Path) -> None:
    ctx = mp.get_context("spawn")
    trip_path = tmp_path / "trip.json"
    TripService().save(_minimal_trip(), trip_path)
    stop = ctx.Event()
    errors: mp.Queue = ctx.Queue()
    proc = ctx.Process(target=_worker, args=(str(trip_path), stop, errors))
    proc.start()
    svc = TripService()
    try:
        # Let the spawn worker land at least one CAS write before main floods.
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            progress = (svc.load(trip_path).get("pipeline") or {}).get("ingestProgress") or {}
            if any(str(k).startswith("worker.") for k in progress):
                break
            time.sleep(0.02)
        else:
            stop.set()
            proc.join(timeout=10)
            pytest.fail("worker process never persisted a trip update")

        for i in range(30):
            key = f"main.{i}"

            def mutator(trip: dict, marker: str = key) -> None:
                bucket = trip.setdefault("pipeline", {}).setdefault("ingestProgress", {})
                bucket[marker] = True

            try:
                svc.update(trip_path, mutator, max_retries=5)
            except (TripConflictError, TripSaveError):
                continue
            time.sleep(0.002)
    finally:
        stop.set()
        proc.join(timeout=10)
        assert proc.exitcode == 0

    assert errors.empty(), [errors.get() for _ in range(errors.qsize())]
    loaded = svc.load(trip_path)
    progress = (loaded.get("pipeline") or {}).get("ingestProgress") or {}
    worker_keys = [k for k in progress if str(k).startswith("worker.")]
    main_written = [k for k in progress if str(k).startswith("main.")]
    assert len(worker_keys) >= 3, progress
    assert len(main_written) >= 3, progress
    assert meta_revision(loaded) >= len(main_written) + len(worker_keys)
