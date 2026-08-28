"""AC-PPX-01 · Studio import child must actually run parallel ingest.

Must go through ``ImportSubprocess.start()``. Direct ``ingest_into_trip``
does not cover the daemon/ProcessPool nest (PRD-PIPELINE-PERF-EXECUTION-V1).
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest
from PIL import Image

from travelogue.web.studio_subprocess import ImportSubprocess

pytestmark = [pytest.mark.integration]

_PHOTO_COUNT = 12
_JOIN_S = 120.0


def _write_kill_config(path: Path, *, trips_dir: Path) -> None:
    path.write_text(
        "\n".join(
            [
                f"trips_dir: {trips_dir.as_posix()}",
                "vision:",
                "  enabled: false",
                "  preload_on_folder_pick: false",
                "pipeline:",
                "  parallel_ingest: true",
                "  parallel_ingest_workers: 2",
                "  parallel_ingest_min_photos: 12",
                "  parallel_embed: false",
                "  deferred_derivatives: true",
                "ingest:",
                "  detect_faces: false",
                "  generate_crops: false",
                "  portrait_analyze: false",
                "  webp_method: 0",
                "  webp_widths: [320]",
                "  webp_ingest_widths: [320]",
                "  min_edge_px: 320",
                "aesthetic:",
                "  enabled: false",
                "  ml_calibrate: false",
                "  warm_learned_on_ingest: false",
                "llm:",
                "  provider: stub",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_album(album: Path, n: int) -> None:
    album.mkdir(parents=True, exist_ok=True)
    base_t = 1_700_000_000.0
    for i in range(n):
        path = album / f"p{i:02d}.jpg"
        Image.new("RGB", (320, 400), (10 + i * 17, 40 + i * 9, 80 + i * 5)).save(
            path, quality=85
        )
        os.utime(path, (base_t + i * 60, base_t + i * 60))


def _read_ingest_timings(trip_json: Path) -> dict | None:
    if not trip_json.is_file():
        return None
    try:
        trip = json.loads(trip_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    timings = (trip.get("pipeline") or {}).get("timings") or {}
    if "ingestWorkers" not in timings and "ingestParallelFallback" not in timings:
        return None
    return timings


def _stop_handle(handle: ImportSubprocess) -> None:
    if handle.alive:
        handle.cancel()
    handle.join(timeout=8)


def test_import_subprocess_start_runs_parallel_ingest(tmp_path: Path) -> None:
    album = tmp_path / "album"
    trips = tmp_path / "trips"
    trips.mkdir()
    _write_album(album, _PHOTO_COUNT)
    cfg_path = tmp_path / "ppx-kill-config.yaml"
    _write_kill_config(cfg_path, trips_dir=trips)

    trip_id = "ppx-spawn-kill"
    trip_json = trips / trip_id / "trip.json"
    handle = ImportSubprocess(
        {
            "albumPath": str(album),
            "tripsDir": str(trips),
            "tripId": trip_id,
            "title": "PPX 杀伤",
            "place": "测试",
            "host": "127.0.0.1",
            "port": 8766,
            "configPath": str(cfg_path),
            "dedupe": False,
            "forceStub": True,
            "photoCullEnabled": False,
            "keepNearDuplicates": True,
            "stopAfter": "structure",
        }
    )
    handle.start()
    deadline = time.monotonic() + _JOIN_S
    last_event: dict | None = None
    timings: dict | None = None
    try:
        while time.monotonic() < deadline:
            for event in handle.drain():
                last_event = event
                if event.get("type") == "error":
                    diag = tmp_path / "studio-import-error.log"
                    detail = (
                        diag.read_text(encoding="utf-8")[-4000:]
                        if diag.is_file()
                        else ""
                    )
                    pytest.fail(
                        "import child failed before ingest telemetry: "
                        f"{event.get('code')} {event.get('message')}\n{detail}"
                    )
                result = event.get("result") if event.get("type") == "done" else None
                if isinstance(result, dict) and result.get("tripId"):
                    alt = trips / str(result["tripId"]) / "trip.json"
                    if alt.is_file():
                        trip_json = alt
            timings = _read_ingest_timings(trip_json)
            if timings is not None:
                break
            if not handle.alive:
                leftover = handle.drain()
                if leftover:
                    last_event = leftover[-1]
                timings = _read_ingest_timings(trip_json)
                break
            time.sleep(0.1)
    finally:
        _stop_handle(handle)

    if timings is None:
        pytest.fail(
            "ImportSubprocess.start() produced no ingestWorkers telemetry; "
            f"last_event={last_event!r} trip_json={trip_json}"
        )

    workers = int(timings.get("ingestWorkers") or 0)
    fallback = int(timings.get("ingestParallelFallback") or 0)
    assert workers > 1, (
        "Studio ImportSubprocess.start() must run parallel ingest; "
        f"got ingestWorkers={workers} fallback={fallback} timings={timings!r} "
        "(PRD-PIPELINE-PERF-EXECUTION-V1 · AC-PPX-01)"
    )
    assert fallback == 0, (
        "ingestParallelFallback must be 0 when parallel ingest is reachable; "
        f"got ingestWorkers={workers} fallback={fallback} timings={timings!r}"
    )
