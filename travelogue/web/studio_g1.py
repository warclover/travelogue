"""Phase 4 M17 · G1 structure confirm (mode B) helpers."""

from __future__ import annotations

from pathlib import Path

from travelogue.config import AppConfig, get_config
from travelogue.demo.build import DemoError
from travelogue.orchestrator.run import run_trip
from travelogue.runtime import app_context_for_trip_json
from travelogue.services.pipeline_state import trip_status


def lock_trip_structure(trip: dict) -> None:
    """G1 confirm: structure_draft → structure_locked."""
    pipe = trip.setdefault("pipeline", {})
    locks = pipe.setdefault("locks", {})
    locks["structure"] = True
    pipe["status"] = "structure_locked"


def continue_after_g1_confirm(
    trip_json: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8766,
    cfg: AppConfig | None = None,
) -> dict:
    """Run narrate (stub) + render + preview after user confirms G1."""
    cfg = cfg or get_config()
    trip = app_context_for_trip_json(trip_json, cfg=cfg).trip_service().load(trip_json)
    status = trip_status(trip)
    if status != "structure_locked":
        raise DemoError(
            "E_PIPELINE_ORDER",
            f"continue_after_g1 requires structure_locked, got {status}",
        )
    trip_dir = trip_json.parent
    trip_id = trip_dir.name
    try:
        run_trip(
            trip_json,
            from_stage="narrate",
            until="rendered",
            skip_locked=True,
            narrate_provider="stub",
            validate=False,
            cfg=cfg,
        )
        from travelogue.render.preview import render_preview_jpg

        render_preview_jpg(trip_json, trip_root=trip_dir)
    except Exception as exc:
        code = getattr(exc, "code", "E_STUDIO_PIPELINE")
        raise DemoError(code, str(exc)) from exc
    return {
        "tripId": trip_id,
        "previewUrl": f"http://{host}:{port}/{trip_id}/index.html",
        "pipelineStatus": "rendered",
    }
