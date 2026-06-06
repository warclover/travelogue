"""Studio security hardening tests."""

from __future__ import annotations

import json
import threading
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib import error, request

import pytest

from tests.test_studio_server import _distinct_album, _free_port, _post_json, _start_studio_server
from travelogue.web.serve import TripPreviewHandler
from travelogue.web.studio_jobs import get_job_store, reset_job_store
from travelogue.web.studio_pipeline import run_studio_pipeline

pytestmark = pytest.mark.e2e


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


def test_studio_bind_trip_rejects_parent_traversal(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    outside_trip = tmp_path / "trip.json"
    outside_trip.write_text('{"meta":{"title":"outside"}}', encoding="utf-8")

    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"

    try:
        with pytest.raises(error.HTTPError) as exc:
            request.urlopen(f"{base}/../index.html", timeout=5)
        assert exc.value.code == 404
    finally:
        server.shutdown()
        server.server_close()


def test_studio_reveal_accepts_trip_rel_path(tmp_path: Path) -> None:
    album = _distinct_album(tmp_path, 6)
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    result = run_studio_pipeline(album, trips_dir=trips_dir, dedupe=False)
    target = trips_dir / result.trip_id / "preview.jpg"
    assert target.is_file()

    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"

    try:
        status, body = _post_json(
            f"{base}/__travelogue/reveal",
            {"tripId": result.trip_id, "relPath": "preview.jpg"},
        )
        assert status == 200, body
        assert body.get("ok") is True
    finally:
        server.shutdown()
        server.server_close()


def test_longshot_cancel_does_not_overwrite_cancelled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from travelogue.web import studio_jobs

    job = get_job_store().create_longshot_job()
    assert job is not None

    def slow_runner() -> dict:
        import time

        time.sleep(0.3)
        return {"tripId": "demo", "outputs": ["demo-longshot.png"]}

    import threading

    threading.Thread(
        target=lambda: studio_jobs.run_longshot_job(job, runner=slow_runner),
        daemon=True,
    ).start()

    import time

    time.sleep(0.05)
    get_job_store().cancel_job(job.job_id)
    time.sleep(0.5)

    assert job.status == "cancelled"
    assert job.result is None


def test_non_loopback_bind_requires_allow_lan() -> None:
    from travelogue.web.studio_auth import ensure_studio_bind_allowed

    with pytest.raises(SystemExit):
        ensure_studio_bind_allowed("0.0.0.0", allow_lan=False)

    ensure_studio_bind_allowed("0.0.0.0", allow_lan=True)


def test_studio_post_requires_token_on_allow_lan(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    token = "test-token-value"
    handler = partial(
        TripPreviewHandler,
        directory=str(trips_dir),
        trip_json=trips_dir / ".placeholder" / "trip.json",
        studio_mode=True,
        trips_dir=trips_dir,
        studio_host="0.0.0.0",
        studio_port=port,
        studio_token=token,
        studio_allow_lan=True,
    )
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    try:
        payload = json.dumps({"jobId": "missing"}).encode("utf-8")
        req = request.Request(
            f"{base}/__travelogue/cancel",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(error.HTTPError) as exc:
            request.urlopen(req, timeout=5)
        assert exc.value.code == 401

        req2 = request.Request(
            f"{base}/__travelogue/cancel",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-Studio-Token": token,
            },
            method="POST",
        )
        try:
            with request.urlopen(req2, timeout=5) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            assert resp.status == 404
        except error.HTTPError as exc:
            body = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 404
        assert body["error"] == "job not found"
    finally:
        server.shutdown()
        server.server_close()


def test_studio_patch_intent_requires_token_on_allow_lan(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_id = "demo-test"
    trip_dir = trips_dir / trip_id
    trip_dir.mkdir(parents=True)
    (trip_dir / "trip.json").write_text(
        json.dumps({"tripId": trip_id, "meta": {"title": "T"}, "intent": {}}),
        encoding="utf-8",
    )
    port = _free_port()
    token = "test-token-value"
    handler = partial(
        TripPreviewHandler,
        directory=str(trips_dir),
        trip_json=trip_dir / "trip.json",
        studio_mode=True,
        trips_dir=trips_dir,
        studio_host="0.0.0.0",
        studio_port=port,
        studio_token=token,
        studio_allow_lan=True,
    )
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    try:
        payload = json.dumps({"title": "新标题"}).encode("utf-8")
        req = request.Request(
            f"{base}/__travelogue/trips/{trip_id}/intent",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="PATCH",
        )
        with pytest.raises(error.HTTPError) as exc:
            request.urlopen(req, timeout=5)
        assert exc.value.code == 401
    finally:
        server.shutdown()
        server.server_close()


def test_longshot_cancel_releases_job_slot() -> None:
    store = get_job_store()
    job = store.create_longshot_job()
    assert job is not None
    store.cancel_job(job.job_id)
    retry = store.create_longshot_job()
    assert retry is not None
