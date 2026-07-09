"""Studio DELETE /__travelogue/trips/{tripId} (M13)."""

from __future__ import annotations

import json
from pathlib import Path
from urllib import error, request

import pytest

from tests.integration.studio.test_studio_server import _free_port, _get_json, _start_studio_server
from travelogue.services.trip_factory import create_trip

pytestmark = pytest.mark.e2e


def _delete(url: str, *, token: str | None = None) -> int:
    headers = {}
    if token:
        headers["X-Studio-Token"] = token
    req = request.Request(url, method="DELETE", headers=headers)
    try:
        with request.urlopen(req, timeout=30) as resp:
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

        assert _delete(f"http://127.0.0.1:{port}/__travelogue/trips/kyoto-test") == 204
        assert not trip_dir.exists()

        status, listing = _get_json(f"http://127.0.0.1:{port}/__travelogue/trips")
        assert status == 200
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
        code = _delete(f"http://127.0.0.1:{port}/__travelogue/trips/demo-album")
        assert code == 403
        assert (trips_dir / "demo-album").is_dir()
    finally:
        server.shutdown()


def test_delete_unknown_trip_404(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        assert _delete(f"http://127.0.0.1:{port}/__travelogue/trips/missing") == 404
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
        assert _delete(f"http://127.0.0.1:{port}/__travelogue/trips/My-Album-01") == 204
        assert not trip_dir.exists()
    finally:
        server.shutdown()
