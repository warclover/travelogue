"""Phase 4 M17 · G1 structure confirm (mode A/B)."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from urllib import error, request

import pytest

from tests.test_studio_server import _distinct_album, _free_port, _start_studio_server
from travelogue.config import StudioConfig, get_config
from travelogue.services.pipeline_state import trip_status
from travelogue.services.trip import TripService
from travelogue.web.studio_g1 import lock_trip_structure
from travelogue.web.studio_pipeline import run_studio_pipeline

pytestmark = pytest.mark.e2e


def _patch_json(url: str, payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="PATCH",
    )
    try:
        with request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, json.loads(body) if body else {}


def test_studio_config_exposes_g1_flag() -> None:
    from travelogue.config import studio_config_expose

    cfg = replace(get_config(), studio=StudioConfig(g1_confirm_structure=True))
    exposed = studio_config_expose(cfg)
    assert exposed["studio"]["g1ConfirmStructure"] is True


def test_lock_trip_structure_sets_locked() -> None:
    trip: dict = {"pipeline": {"status": "structure_draft", "locks": {}}}
    lock_trip_structure(trip)
    assert trip["pipeline"]["status"] == "structure_locked"
    assert trip["pipeline"]["locks"]["structure"] is True


def test_g1_mode_b_stops_at_structure_draft(tmp_path: Path) -> None:
    album = _distinct_album(tmp_path, 8)
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    cfg = replace(get_config(), trips_dir=trips_dir, studio=StudioConfig(g1_confirm_structure=True))
    result = run_studio_pipeline(
        album,
        trips_dir=trips_dir,
        dedupe=False,
        app_config=cfg,
    )
    assert result.g1_pending is True
    trip = json.loads(result.trip_json.read_text(encoding="utf-8"))
    assert trip_status(trip) == "structure_draft"
    assert (result.trip_dir / "index.html").is_file()


def test_g1_mode_a_reaches_rendered(tmp_path: Path) -> None:
    album = _distinct_album(tmp_path, 8)
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    cfg = replace(get_config(), trips_dir=trips_dir, studio=StudioConfig(g1_confirm_structure=False))
    result = run_studio_pipeline(
        album,
        trips_dir=trips_dir,
        dedupe=False,
        app_config=cfg,
    )
    assert result.g1_pending is False
    trip = json.loads(result.trip_json.read_text(encoding="utf-8"))
    assert trip_status(trip) == "rendered"


def test_patch_pipeline_confirm_structure_draft(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_id = "demo-g1"
    trip_dir = trips_dir / trip_id
    trip_dir.mkdir(parents=True)
    trip = {
        "meta": {"title": "测试"},
        "pipeline": {"status": "structure_draft", "locks": {}},
        "assets": [{"id": "a1"}, {"id": "a2"}, {"id": "a3"}, {"id": "a4"}],
        "chapters": [],
    }
    TripService(root=tmp_path).save(trip, trip_dir / "trip.json")

    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        status, body = _patch_json(
            f"http://127.0.0.1:{port}/__travelogue/trips/{trip_id}/pipeline",
            {"status": "structure_locked", "continuePipeline": False},
        )
        assert status == 200
        assert body["ok"] is True
        saved = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
        assert trip_status(saved) == "structure_locked"
    finally:
        server.shutdown()
