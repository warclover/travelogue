"""CLG · sibling-journal 路由与 handler。"""

from __future__ import annotations

import json
from pathlib import Path

from tests.studio_test_helpers import MockStudioHandler
from travelogue.web.studio_dispatch import _CAPTURE_MATCHERS, ROUTE_SPECS
from travelogue.web.studio_handlers.common import match_trip_sibling_journal
from travelogue.web.studio_handlers.trip_list_handlers import handle_sibling_journal
from travelogue.services.trip_factory import create_trip


def test_sibling_journal_route_registered() -> None:
    path = "/__travelogue/trips/{tripId}/sibling-journal"
    assert path in {spec.path for spec in ROUTE_SPECS}
    assert path in _CAPTURE_MATCHERS
    assert match_trip_sibling_journal("/__travelogue/trips/demo-x/sibling-journal") == "demo-x"


def test_handle_sibling_journal_404(tmp_path: Path) -> None:
    handler = MockStudioHandler(tmp_path / "trips")
    handle_sibling_journal(handler, "missing-trip")
    assert handler.response is not None
    assert handler.response[0] == 404


def test_handle_sibling_journal_present_false_when_no_root(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    create_trip("pf-alone", trips, title="alone")
    trip_json = trips / "pf-alone" / "trip.json"
    data = json.loads(trip_json.read_text(encoding="utf-8"))
    data["studio"] = {"edition": "portfolio"}
    trip_json.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    handler = MockStudioHandler(trips)
    handle_sibling_journal(handler, "pf-alone")
    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    assert body["ok"] is True
    assert body["present"] is False
    assert body["canCreateSibling"] is False
