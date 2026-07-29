"""Studio cancel / export API (M10)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.integration.studio.test_studio_server import (
    _distinct_album,
    _free_port,
    _get_json,
    _post_json,
    _start_studio_server,
)
from tests.studio_test_helpers import wait_for_job
from travelogue.web.studio_jobs import get_job_store, reset_job_store
from travelogue.web.studio_pipeline import run_studio_pipeline
from travelogue.web.studio_trips import (
    has_longshot_exports,
    list_studio_trips,
    longshot_outputs_stale,
    longshot_reveal_rel_path,
    _longshot_files,
)

pytestmark = pytest.mark.e2e


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
    assert row.get("previewRelPath") == "preview.jpg"
    assert (trips_dir / result.trip_id / "preview.jpg").is_file()
    assert row.get("hasLongshotExport") is False
    assert row.get("longshotRevealRelPath") is None


def test_longshot_reveal_rel_prefers_current_manifesto(tmp_path: Path) -> None:
    from travelogue.export.longshot import write_longshot_current

    trip_dir = tmp_path / "reveal-trip"
    trip_dir.mkdir()
    (trip_dir / "older-longshot.png").write_bytes(b"png")
    (trip_dir / "newer-长图.png").write_bytes(b"png")
    write_longshot_current(
        trip_dir,
        batch_id="batch-1",
        kind="whole",
        files=["newer-长图.png"],
    )
    assert longshot_reveal_rel_path(trip_dir) == "newer-长图.png"


def test_longshot_reveal_rel_falls_back_to_newest_file(tmp_path: Path) -> None:
    import os
    import time

    trip_dir = tmp_path / "reveal-legacy"
    trip_dir.mkdir()
    older = trip_dir / "trip-ch01.png"
    newer = trip_dir / "trip-ch02.png"
    older.write_bytes(b"png")
    newer.write_bytes(b"png")
    base = time.time()
    os.utime(older, (base - 20, base - 20))
    os.utime(newer, (base - 5, base - 5))
    assert longshot_reveal_rel_path(trip_dir) == "trip-ch02.png"


def test_has_longshot_exports_detects_chapter_pngs(tmp_path: Path) -> None:
    trip_dir = tmp_path / "demo-trip"
    trip_dir.mkdir()
    assert has_longshot_exports(trip_dir) is False
    (trip_dir / "trip-ch01.png").write_bytes(b"png")
    assert has_longshot_exports(trip_dir) is True


def test_has_longshot_exports_detects_chapter_jpgs(tmp_path: Path) -> None:
    trip_dir = tmp_path / "demo-trip-jpg"
    trip_dir.mkdir()
    assert has_longshot_exports(trip_dir) is False
    (trip_dir / "trip-ch01.jpg").write_bytes(b"jpg")
    assert has_longshot_exports(trip_dir) is True


def test_has_longshot_exports_detects_moments_png(tmp_path: Path) -> None:
    """AC-LNG2-06 · moments glob participates in longshot file set."""
    from travelogue.web.studio_trips import _longshot_files

    trip_dir = tmp_path / "demo-moments"
    trip_dir.mkdir()
    assert has_longshot_exports(trip_dir) is False
    (trip_dir / "demo-moments-01.png").write_bytes(b"png")
    assert has_longshot_exports(trip_dir) is True
    (trip_dir / "demo-moments-02.png.part").write_bytes(b"part")
    names = {p.name for p in _longshot_files(trip_dir)}
    assert "demo-moments-01.png" in names
    assert "demo-moments-02.png.part" not in names


def test_longshot_stale_when_moments_older_than_trip(tmp_path: Path) -> None:
    """AC-LNG2-06 · trip mtime newer than moments → stale."""
    import os
    import time

    trip_dir = tmp_path / "demo-stale-moments"
    trip_dir.mkdir()
    moments = trip_dir / "demo-moments-01.png"
    moments.write_bytes(b"png")
    base = time.time() - 100
    os.utime(moments, (base, base))
    trip_json = trip_dir / "trip.json"
    trip_json.write_text('{"meta":{"title":"demo"}}', encoding="utf-8")
    assert longshot_outputs_stale(trip_dir, trip_mtime=trip_json.stat().st_mtime) is True


def test_has_longshot_exports_detects_xhs_png(tmp_path: Path) -> None:
    """AC-LNG2-06 · xhs glob participates in longshot file set."""
    from travelogue.web.studio_trips import _longshot_files

    trip_dir = tmp_path / "demo-xhs"
    trip_dir.mkdir()
    assert has_longshot_exports(trip_dir) is False
    (trip_dir / "demo-xhs-01.png").write_bytes(b"png")
    assert has_longshot_exports(trip_dir) is True
    (trip_dir / "demo-xhs-02.png.part").write_bytes(b"part")
    names = {p.name for p in _longshot_files(trip_dir)}
    assert "demo-xhs-01.png" in names
    assert "demo-xhs-02.png.part" not in names


def test_longshot_stale_when_xhs_older_than_trip(tmp_path: Path) -> None:
    """AC-LNG2-06 · trip mtime newer than *-xhs-* → stale."""
    import os
    import time

    trip_dir = tmp_path / "demo-stale-xhs"
    trip_dir.mkdir()
    xhs = trip_dir / "demo-xhs-01.png"
    xhs.write_bytes(b"png")
    base = time.time() - 100
    os.utime(xhs, (base, base))
    trip_json = trip_dir / "trip.json"
    trip_json.write_text('{"meta":{"title":"demo"}}', encoding="utf-8")
    assert longshot_outputs_stale(trip_dir, trip_mtime=trip_json.stat().st_mtime) is True


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


def test_longshot_stale_when_trip_newer_jpg(tmp_path: Path) -> None:
    import os
    import time

    trip_dir = tmp_path / "demo-jpg"
    trip_dir.mkdir()
    shot = trip_dir / "demo-longshot.jpg"
    shot.write_bytes(b"jpg")
    base = time.time() - 100
    os.utime(shot, (base, base))
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
        assert body.get("zipRelPath")
        zip_path = trips_dir / result.trip_id / body["zipRelPath"]
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

        last = wait_for_job(
            lambda: _get_json(f"{base}/__travelogue/status?jobId={job_id}")[1],
            timeout_sec=120,
            poll_sec=0.05,
            terminal=frozenset({"cancelled", "succeeded", "failed"}),
        )

        assert last.get("status") in ("cancelled", "succeeded")
        if last.get("status") == "cancelled":
            assert last.get("error", {}).get("code") == "E_STUDIO_CANCELLED"
    finally:
        server.shutdown()
        server.server_close()
        get_job_store().finish_import()
