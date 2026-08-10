"""Studio LLM narrate job (F-NAR-P2-03)."""

from __future__ import annotations

from pathlib import Path

from travelogue.config import AppConfig, get_config
from travelogue.config._common import capability_allows, normalize_tri_state
from travelogue.llm.errors import LlmError
from travelogue.llm.ready import (
    probe_llm_ready,
    resolve_llm_may_call,
    resolve_llm_ready_summary,
    resolve_ready_provider,
    studio_llm_status,
)
from travelogue.orchestrator.run import run_trip
from travelogue.services.narrate import run_narrate
from travelogue.services.trip import TripService

# Re-export Ready helpers for Studio callers (implementation lives in llm.ready).
__all__ = [
    "probe_llm_ready",
    "resolve_llm_may_call",
    "resolve_llm_ready_summary",
    "resolve_studio_narrate_provider",
    "resolve_studio_narrate_provider_if_ready",
    "run_studio_llm_narrate",
    "studio_llm_status",
]


def resolve_studio_narrate_provider(
    *,
    cfg: AppConfig | None = None,
    force_stub: bool = False,
) -> str:
    """Resolve narrate provider for Studio **import** / G1 continue.

    Product contract (ALG-V3 §3.5 / D-DLLM-02):
    - Default ``prefer_llm_when_ready=false`` → stub.
    - LLM only when ``prefer ∧ ready ∧ may_call`` (and not ``force_stub``).
    - NAS MayCall is false unless Surface/dark is on.
    """
    if force_stub:
        return "stub"
    app_cfg = cfg or get_config()
    prefer = bool(getattr(app_cfg.llm, "prefer_llm_when_ready", False))
    if not prefer:
        return "stub"
    if not resolve_llm_may_call(cfg=app_cfg):
        return "stub"
    capability = normalize_tri_state(getattr(app_cfg.llm, "capability", "auto"), default="auto")
    probe_ready = probe_llm_ready(cfg=app_cfg)
    allowed, _degrade = capability_allows(capability, ready=probe_ready)
    if not allowed:
        return "stub"
    return resolve_ready_provider(cfg=app_cfg)


def resolve_studio_narrate_provider_if_ready(*, cfg: AppConfig | None = None) -> str:
    """Return configured LLM provider when credentials resolve; else stub.

    Not used by import. Kept for callers that intentionally want LLM-when-ready.
    Still respects MayCall (NAS) so dark-only surfaces can open the path.
    """
    app_cfg = cfg or get_config()
    if not resolve_llm_may_call(cfg=app_cfg):
        return "stub"
    status = studio_llm_status(cfg=app_cfg)
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
    if not resolve_llm_may_call(cfg=app_cfg):
        from travelogue.web.studio_errors import user_message

        raise LlmError("E_AI_SURFACE_DISABLED", user_message("E_AI_SURFACE_DISABLED"))
    status = studio_llm_status(cfg=app_cfg)
    if not status.get("llmAvailable"):
        from travelogue.web.studio_errors import user_message

        raise LlmError("E_LLM_AUTH", user_message("E_LLM_AUTH"))

    trip_dir = trip_dir.resolve()
    trip_json = trip_dir / "trip.json"
    if not trip_json.is_file():
        raise FileNotFoundError(f"trip.json not found: {trip_json}")

    trips_root = (trips_dir or trip_dir.parent).resolve()
    svc = TripService(root=trips_root.parent)
    trip = svc.load(trip_json)
    provider = str(status["llmProvider"])

    # BE-SFI-06 · 刷新锁定 Copy sparse（frame）；禁止升 full
    narrate_result = run_narrate(
        trip,
        provider=provider,
        scope="frame",
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
    from travelogue.domain.narrate_diff import summarize_narrate_fields
    from travelogue.render.preview import render_preview_jpg

    preview_path = render_preview_jpg(trip_json, trip_root=trip_dir)
    fields = list(getattr(narrate_result, "fields_updated", None) or [])
    diff = summarize_narrate_fields(fields)
    return {
        "tripId": trip_dir.name,
        "provider": provider,
        "previewRelPath": preview_path.name,
        # SNR D-SNR-06 · 供 FE 成功后 diff 条（空则不展示假 diff）
        "fieldsUpdated": fields,
        "diffSummary": diff,
    }
