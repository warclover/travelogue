"""CQA M2 · force import PDG gate (AC-15/16)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.studio_test_helpers import MockStudioHandler
from travelogue.web.studio_handlers.import_handlers import handle_import
from travelogue.web.studio_jobs import reset_job_store

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


@pytest.fixture(autouse=True)
def _trust_local_album(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM", "1")


def _write_trip(trips_root: Path, trip_id: str, *, title: str) -> Path:
    trip_dir = trips_root / trip_id
    trip_dir.mkdir(parents=True)
    (trip_dir / "trip.json").write_text(
        json.dumps({"meta": {"title": title}}, ensure_ascii=False),
        encoding="utf-8",
    )
    (trip_dir / "keep.txt").write_text("alive", encoding="utf-8")
    return trip_dir


def test_force_import_rejects_protected_demo(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    album = tmp_path / "album-demo"
    album.mkdir()
    (album / "a.jpg").write_bytes(b"x")
    trip_dir = _write_trip(trips, "demo-album", title="示例旅途")
    keep = (trip_dir / "keep.txt").read_text(encoding="utf-8")

    handler = MockStudioHandler(
        trips,
        json_body={
            "albumPath": str(album),
            "title": "覆盖",
            "place": "测试",
            "tripId": "demo-album",
            "force": True,
        },
    )
    with patch(
        "travelogue.web.studio_handlers.import_handlers.assert_album_importable",
        return_value="demo-album",
    ):
        handle_import(handler)

    assert handler.response is not None
    status, body = handler.response
    assert status == 403
    assert body["error"] == "E_TRIP_DELETE_DENIED"
    assert (trip_dir / "keep.txt").read_text(encoding="utf-8") == keep


def test_force_import_busy_on_demand_returns_409(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    trips = tmp_path / "trips"
    album = tmp_path / "album-busy"
    album.mkdir()
    (album / "a.jpg").write_bytes(b"x")
    trip_dir = _write_trip(trips, "busy-trip", title="进行中")
    keep = (trip_dir / "keep.txt").read_text(encoding="utf-8")

    monkeypatch.setattr(
        "travelogue.media.derivatives.is_on_demand_alive_for_trip_id",
        lambda tid: tid == "busy-trip",
    )

    handler = MockStudioHandler(
        trips,
        json_body={
            "albumPath": str(album),
            "title": "覆盖",
            "place": "测试",
            "tripId": "busy-trip",
            "force": True,
        },
    )
    with patch(
        "travelogue.web.studio_handlers.import_handlers.assert_album_importable",
        return_value="busy-trip",
    ):
        handle_import(handler)

    assert handler.response is not None
    status, body = handler.response
    assert status == 409
    assert body["error"] == "E_STUDIO_JOB_BUSY"
    assert (trip_dir / "keep.txt").read_text(encoding="utf-8") == keep
    assert trip_dir.is_dir()
