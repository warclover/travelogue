"""Studio LLM narrate job (F-NAR-P2-03)."""

from __future__ import annotations

from pathlib import Path

from travelogue.config import AppConfig, get_config
from travelogue.llm.errors import LlmError
from travelogue.orchestrator.run import run_trip
from travelogue.services.narrate import run_narrate
from travelogue.services.trip import TripService


def studio_llm_status(*, cfg: AppConfig | None = None) -> dict[str, object]:
    app_cfg = cfg or get_config()
    provider = (app_cfg.llm.provider or "stub").strip().lower()
    if provider == "stub":
        return {"llmAvailable": False, "llmProvider": "stub"}
    try:
        from travelogue.llm.client import resolve_llm_runtime

        resolve_llm_runtime(provider, cfg=app_cfg)
        return {"llmAvailable": True, "llmProvider": provider}
    except LlmError:
        return {"llmAvailable": False, "llmProvider": provider}


def run_studio_llm_narrate(trip_dir: Path, *, cfg: AppConfig | None = None) -> dict[str, str]:
    app_cfg = cfg or get_config()
    status = studio_llm_status(cfg=app_cfg)
    if not status.get("llmAvailable"):
        raise LlmError("E_LLM_AUTH", "未配置 LLM API Key，无法生成杂志感文案")

    trip_dir = trip_dir.resolve()
    trip_json = trip_dir / "trip.json"
    if not trip_json.is_file():
        raise FileNotFoundError(f"trip.json not found: {trip_json}")

    trips_root = trip_dir.parent
    svc = TripService(root=trips_root.parent if trips_root.name == "trips" else trips_root)
    trip = svc.load(trip_json)
    provider = str(status["llmProvider"])

    run_narrate(
        trip,
        provider=provider,
        scope=app_cfg.narrative.scope,
        regenerate=True,
        cfg=app_cfg,
    )
    svc.save(trip, trip_json)
    run_trip(
        trip_json,
        from_stage="render",
        until="rendered",
        skip_locked=True,
        validate=False,
        cfg=app_cfg,
    )
    from travelogue.render.preview import render_preview_jpg

    preview_path = render_preview_jpg(trip_json, trip_root=trip_dir)
    return {
        "tripId": trip_dir.name,
        "provider": provider,
        "previewPath": str(preview_path.resolve()),
    }
