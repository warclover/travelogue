"""Re-render draft HTML after inline copy edits."""

from __future__ import annotations

from pathlib import Path

from travelogue.render.engine import LONGSHOT_INDEX_NAME, render_trip, render_trip_surfaces


def rerender_draft_trip(trip_json: Path) -> list[str]:
    """Render index.html (+ mobile when auto) after trip.json edits."""
    from travelogue.runtime import app_context_for_trip_json

    trip_json = trip_json.resolve()
    trip_root = trip_json.parent
    trip = app_context_for_trip_json(trip_json).trip_service().load(trip_json)
    layout_engine = trip.get("layoutEngine")
    if trip.get("exportLayout", "auto") == "auto":
        web_path, mobile_path, present_path = render_trip_surfaces(
            trip_json,
            trip_root,
            export_mode="draft",
            validate=False,
            update_pipeline=False,
        )
        written = [web_path.name, mobile_path.name]
        if present_path is not None:
            written.append(present_path.name)
    else:
        render_trip(
            trip_json,
            trip_root,
            export_mode="draft",
            validate=False,
            layout_engine=layout_engine,
            stamp_render_bundle=True,
        )
        written = ["index.html"]
    if (trip_root / LONGSHOT_INDEX_NAME).is_file():
        written.append(LONGSHOT_INDEX_NAME)
    return written
