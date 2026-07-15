"""Phase 4 M17 · G1 structure confirm (mode B) helpers."""

from __future__ import annotations

import logging
from pathlib import Path

from travelogue.config import AppConfig, get_config
from travelogue.demo.build import DemoError
from travelogue.orchestrator.run import run_trip
from travelogue.runtime import app_context_for_trip_json
from travelogue.services.pipeline_state import lock_structure, trip_status

_log = logging.getLogger(__name__)


def lock_trip_structure(trip: dict) -> None:
    """G1 confirm: structure_draft → structure_locked."""
    lock_structure(trip)


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
    from travelogue.web.studio_narrate import resolve_studio_narrate_provider

    narrate_provider = resolve_studio_narrate_provider(cfg=cfg, force_stub=True)
    try:
        run_trip(
            trip_json,
            from_stage="narrate",
            until="rendered",
            skip_locked=True,
            narrate_provider=narrate_provider,
            validate=False,
            cfg=cfg,
        )
        from travelogue.render.preview import render_preview_jpg

        render_preview_jpg(trip_json, trip_root=trip_dir)
    except Exception as exc:
        code = getattr(exc, "code", "E_STUDIO_PIPELINE")
        if code == "E_LLM_AUTH" and narrate_provider != "stub":
            _log.warning(
                "studio g1 continue narrate hit E_LLM_AUTH with provider=%s; degrading to stub",
                narrate_provider,
            )
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
            except Exception as stub_exc:
                stub_code = getattr(stub_exc, "code", "E_STUDIO_PIPELINE")
                raise DemoError(stub_code, str(stub_exc)) from stub_exc
        else:
            raise DemoError(code, str(exc)) from exc
    return {
        "tripId": trip_id,
        "previewUrl": f"http://{host}:{port}/{trip_id}/index.html",
        "pipelineStatus": "rendered",
    }
