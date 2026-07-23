"""Studio DELETE /__travelogue/trips/{tripId} (M13 + PDG)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from urllib import error, request

import pytest

from tests.integration.studio.test_studio_server import _free_port, _get_json, _start_studio_server
from travelogue.services.trip_factory import create_trip
from travelogue.web.studio_jobs import get_job_store, reset_job_store
from travelogue.web.studio_trip_delete import (
    rename_trip_to_tombstone,
    sweep_deleting_tombstones,
    tombstone_name,
)

pytestmark = pytest.mark.e2e


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


def _delete(url: str, *, token: str | None = None) -> tuple[int, dict]:
    headers = {}
    if token:
        headers["X-Studio-Token"] = token
    req = request.Request(url, method="DELETE", headers=headers)
    try:
        with request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8") if exc.fp else ""
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {}
        return exc.code, payload


def _get(url: str) -> int:
    req = request.Request(url, method="GET")
    try:
        with request.urlopen(req, timeout=10) as resp:
            return resp.status
    except error.HTTPError as exc:
        return exc.code


def test_delete_trip_removes_directory(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    create_trip("kyoto-test", trips_dir)
    trip_dir = trips_dir / "kyoto-test"
    assert trip_dir.is_dir()

    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        status, listing = _get_json(f"http://127.0.0.1:{port}/__travelogue/trips")
        assert status == 200
        assert listing["total"] == 1

        code, _ = _delete(f"http://127.0.0.1:{port}/__travelogue/trips/kyoto-test")
        assert code == 204
        assert not trip_dir.exists()

        # async rmtree may leave tombstone briefly; logical list must be empty
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            status, listing = _get_json(f"http://127.0.0.1:{port}/__travelogue/trips")
            if status == 200 and listing["total"] == 0:
                break
            time.sleep(0.05)
        assert listing["total"] == 0
    finally:
        server.shutdown()


def test_delete_demo_trip_denied(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    create_trip("demo-album", trips_dir)
    trip_json = trips_dir / "demo-album" / "trip.json"
    data = json.loads(trip_json.read_text(encoding="utf-8"))
    data.setdefault("meta", {})["title"] = "示例旅途"
    trip_json.write_text(json.dumps(data), encoding="utf-8")

    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        code, payload = _delete(f"http://127.0.0.1:{port}/__travelogue/trips/demo-album")
        assert code == 403
        assert payload.get("error") == "E_TRIP_DELETE_DENIED"
        assert (trips_dir / "demo-album").is_dir()
    finally:
        server.shutdown()


def test_delete_unknown_trip_404(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        code, payload = _delete(f"http://127.0.0.1:{port}/__travelogue/trips/missing")
        assert code == 404
        assert payload.get("error") == "E_TRIP_NOT_FOUND"
    finally:
        server.shutdown()


def test_delete_trip_by_listed_folder_name(tmp_path: Path) -> None:
    """list 可见的目录名（非 strict slug）也应能删除。"""
    trips_dir = tmp_path / "trips"
    trip_dir = trips_dir / "My-Album-01"
    trip_dir.mkdir(parents=True)
    trip_json = {
        "meta": {"title": "我的相册"},
        "assets": [],
        "pipeline": {"status": "done"},
    }
    (trip_dir / "trip.json").write_text(json.dumps(trip_json), encoding="utf-8")

    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        status, listing = _get_json(f"http://127.0.0.1:{port}/__travelogue/trips")
        assert status == 200
        assert listing["total"] == 1
        assert listing["trips"][0]["tripId"] == "My-Album-01"
        code, _ = _delete(f"http://127.0.0.1:{port}/__travelogue/trips/My-Album-01")
        assert code == 204
        assert not trip_dir.exists()
    finally:
        server.shutdown()


def test_delete_busy_job_409(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    create_trip("busy-trip", trips_dir)
    store = get_job_store()
    job = store.create_import_job()
    assert job is not None
    store.update(job, status="running", trip_id="busy-trip")

    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        code, payload = _delete(f"http://127.0.0.1:{port}/__travelogue/trips/busy-trip")
        assert code == 409
        assert payload.get("error") == "E_STUDIO_JOB_BUSY"
        assert (trips_dir / "busy-trip").is_dir()
    finally:
        server.shutdown()


def test_delete_while_deleting_flag_blocks_static(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    create_trip("gate-trip", trips_dir)
    (trips_dir / "gate-trip" / "preview.jpg").write_bytes(b"fake")

    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        assert get_job_store().begin_trip_delete("gate-trip")
        assert _get(f"http://127.0.0.1:{port}/gate-trip/preview.jpg") == 404
    finally:
        get_job_store().end_trip_delete("gate-trip")
        server.shutdown()


def test_rename_failure_clears_deleting_and_returns_structured_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    create_trip("fail-rename", trips_dir)

    def _boom(_trip_dir: Path) -> Path:
        raise OSError("simulated rename busy")

    monkeypatch.setattr(
        "travelogue.web.studio_handlers.trip_list_handlers.rename_trip_to_tombstone",
        _boom,
    )

    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        code, payload = _delete(f"http://127.0.0.1:{port}/__travelogue/trips/fail-rename")
        assert code == 500
        assert payload.get("error") == "E_TRIP_DELETE_FAILED"
        assert payload.get("message")
        assert not get_job_store().is_trip_deleting("fail-rename")
        # can retry
        monkeypatch.undo()
        code2, _ = _delete(f"http://127.0.0.1:{port}/__travelogue/trips/fail-rename")
        assert code2 == 204
    finally:
        server.shutdown()


def test_sweep_deleting_tombstones(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    create_trip("alive", trips_dir)
    tomb = trips_dir / tombstone_name("gone", nonce="abcd1234")
    tomb.mkdir()
    (tomb / "trip.json").write_text("{}", encoding="utf-8")
    assert sweep_deleting_tombstones(trips_dir) >= 1
    assert not tomb.exists()
    assert (trips_dir / "alive").is_dir()


def test_rename_trip_to_tombstone_hides_from_list_prefix(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    create_trip("to-hide", trips_dir)
    tomb = rename_trip_to_tombstone(trips_dir / "to-hide")
    assert tomb.name.startswith("_deleting-")
    assert not (trips_dir / "to-hide").exists()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        status, listing = _get_json(f"http://127.0.0.1:{port}/__travelogue/trips")
        assert status == 200
        assert listing["total"] == 0
    finally:
        server.shutdown()
        sweep_deleting_tombstones(trips_dir)


def test_ac_pdg_07_delete_joins_on_demand_barrier(tmp_path: Path) -> None:
    """AC-PDG-07 · 注入慢 on-demand 线程：DELETE 同步路径 <5s 返回且目录逻辑消失。"""
    import threading

    from travelogue.media.derivatives import register_on_demand_thread_for_tests

    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    create_trip("ondemand-trip", trips_dir)
    trip_dir = trips_dir / "ondemand-trip"
    (trip_dir / "preview.jpg").write_bytes(b"fake-preview")

    def _slow() -> None:
        time.sleep(1.2)

    thr = threading.Thread(target=_slow, name="test-on-demand", daemon=True)
    thr.start()
    register_on_demand_thread_for_tests(trip_dir, thr)

    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        t0 = time.monotonic()
        code, _ = _delete(f"http://127.0.0.1:{port}/__travelogue/trips/ondemand-trip")
        elapsed = time.monotonic() - t0
        assert code == 204
        assert elapsed < 5.0, f"delete hung: {elapsed:.2f}s"
        assert not trip_dir.exists()
        assert not thr.is_alive()
    finally:
        server.shutdown()


def test_ac_pdg_07_volume_many_files_delete_under_budget(tmp_path: Path) -> None:
    """AC-PDG-07 补充 · ≥20 假资产文件：rename+204 同步路径 <5s（不挡 Windows 大图签字）。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    create_trip("volume-trip", trips_dir)
    trip_dir = trips_dir / "volume-trip"
    assets = trip_dir / "assets"
    assets.mkdir(exist_ok=True)
    blob = b"x" * 64_000
    for i in range(24):
        (assets / f"asset-{i:03d}.bin").write_bytes(blob)

    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        t0 = time.monotonic()
        code, _ = _delete(f"http://127.0.0.1:{port}/__travelogue/trips/volume-trip")
        elapsed = time.monotonic() - t0
        assert code == 204
        assert elapsed < 5.0, f"delete hung: {elapsed:.2f}s"
        assert not trip_dir.exists()
    finally:
        server.shutdown()
