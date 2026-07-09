"""Golden reference trip materialization."""

from __future__ import annotations

import json

from travelogue.demo.golden_reference import materialize_golden_reference
from travelogue.render.golden_regression import GOLDEN_TRIP_FIXTURE


def test_materialize_golden_reference(tmp_path) -> None:
    trips = tmp_path / "trips"
    ref = materialize_golden_reference(trips, force=True)
    assert ref.trip_dir.is_dir()
    assert (ref.trip_dir / "trip.json").is_file()
    assert (ref.trip_dir / "index.html").is_file()
    assert (ref.trip_dir / "assets" / "demo" / "cover-w1600.webp").is_file()
    trip = json.loads((ref.trip_dir / "trip.json").read_text(encoding="utf-8"))
    expected = json.loads(GOLDEN_TRIP_FIXTURE.read_text(encoding="utf-8"))
    assert trip["tripId"] == expected["tripId"]
    assert len(trip["chapters"]) == 4
