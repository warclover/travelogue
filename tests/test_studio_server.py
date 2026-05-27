"""Studio serve --studio API (M8a)."""

from __future__ import annotations

import json
import threading
import time
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib import error, request

import pytest

from travelogue.web.serve import TripPreviewHandler
from travelogue.web.studio_jobs import reset_job_store
from travelogue.web.studio_pipeline import run_studio_pipeline
from tests.test_ingest import _album


def _distinct_album(tmp_path: Path, n: int = 6) -> Path:
    import os
    import time

    from PIL import Image

    album = tmp_path / "album-distinct"
    album.mkdir()
    base = time.time() - n * 10
    for i in range(n):
        path = album / f"p{i:02d}.jpg"
        Image.new("RGB", (900, 700), (20 + i * 35, 50 + i * 10, 80)).save(
            path, quality=95
        )
        ts = base + i * 10
        os.utime(path, (ts, ts))
    return album


def _free_port() -> int:
    server = ThreadingHTTPServer(("127.0.0.1", 0), TripPreviewHandler)
    port = server.server_address[1]
    server.server_close()
    return port


def _start_studio_server(trips_dir: Path, port: int) -> ThreadingHTTPServer:
    handler = partial(
        TripPreviewHandler,
        directory=str(trips_dir),
        trip_json=trips_dir / ".placeholder" / "trip.json",
        studio_mode=True,
        trips_dir=trips_dir,
        studio_host="127.0.0.1",
        studio_port=port,
    )
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def _post_json(url: str, payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, json.loads(body) if body else {}


def _get_json(url: str) -> tuple[int, dict]:
    with request.urlopen(url, timeout=30) as resp:
        body = resp.read().decode("utf-8")
        return resp.status, json.loads(body) if body else {}


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


def test_studio_import_job(tmp_path: Path) -> None:
    album = _distinct_album(tmp_path, 6)
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"

    try:
        status, body = _post_json(
            f"{base}/__travelogue/import",
            {"albumPath": str(album), "title": "测试", "place": "测试"},
        )
        assert status == 202
        job_id = body["jobId"]

        deadline = time.time() + 180
        last: dict = {}
        while time.time() < deadline:
            status, last = _get_json(f"{base}/__travelogue/status?jobId={job_id}")
            assert status == 200
            if last.get("status") in ("succeeded", "failed"):
                break
            time.sleep(0.5)

        assert last.get("status") == "succeeded", last
        assert last.get("stageIndex") == 4
        assert last.get("stageHint")
        assert last.get("result", {}).get("previewUrl", "").endswith("/index.html")
        trip_id = last["tripId"]
        assert (trips_dir / trip_id / "index.html").is_file()
        assert (trips_dir / trip_id / "preview.jpg").is_file()
    finally:
        server.shutdown()
        server.server_close()


def test_studio_demo_exists_409(tmp_path: Path) -> None:
    album = _distinct_album(tmp_path, 6)
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()

    run_studio_pipeline(
        album,
        trips_dir=trips_dir,
        title="测试",
        place="测试",
        host="127.0.0.1",
        port=8766,
        dedupe=False,
    )

    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"

    try:
        status, body = _post_json(
            f"{base}/__travelogue/import",
            {"albumPath": str(album), "title": "测试", "place": "测试", "force": False},
        )
        assert status == 409
        assert body["error"] == "E_DEMO_EXISTS"
        assert body.get("existingTripId")
        assert (trips_dir / body["existingTripId"] / "trip.json").is_file()
    finally:
        server.shutdown()
        server.server_close()


def test_studio_reveal_denied(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"

    try:
        outside = tmp_path / "outside.txt"
        outside.write_text("x", encoding="utf-8")
        status, body = _post_json(f"{base}/__travelogue/reveal", {"path": str(outside)})
        assert status == 403
        assert body["error"] == "E_STUDIO_REVEAL_DENIED"
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.skipif(
    not __import__("importlib").util.find_spec("playwright"),
    reason="playwright not installed",
)
def test_studio_longshot_job(tmp_path: Path) -> None:
    album = _distinct_album(tmp_path, 6)
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"

    run_studio_pipeline(
        album,
        trips_dir=trips_dir,
        title="长图测试",
        place="测试",
        host="127.0.0.1",
        port=port,
        dedupe=False,
    )
    trip_id = next(p.name for p in trips_dir.iterdir() if (p / "trip.json").is_file())

    try:
        status, body = _post_json(
            f"{base}/__travelogue/longshot",
            {"tripId": trip_id, "scale": 1},
        )
        assert status == 202, body
        job_id = body["jobId"]

        deadline = time.time() + 180
        last: dict = {}
        while time.time() < deadline:
            status, last = _get_json(f"{base}/__travelogue/status?jobId={job_id}")
            assert status == 200
            if last.get("status") in ("succeeded", "failed"):
                break
            time.sleep(0.5)

        assert last.get("status") == "succeeded", last
        outputs = last.get("result", {}).get("outputs") or []
        assert outputs
        trip_dir = trips_dir / trip_id
        assert (trip_dir / outputs[0]).is_file()
    finally:
        server.shutdown()
        server.server_close()
