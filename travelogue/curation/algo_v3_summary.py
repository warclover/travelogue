"""ALG-V3 · effective config / observability summary (``curation.algoV3``)."""

from __future__ import annotations

from collections import Counter
from typing import Any

from travelogue.config import AppConfig, get_config
from travelogue.layout_engine.adapter import get_build_screen_calls

_NOISE_CLUSTER_ID = -1

_FUNNEL_KEYS = (
    "atom_boundary",
    "shot_group_cross",
    "shot_group_anti_slice",
    "near_scene_clone",
    "geometry_invalid",
    "main_ar_ineligible",
    "ordering_failed",
)


def _vision_effective(cfg: AppConfig) -> str:
    raw = str(getattr(cfg.vision, "enabled", "false") or "false").strip().lower()
    if raw in ("true", "1", "on", "yes"):
        return "true"
    if raw in ("false", "0", "off", "no"):
        return "off"
    return "auto_skipped"  # auto without distinguishing ran/skipped in W0


def _ssg_mode(trip: dict) -> str:
    curation = trip.get("curation") or {}
    sg = curation.get("shotGrouping")
    if not isinstance(sg, dict):
        assets = trip.get("assets") or []
        if any(isinstance(a, dict) and a.get("shotGroupId") for a in assets):
            return "empty"
        return "off"
    telem = sg.get("telemetry") if isinstance(sg.get("telemetry"), dict) else {}
    mode = str(telem.get("mode") or sg.get("mode") or "").strip().lower()
    if mode in ("scene", "look"):
        return mode
    look_n = int((sg.get("stats") or {}).get("lookGroupCount") or 0)
    if look_n > 0:
        return "look"
    groups = sg.get("groups")
    if isinstance(groups, list) and groups:
        return "scene"
    return "empty"


def _cluster_noise_ratio(trip: dict) -> float:
    assets = [a for a in (trip.get("assets") or []) if isinstance(a, dict)]
    if not assets:
        return 0.0
    with_cluster = [a for a in assets if "sceneClusterId" in a]
    if not with_cluster:
        return 0.0
    noise = sum(1 for a in with_cluster if a.get("sceneClusterId") == _NOISE_CLUSTER_ID)
    return round(noise / len(with_cluster), 4)


def _reject_funnel_top(curation: dict[str, Any]) -> dict[str, int]:
    logs = curation.get("mosaicDecisionLog")
    counts: Counter[str] = Counter()
    if isinstance(logs, list):
        for entry in logs:
            if not isinstance(entry, dict):
                continue
            for rej in entry.get("rejectedTemplates") or []:
                if not isinstance(rej, dict):
                    continue
                reason = str(rej.get("reason") or "").strip()
                if not reason:
                    continue
                if reason.startswith("shot_group"):
                    key = reason
                elif reason in _FUNNEL_KEYS:
                    key = reason
                elif reason == "near_scene_clone":
                    key = reason
                else:
                    continue
                counts[key] += 1
    # PRD §7.1 shape: keep stable keys + any observed shot_group_* 
    out = {
        "atom_boundary": int(counts.get("atom_boundary", 0)),
        "shot_group": int(
            counts.get("shot_group_cross", 0) + counts.get("shot_group_anti_slice", 0)
        ),
        "near_scene_clone": int(counts.get("near_scene_clone", 0)),
    }
    return out


def build_algo_v3_summary(
    trip: dict,
    *,
    cfg: AppConfig | None = None,
    build_screen_calls: int | None = None,
) -> dict[str, Any]:
    """Build ``curation.algoV3`` payload (ALG-V3 §7.1)."""
    app_cfg = cfg or get_config()
    curation = trip.get("curation") if isinstance(trip.get("curation"), dict) else {}

    from travelogue.llm.ready import resolve_llm_ready_summary

    llm = resolve_llm_ready_summary(cfg=app_cfg)
    degrade = llm.pop("degradeReason", None)
    degrade_reasons: list[str] = [str(degrade)] if degrade else []

    gate = getattr(app_cfg.mosaic, "near_scene_clone_gate", None)
    clone_on = bool(gate is not None and getattr(gate, "enabled", False))
    if not clone_on:
        # B7 effective: trip-level SSG off/empty or vision degraded
        # (inline vision probe — avoid curation→mosaic.clone_detection LSE edge)
        from travelogue.config._common import normalize_tri_state

        raw = getattr(getattr(app_cfg, "vision", None), "enabled", "false")
        vision_off = normalize_tri_state(raw, default="false") == "false"
        ssg = _ssg_mode(trip)
        if ssg in ("off", "empty") or vision_off:
            clone_on = bool(gate is None or getattr(gate, "conditional", True))
    scoring_on = bool(getattr(app_cfg.layout.scoring, "enabled", False))
    wall_clock = bool(
        getattr(app_cfg.layout.scoring, "wall_clock_limits_output", True)
    )

    calls = (
        int(build_screen_calls)
        if build_screen_calls is not None
        else get_build_screen_calls()
    )

    return {
        "visionEffective": _vision_effective(app_cfg),
        "ssgMode": _ssg_mode(trip),
        "clusterNoiseRatio": _cluster_noise_ratio(trip),
        "cloneGateEffective": clone_on,
        "layoutScoringEffective": scoring_on,
        "wallClockHardLimit": wall_clock and scoring_on,
        "llm": llm,
        "degradeReasons": degrade_reasons,
        "rejectFunnelTop": _reject_funnel_top(curation or {}),
        "buildScreenCalls": calls,
    }


def attach_algo_v3_summary(
    trip: dict,
    *,
    cfg: AppConfig | None = None,
) -> dict[str, Any]:
    """Write ``trip.curation.algoV3`` and return the summary."""
    summary = build_algo_v3_summary(trip, cfg=cfg)
    curation = trip.setdefault("curation", {})
    curation["algoV3"] = summary
    return summary
