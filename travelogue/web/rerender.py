"""Re-render draft HTML after inline copy edits."""

from __future__ import annotations

from pathlib import Path

from travelogue.render.engine import LONGSHOT_INDEX_NAME, render_trip, render_trip_surfaces


def rerender_draft_trip(trip_json: Path) -> list[str]:
    """Render index.html (+ mobile when auto) after trip.json edits.

    Always refreshes ``index-longshot.html`` when screens layout is active, even if
    ``exportLayout`` is ``mobile`` (bridge gate would otherwise skip the sidecar).
    """
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

    # BE-SFI-05 / FX-SFI-03 · 勿只凭「文件存在」宣称已重渲；mobile 册也须刷新长图面
    from travelogue.layout_engine.planner.screen_planner import LAYOUT_ENGINE_SCREENS
    from travelogue.render.engine import write_longshot_sidecar

    engine = str(layout_engine or trip.get("layoutEngine") or "").strip().lower()
    if engine == LAYOUT_ENGINE_SCREENS or (trip_root / LONGSHOT_INDEX_NAME).is_file():
        # Reload after index write so sidecar sees latest trip.json (incl. stamp).
        trip = app_context_for_trip_json(trip_json).trip_service().load(trip_json)
        write_longshot_sidecar(
            trip,
            trip_root,
            export_mode="draft",
            trip_root=trip_root,
        )
        if LONGSHOT_INDEX_NAME not in written:
            written.append(LONGSHOT_INDEX_NAME)
    return written
