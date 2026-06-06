"""Re-export assets from source."""

from __future__ import annotations

from pathlib import Path

from tests.test_ingest import _album
from travelogue.media.ingest import ingest_into_trip
from travelogue.media.reexport import reexport_trip_assets
from travelogue.services.trip_factory import create_trip


def test_reexport_updates_webp(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("reexport-test", trips)
    trip_dir = trips / "reexport-test"
    import json

    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    ingest_into_trip(trip, trip_dir, from_dir=_album(tmp_path, 5), dedupe=False)
    aid = trip["assets"][0]["id"]
    display = trip_dir / trip["assets"][0]["displayFile"]
    assert display.is_file()
    old_mtime = display.stat().st_mtime

    trip["assets"][0]["focalPoint"] = {"x": 0.2, "y": 0.3}
    result = reexport_trip_assets(trip, trip_dir, asset_ids=[aid])
    assert result.updated == 1
    assert display.stat().st_mtime >= old_mtime
