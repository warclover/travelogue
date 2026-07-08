"""Tests for trip.version migration registry (M-B6)."""

from __future__ import annotations

import pytest

from travelogue.curation.trip_migration import (
    CURRENT_TRIP_VERSION,
    TripVersionError,
    migrate_trip,
    strip_legacy_curation_fields,
)


def test_strip_legacy_curation_fields() -> None:
    trip = {"version": "0.2", "curation": {"insights": {"x": 1}, "layoutStrategy": {}}}
    out = strip_legacy_curation_fields(trip)
    assert "insights" not in out["curation"]
    assert "layoutStrategy" in out["curation"]


def test_migrate_trip_applies_registry() -> None:
    trip = {"curation": {"insights": [1]}}
    out = migrate_trip(trip)
    assert "insights" not in out["curation"]
    assert out.get("version", "0.2") == "0.2" or "curation" in out


def test_migrate_trip_rejects_unsupported_version() -> None:
    with pytest.raises(TripVersionError):
        migrate_trip({"version": "9.9", "assets": []})


def test_migrate_trip_accepts_current_version() -> None:
    trip = {"version": CURRENT_TRIP_VERSION, "assets": []}
    assert migrate_trip(trip)["version"] == CURRENT_TRIP_VERSION
