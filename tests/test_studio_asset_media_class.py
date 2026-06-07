"""Studio PATCH asset-media-class (PRD §3.4 collage 改判)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.studio_test_helpers import MockStudioHandler
from travelogue.services.trip import TripService
from travelogue.services.trip_factory import create_trip
from travelogue.web.studio_entry import build_asset_media_index, build_entry
from travelogue.web.studio_handlers.paths import ASSET_MEDIA_SUFFIX, TRIPS_PATH
from travelogue.web.studio_handlers.trip_handlers import handle_asset_media_class
from travelogue.web.studio_routes import StudioMixin

pytestmark = pytest.mark.unit


class _PatchProbe(StudioMixin):
    studio_mode = True
    studio_token = "t"
    studio_host = "127.0.0.1"
    studio_port = 8766
    studio_allow_lan = False
    studio_config_path = None
    trips_dir = None
    trip_json_path = None
    app_config = None
    command = "PATCH"
    path = "/"
    headers: dict = {}

    def __init__(self) -> None:
        self.calls: list[str] = []

    def _studio_require_post_auth(self) -> bool:
        return True

    def _json_response(self, code: int, payload: dict) -> None:
        pass


def test_studio_dispatch_patch_asset_media_class(monkeypatch) -> None:
    probe = _PatchProbe()
    monkeypatch.setattr(
        "travelogue.web.studio_handlers.trip_handlers.handle_asset_media_class",
        lambda h, tid: probe.calls.append(f"asset_media:{tid}"),
    )
    trip = "demo-collage"
    assert probe.studio_dispatch_PATCH(f"{TRIPS_PATH}/{trip}{ASSET_MEDIA_SUFFIX}") is True
    assert probe.calls == [f"asset_media:{trip}"]


def test_build_entry_includes_asset_media_by_id() -> None:
    trip = {
        "assets": [
            {"id": "a1", "mediaClass": "photo"},
            {"id": "a2", "mediaClass": "collage"},
        ],
        "chapters": [],
    }
    entry = build_entry(trip, "demo")
    assert entry["assetMediaById"] == {"a1": "photo", "a2": "collage"}
    assert build_asset_media_index(trip)["a2"] == "collage"


def test_handle_asset_media_class_updates_trip(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_json = create_trip("demo-media", trips_dir, title="T", place="P")
    trip = TripService(root=trips_dir.parent).load(trip_json)
    trip["assets"] = [{"id": "a1", "mediaClass": "photo"}]
    TripService(root=trips_dir.parent).save(trip, trip_json)

    handler = MockStudioHandler(
        trips_dir,
        json_body={"assetId": "a1", "mediaClass": "collage"},
        path=f"{TRIPS_PATH}/demo-media{ASSET_MEDIA_SUFFIX}",
    )
    handle_asset_media_class(handler, "demo-media")
    assert handler.response == (200, {"ok": True, "assetId": "a1", "mediaClass": "collage"})

    saved = json.loads(trip_json.read_text(encoding="utf-8"))
    assert saved["assets"][0]["mediaClass"] == "collage"


def test_handle_asset_media_class_rejects_invalid_class(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    create_trip("demo-bad", trips_dir, title="T", place="P")
    handler = MockStudioHandler(
        trips_dir,
        json_body={"assetId": "a1", "mediaClass": "not-a-class"},
        path=f"{TRIPS_PATH}/demo-bad{ASSET_MEDIA_SUFFIX}",
    )
    handle_asset_media_class(handler, "demo-bad")
    assert handler.response is not None
    status, body = handler.response
    assert status == 400
    assert body["error"] == "E_MEDIA_CLASS_INVALID"
