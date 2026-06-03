"""Studio template create / API tests (Phase 13)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.config import AppConfig
from travelogue.services.trip_factory import create_trip
from travelogue.templating.resolver import resolve_effective_template


def test_create_trip_smart_writes_template_selection(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trips.mkdir()
    trip_json = create_trip("demo-p13-smart", trips, cfg=AppConfig(trips_dir=trips))
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    sel = trip.get("templateSelection") or {}
    assert sel.get("mode") == "smart"
    assert resolve_effective_template(trip) == "visual-journal"
    assert trip["templateId"] == "visual-journal"
    assert sel.get("decisionHash", "").startswith("sha256:")


def test_create_trip_manual_override(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trips.mkdir()
    trip_json = create_trip(
        "demo-p13-manual",
        trips,
        template_mode="manual",
        template_id="visual-journal",
        cfg=AppConfig(trips_dir=trips),
    )
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    sel = trip.get("templateSelection") or {}
    assert sel.get("mode") == "manual"
    assert sel.get("requestedTemplateId") == "visual-journal"
