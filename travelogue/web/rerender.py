"""Re-render draft HTML after inline copy edits."""

from __future__ import annotations

from pathlib import Path

from travelogue.render.engine import LONGSHOT_INDEX_NAME, render_trip


def rerender_draft_trip(trip_json: Path) -> list[str]:
    """Render index.html and longshot sidecar (when applicable) after trip.json edits."""
    from travelogue.services.trip import TripService

    trip_json = trip_json.resolve()
    trip_root = trip_json.parent
    trip = TripService().load(trip_json)
    layout_engine = trip.get("layoutEngine")
    render_trip(
        trip_json,
        trip_root,
        export_mode="draft",
        validate=False,
        layout_engine=layout_engine,
    )
    written = ["index.html"]
    if (trip_root / LONGSHOT_INDEX_NAME).is_file():
        written.append(LONGSHOT_INDEX_NAME)
    mobile = trip_root / "index-mobile.html"
    if mobile.is_file():
        written.append("index-mobile.html")
    return written
