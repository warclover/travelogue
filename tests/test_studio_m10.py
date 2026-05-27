"""Studio cancel / export API (M10)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from travelogue.web.studio_jobs import get_job_store, reset_job_store
from travelogue.web.studio_pipeline import run_studio_pipeline
from travelogue.web.studio_trips import list_studio_trips, longshot_outputs_stale
from tests.test_studio_server import (
    _distinct_album,
    _free_port,
    _get_json,
    _post_json,
    _start_studio_server,
)


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


def test_studio_trips_includes_preview_path(tmp_path: Path) -> None:
    album = _distinct_album(tmp_path, 6)
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    result = run_studio_pipeline(album, trips_dir=trips_dir, dedupe=False)
    trips = list_studio_trips(trips_dir)
    assert trips
    row = trips[0]
    assert row["tripId"] == result.trip_id
    assert row.get("previewPath")
    assert Path(row["previewPath"]).is_file()


def test_longshot_stale_when_trip_newer(tmp_path: Path) -> None:
    import os
    import time

    trip_dir = tmp_path / "demo"
    trip_dir.mkdir()
    png = trip_dir / "demo-longshot.png"
    png.write_bytes(b"png")
    base = time.time() - 100
    os.utime(png, (base, base))
    trip_json = trip_dir / "trip.json"
    trip_json.write_text('{"meta":{"title":"demo"}}', encoding="utf-8")
    assert longshot_outputs_stale(trip_dir, trip_mtime=trip_json.stat().st_mtime) is True


def test_studio_cancel_unknown_job(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"
    try:
        status, body = _post_json(f"{base}/__travelogue/cancel", {"jobId": "job-missing"})
        assert status == 404
        assert body["error"] == "job not found"
    finally:
        server.shutdown()
        server.server_close()


def test_studio_export_zip(tmp_path: Path) -> None:
    album = _distinct_album(tmp_path, 6)
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    result = run_studio_pipeline(album, trips_dir=trips_dir, dedupe=False)
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"
    try:
        status, body = _post_json(
            f"{base}/__travelogue/export",
            {"tripId": result.trip_id, "confirmPrivacy": True},
        )
        assert status == 200, body
        zip_path = Path(body["zipPath"])
        assert zip_path.is_file()
        assert zip_path.suffix == ".zip"
    finally:
        server.shutdown()
        server.server_close()


def test_studio_cancel_import_job(tmp_path: Path) -> None:
    album = _distinct_album(tmp_path, 6)
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"

    try:
        status, body = _post_json(
            f"{base}/__travelogue/import",
            {"albumPath": str(album), "title": "取消测试", "place": "测试"},
        )
        assert status == 202
        job_id = body["jobId"]

        cancel_status, cancel_body = _post_json(
            f"{base}/__travelogue/cancel",
            {"jobId": job_id},
        )
        assert cancel_status == 200
        assert cancel_body.get("status") in ("cancelled", "running", "queued", "succeeded")

        deadline = time.time() + 120
        last: dict = {}
        while time.time() < deadline:
            status, last = _get_json(f"{base}/__travelogue/status?jobId={job_id}")
            if last.get("status") in ("cancelled", "succeeded", "failed"):
                break
            time.sleep(0.3)

        assert last.get("status") in ("cancelled", "succeeded")
        if last.get("status") == "cancelled":
            assert last.get("error", {}).get("code") == "E_STUDIO_CANCELLED"
    finally:
        server.shutdown()
        server.server_close()
        get_job_store().finish_import()
