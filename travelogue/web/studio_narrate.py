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
    try:
        from travelogue.llm.user_settings import inject_secrets_into_environ, read_user_llm_secrets

        secrets = read_user_llm_secrets()
        inject_secrets_into_environ(secrets)
        if secrets.configured and secrets.provider:
            provider = secrets.provider
    except Exception:
        pass
    if provider == "stub":
        return {"llmAvailable": False, "llmProvider": "stub"}
    try:
        from travelogue.llm.client import resolve_llm_runtime

        resolve_llm_runtime(provider, cfg=app_cfg)
        return {"llmAvailable": True, "llmProvider": provider}
    except LlmError:
        return {"llmAvailable": False, "llmProvider": provider}


def resolve_studio_narrate_provider(*, cfg: AppConfig | None = None) -> str:
    """Use configured LLM for Studio narrate when credentials are available."""
    status = studio_llm_status(cfg=cfg)
    if status.get("llmAvailable"):
        return str(status["llmProvider"])
    return "stub"


def run_studio_llm_narrate(
    trip_dir: Path,
    *,
    cfg: AppConfig | None = None,
    trips_dir: Path | None = None,
) -> dict[str, str]:
    app_cfg = cfg or get_config()
    status = studio_llm_status(cfg=app_cfg)
    if not status.get("llmAvailable"):
        raise LlmError("E_LLM_AUTH", "要生成杂志感文案，请先在设置中配置写作引擎")

    trip_dir = trip_dir.resolve()
    trip_json = trip_dir / "trip.json"
    if not trip_json.is_file():
        raise FileNotFoundError(f"trip.json not found: {trip_json}")

    trips_root = (trips_dir or trip_dir.parent).resolve()
    svc = TripService(root=trips_root.parent)
    trip = svc.load(trip_json)
    provider = str(status["llmProvider"])

    run_narrate(
        trip,
        provider=provider,
        scope=app_cfg.narrative.scope,
        regenerate=True,
        cfg=app_cfg,
    )

    def mutator(t: dict) -> None:
        for key, value in trip.items():
            t[key] = value

    svc.update(trip_json, mutator)
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
        "previewRelPath": preview_path.name,
    }
