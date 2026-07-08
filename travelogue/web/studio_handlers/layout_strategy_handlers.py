"""LSE layout strategy Inspector API (Phase 17 · W2 · read-only)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from travelogue.config import load_config, patch_config_file
from travelogue.layout_engine.capabilities import (
    capabilities_from_pack,
    effective_capabilities,
)
from travelogue.layout_engine.governance import normalize_lse_patch, pending_lse_changes
from travelogue.layout_engine.policy import load_policy
from travelogue.layout_engine.query import (
    lookup_weights_by_hash,
    read_sidecar_events,
    strategy_pack_summary,
)
from travelogue.layout_engine.registry import get_strategy_pack, list_active_strategies
from travelogue.layout_engine.rollout import lse_rollout_snapshot
from travelogue.layout_engine.runtime_store import (
    load_lse_runtime,
    rollback_lse_runtime,
    runtime_scoring_overlay,
)
from travelogue.layout_engine.sandbox import (
    cfg_lse_sandbox_pair,
    enrich_changed_screen_previews,
    sandbox_replay_trip,
)
from travelogue.layout_engine.shadow import shadow_lse_from_cfg
from travelogue.templating.admin_store import load_runtime
from travelogue.templating.config_governance import (
    approve_router_change,
    propose_layout_strategy_change,
)
from travelogue.templating.roles import require_template_role
from travelogue.web.studio_bento_preview import _trip_static_url
from travelogue.web.studio_admin_auth import require_admin_api_access, studio_authenticated
from travelogue.web.studio_errors import client_error_payload
from travelogue.web.studio_handlers.common import resolve_trip_dir_listed, studio_ctx
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol

_log = logging.getLogger(__name__)

LSE_CAPS_BOOL_FIELDS: tuple[tuple[str, str], ...] = (
    ("saliencyScoring", "saliency_scoring"),
    ("toneHarmony", "tone_harmony"),
    ("hungarianAssignment", "hungarian_assignment"),
    ("qualityUnified", "quality_unified"),
    ("segmentOrderOptimizer", "segment_order_optimizer"),
    ("implicitFeedbackExport", "implicit_feedback_export"),
    ("highlightWindows", "highlight_windows"),
    ("editorialHints", "editorial_hints"),
)

LSE_BEAT_PROFILE_OPTIONS = ("flat", "classic_magazine", "dense_mid")


def _auth(handler: StudioHandlerProtocol, *, minimum: str = "viewer") -> bool:
    ctx = studio_ctx(handler)
    if not require_admin_api_access(handler, ctx.cfg):
        return False
    ok, role, code = require_template_role(
        handler.headers,
        host=handler.studio_host,
        allow_lan=handler.studio_allow_lan,
        minimum=minimum,  # type: ignore[arg-type]
        cfg=ctx.cfg,
        studio_authenticated=studio_authenticated(handler),
    )
    if ok:
        return True
    handler._json_response(
        403,
        {
            "ok": False,
            "error": code or "E_TEMPLATE_PERMISSION_DENIED",
            "message": "排版策略 Inspector 权限不足",
            "role": role,
        },
    )
    return False


def _lse_internal(handler: StudioHandlerProtocol) -> bool:
    """AC-P16-14 · LSE Inspector internal only (loopback or flag)."""
    ctx = studio_ctx(handler)
    if getattr(ctx.cfg.studio, "layout_templates_internal", False):
        return True
    host = str(getattr(handler, "studio_host", "") or "")
    return host in ("127.0.0.1", "localhost", "::1")


def handle_layout_strategies_list(handler: StudioHandlerProtocol) -> None:
    if not _auth(handler):
        return
    if not _lse_internal(handler):
        handler._json_response(
            403,
            {
                "ok": False,
                "error": "E_LSE_INTERNAL_ONLY",
                "message": "排版策略 Inspector 仅 loopback 或 layout_templates_internal 可用",
            },
        )
        return
    ctx = studio_ctx(handler)
    pol = load_policy(ctx.cfg.layout.strategy_engine.policy_path)
    packs = list_active_strategies(policy=pol)
    rows = [strategy_pack_summary(p) for p in packs]
    lse_rt = load_lse_runtime(ctx.cfg.layout.strategy_engine.runtime_store)
    tpl_rt = load_runtime()
    from travelogue.layout_engine.rollout import lse_rollout_snapshot

    handler._json_response(
        200,
        {
            "ok": True,
            "strategies": rows,
            "runtime": {
                "enabled": ctx.cfg.layout.strategy_engine.enabled,
                "rollout": lse_rollout_snapshot(ctx.cfg),
                "defaultStrategyId": ctx.cfg.layout.strategy_engine.default_strategy_id,
                "overrides": {
                    "disableStages": list(ctx.cfg.layout.strategy_engine.overrides.disable_stages),
                    "disableProfiles": list(
                        ctx.cfg.layout.strategy_engine.overrides.disable_profiles
                    ),
                },
                "lseRuntime": lse_rt,
                "pendingLseChanges": pending_lse_changes(tpl_rt),
            },
        },
    )


def handle_layout_strategy_detail(handler: StudioHandlerProtocol, strategy_id: str) -> None:
    if not _auth(handler):
        return
    if not _lse_internal(handler):
        handler._json_response(403, {"ok": False, "error": "E_LSE_INTERNAL_ONLY"})
        return
    ctx = studio_ctx(handler)
    try:
        pack = get_strategy_pack(strategy_id, ctx.cfg.layout.strategy_engine.policy_path)
    except KeyError:
        handler._json_response(404, {"ok": False, "error": "E_STRATEGY_NOT_FOUND"})
        return
    detail = strategy_pack_summary(pack)
    detail["rawPath"] = str(pack.path)
    caps = ctx.cfg.layout.strategy_engine.capabilities
    detail["capabilities"] = {
        "saliencyScoring": caps.saliency_scoring,
        "beatProfile": caps.beat_profile,
        "toneHarmony": caps.tone_harmony,
        "hungarianAssignment": caps.hungarian_assignment,
        "segmentOrderOptimizer": caps.segment_order_optimizer,
        "implicitFeedbackExport": caps.implicit_feedback_export,
        "paceProfile": caps.pace_profile,
        "highlightWindows": caps.highlight_windows,
        "editorialHints": caps.editorial_hints,
    }
    overlay = runtime_scoring_overlay(ctx.cfg)
    pack_prof = detail.get("scoringProfile") or {}
    eff_weights = dict(pack_prof.get("weights") or {})
    eff_weights.update(overlay["weights"])
    eff_penalties = dict(pack_prof.get("penalties") or {})
    eff_penalties.update(overlay["penalties"])
    detail["runtimeOverlay"] = overlay
    detail["effectiveScoringProfile"] = {
        "weights": eff_weights,
        "penalties": eff_penalties,
    }
    detail["lseRuntime"] = load_lse_runtime(ctx.cfg.layout.strategy_engine.runtime_store)
    handler._json_response(200, {"ok": True, "strategy": detail})


def handle_layout_strategy_weights(handler: StudioHandlerProtocol, weights_hash: str) -> None:
    """AC-P17-13 · lookup persisted weights snapshot by hash."""
    if not _auth(handler):
        return
    if not _lse_internal(handler):
        handler._json_response(403, {"ok": False, "error": "E_LSE_INTERNAL_ONLY"})
        return
    snap = lookup_weights_by_hash(weights_hash)
    if not snap:
        handler._json_response(
            404,
            {
                "ok": False,
                "error": "E_LSE_WEIGHTS_NOT_FOUND",
                "weightsHash": weights_hash,
            },
        )
        return
    handler._json_response(200, {"ok": True, "weightsHash": weights_hash, "snapshot": snap})


def handle_layout_strategy_decisions(
    handler: StudioHandlerProtocol, strategy_id: str
) -> None:
    if not _auth(handler):
        return
    if not _lse_internal(handler):
        handler._json_response(403, {"ok": False, "error": "E_LSE_INTERNAL_ONLY"})
        return
    from urllib.parse import parse_qs, urlparse

    ctx = studio_ctx(handler)
    query = parse_qs(urlparse(handler.path).query)
    trip_id = (query.get("tripId") or [""])[0].strip()
    chapter_id = (query.get("chapterId") or [""])[0].strip() or None
    try:
        limit = int((query.get("limit") or ["50"])[0])
    except ValueError:
        limit = 50
    try:
        offset = int((query.get("offset") or ["0"])[0])
    except ValueError:
        offset = 0
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    if not trip_id:
        handler._json_response(400, {"ok": False, "error": "E_TRIP_ID_REQUIRED"})
        return
    trip_dir = resolve_trip_dir_listed(ctx, trip_id)
    if trip_dir is None:
        handler._json_response(404, {"ok": False, "error": "E_TRIP_NOT_FOUND"})
        return

    events, total = read_sidecar_events(
        trip_dir,
        limit=limit,
        offset=offset,
        chapter_id=chapter_id,
        strategy_id=strategy_id or None,
    )
    handler._json_response(
        200,
        {
            "ok": True,
            "strategyId": strategy_id,
            "tripId": trip_id,
            "events": events,
            "pagination": {"offset": offset, "limit": limit, "total": total},
        },
    )


def handle_layout_strategy_runtime_propose(
    handler: StudioHandlerProtocol, strategy_id: str
) -> None:
    if not _auth(handler, minimum="template_operator"):
        return
    if not _lse_internal(handler):
        handler._json_response(403, {"ok": False, "error": "E_LSE_INTERNAL_ONLY"})
        return
    ctx = studio_ctx(handler)
    try:
        get_strategy_pack(strategy_id, ctx.cfg.layout.strategy_engine.policy_path)
    except KeyError:
        handler._json_response(404, {"ok": False, "error": "E_STRATEGY_NOT_FOUND"})
        return

    payload = handler._read_json_body() or {}
    operator = str(payload.get("operator") or "studio").strip() or "studio"
    reason = str(payload.get("reason") or "").strip()
    try:
        patch = normalize_lse_patch(payload)
        change = propose_layout_strategy_change(patch, operator=operator, reason=reason)
    except ValueError as exc:
        handler._json_response(400, client_error_payload(exc))
        return
    handler._json_response(
        200,
        {
            "ok": True,
            "strategyId": strategy_id,
            "change": change,
            "runtime": load_runtime(),
        },
    )


def handle_layout_strategy_runtime_approve(handler: StudioHandlerProtocol) -> None:
    if not _auth(handler, minimum="template_operator"):
        return
    if not _lse_internal(handler):
        handler._json_response(403, {"ok": False, "error": "E_LSE_INTERNAL_ONLY"})
        return
    payload = handler._read_json_body() or {}
    change_id = str(payload.get("changeId") or "").strip()
    approver = str(payload.get("approver") or "studio").strip() or "studio"
    if not change_id:
        handler._json_response(400, {"ok": False, "error": "E_CHANGE_ID_REQUIRED"})
        return
    try:
        change = approve_router_change(change_id, approver=approver)
    except ValueError as exc:
        handler._json_response(400, client_error_payload(exc))
        return
    ctx = studio_ctx(handler)
    handler._json_response(
        200,
        {
            "ok": True,
            "change": change,
            "runtime": load_runtime(),
            "lseRuntime": load_lse_runtime(ctx.cfg.layout.strategy_engine.runtime_store),
        },
    )


def handle_layout_strategy_sandbox(handler: StudioHandlerProtocol) -> None:
    if not _auth(handler, minimum="template_operator"):
        return
    if not _lse_internal(handler):
        handler._json_response(403, {"ok": False, "error": "E_LSE_INTERNAL_ONLY"})
        return
    import json

    ctx = studio_ctx(handler)
    payload = handler._read_json_body() or {}
    trip_id = str(payload.get("tripId") or "").strip()
    if not trip_id:
        handler._json_response(400, {"ok": False, "error": "E_TRIP_ID_REQUIRED"})
        return
    trip_dir = resolve_trip_dir_listed(ctx, trip_id)
    if trip_dir is None:
        handler._json_response(404, {"ok": False, "error": "E_TRIP_NOT_FOUND"})
        return
    trip_path = trip_dir / "trip.json"
    if not trip_path.is_file():
        handler._json_response(404, {"ok": False, "error": "E_TRIP_NOT_FOUND"})
        return
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    baseline_cfg, candidate_cfg = cfg_lse_sandbox_pair(ctx.cfg)
    work_dir = trip_dir / "runs" / "lse-sandbox"
    work_dir.mkdir(parents=True, exist_ok=True)
    report = sandbox_replay_trip(
        trip,
        baseline_cfg=baseline_cfg,
        candidate_cfg=candidate_cfg,
        work_dir=work_dir,
    )
    previews = enrich_changed_screen_previews(
        trip,
        trip_dir,
        report.get("diff") or {},
        preview_url_for=lambda rel, _tid=trip_id: _trip_static_url(_tid, rel),
    )
    handler._json_response(
        200,
        {
            "ok": True,
            "tripId": trip_id,
            "mode": "lse_off_vs_on",
            **report,
            "changedPreviews": previews,
        },
    )


def handle_layout_strategy_shadow(handler: StudioHandlerProtocol) -> None:
    if not _auth(handler, minimum="template_operator"):
        return
    if not _lse_internal(handler):
        handler._json_response(403, {"ok": False, "error": "E_LSE_INTERNAL_ONLY"})
        return
    import json

    ctx = studio_ctx(handler)
    payload = handler._read_json_body() or {}
    trip_id = str(payload.get("tripId") or "").strip()
    if not trip_id:
        handler._json_response(400, {"ok": False, "error": "E_TRIP_ID_REQUIRED"})
        return
    trip_dir = resolve_trip_dir_listed(ctx, trip_id)
    if trip_dir is None:
        handler._json_response(404, {"ok": False, "error": "E_TRIP_NOT_FOUND"})
        return
    trip_path = trip_dir / "trip.json"
    if not trip_path.is_file():
        handler._json_response(404, {"ok": False, "error": "E_TRIP_NOT_FOUND"})
        return
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    work_dir = trip_dir / "runs" / "lse-shadow" / "replay"
    work_dir.mkdir(parents=True, exist_ok=True)
    report = shadow_lse_from_cfg(
        trip,
        trip_id=trip_id,
        base_cfg=ctx.cfg,
        work_dir=work_dir,
        write_sidecar=True,
    )
    previews = enrich_changed_screen_previews(
        trip,
        trip_dir,
        report.get("diff") or {},
        preview_url_for=lambda rel, _tid=trip_id: _trip_static_url(_tid, rel),
    )
    handler._json_response(
        200,
        {
            "ok": True,
            "tripId": trip_id,
            "mode": "lse_shadow_record_only",
            **report,
            "changedPreviews": previews,
        },
    )


def handle_layout_strategy_rollback(
    handler: StudioHandlerProtocol, strategy_id: str
) -> None:
    if not _auth(handler, minimum="template_admin"):
        return
    if not _lse_internal(handler):
        handler._json_response(403, {"ok": False, "error": "E_LSE_INTERNAL_ONLY"})
        return
    ctx = studio_ctx(handler)
    try:
        get_strategy_pack(strategy_id, ctx.cfg.layout.strategy_engine.policy_path)
    except KeyError:
        handler._json_response(404, {"ok": False, "error": "E_STRATEGY_NOT_FOUND"})
        return
    payload = handler._read_json_body() or {}
    try:
        steps = int(payload.get("steps") or 1)
    except (TypeError, ValueError):
        steps = 1
    try:
        rt = rollback_lse_runtime(
            steps=steps,
            store_path=ctx.cfg.layout.strategy_engine.runtime_store,
        )
    except ValueError as exc:
        handler._json_response(400, client_error_payload(exc))
        return
    handler._json_response(
        200,
        {
            "ok": True,
            "strategyId": strategy_id,
            "lseRuntime": rt,
            "revision": rt.get("revision"),
        },
    )


def _config_path(handler: StudioHandlerProtocol) -> Path:
    return handler.studio_config_path or (Path.cwd() / "config.yaml")


def _load_fresh_config(handler: StudioHandlerProtocol):
    path = _config_path(handler)
    return load_config(path if path.is_file() else None)


def _default_strategy_pack(cfg):
    se = cfg.layout.strategy_engine
    try:
        return get_strategy_pack(se.default_strategy_id, se.policy_path)
    except KeyError:
        packs = list_active_strategies(policy=load_policy(se.policy_path))
        return packs[0] if packs else None


def _cap_source_bool(from_config: bool, from_pack: bool) -> str:
    if from_config and from_pack:
        return "config+pack"
    if from_config:
        return "config"
    if from_pack:
        return "pack"
    return "default"


def _capabilities_payload(cfg, pack) -> dict[str, Any]:
    base = cfg.layout.strategy_engine.capabilities
    pack_caps = capabilities_from_pack(pack)
    effective = effective_capabilities(cfg, pack)

    caps: dict[str, Any] = {}
    for api_key, cfg_key in LSE_CAPS_BOOL_FIELDS:
        from_cfg = bool(getattr(base, cfg_key))
        from_pack = bool(getattr(pack_caps, cfg_key))
        caps[api_key] = {
            "effective": bool(getattr(effective, cfg_key)),
            "fromConfig": from_cfg,
            "fromPack": from_pack,
            "source": _cap_source_bool(from_cfg, from_pack),
            "lockedOff": from_pack and not from_cfg,
        }

    beat_cfg = str(base.beat_profile or "flat")
    beat_pack = str(pack_caps.beat_profile or "flat")
    beat_eff = str(effective.beat_profile or "flat")
    beat_from_cfg = beat_cfg not in ("", "flat")
    beat_from_pack = beat_pack not in ("", "flat") and not beat_from_cfg
    caps["beatProfile"] = {
        "effective": beat_eff,
        "fromConfig": beat_cfg,
        "fromPack": beat_pack,
        "source": _cap_source_bool(beat_from_cfg, beat_from_pack and beat_cfg in ("", "flat")),
        "lockedOff": beat_from_pack and beat_cfg in ("", "flat"),
        "options": list(LSE_BEAT_PROFILE_OPTIONS),
    }
    return caps


def _capabilities_response_body(cfg, pack) -> dict[str, Any]:
    return {
        "ok": True,
        "engineEnabled": bool(cfg.layout.strategy_engine.enabled),
        "rollout": lse_rollout_snapshot(cfg),
        "capabilities": _capabilities_payload(cfg, pack),
    }


def _lse_caps_gate(handler: StudioHandlerProtocol, *, minimum: str) -> bool:
    if not _auth(handler, minimum=minimum):
        return False
    if not _lse_internal(handler):
        handler._json_response(
            403,
            {
                "ok": False,
                "error": "E_LSE_INTERNAL_ONLY",
                "message": "LSE 能力开关页仅 loopback 或 layout_templates_internal 可用",
            },
        )
        return False
    return True


def handle_lse_capabilities_get(handler: StudioHandlerProtocol) -> None:
    if not _lse_caps_gate(handler, minimum="viewer"):
        return
    cfg = _load_fresh_config(handler)
    pack = _default_strategy_pack(cfg)
    handler._json_response(200, _capabilities_response_body(cfg, pack))


def _map_capabilities_patch(raw: dict[str, Any]) -> dict[str, Any]:
    caps: dict[str, Any] = {}
    for api_key, cfg_key in LSE_CAPS_BOOL_FIELDS:
        if api_key in raw:
            caps[cfg_key] = bool(raw[api_key])
    if "beatProfile" in raw:
        caps["beat_profile"] = str(raw["beatProfile"] or "flat").strip().lower()
    return caps


def handle_lse_capabilities_patch(handler: StudioHandlerProtocol) -> None:
    if not _lse_caps_gate(handler, minimum="template_admin"):
        return
    payload = handler._read_json_body()
    if not isinstance(payload, dict) or not payload:
        handler._json_response(400, {"ok": False, "error": "empty body"})
        return

    before_cfg = _load_fresh_config(handler)
    before_pack = _default_strategy_pack(before_cfg)
    before_body = _capabilities_response_body(before_cfg, before_pack)

    se_patch: dict[str, Any] = {}
    if "engineEnabled" in payload:
        se_patch["enabled"] = bool(payload["engineEnabled"])
    caps_raw = payload.get("capabilities")
    if isinstance(caps_raw, dict) and caps_raw:
        se_patch["capabilities"] = _map_capabilities_patch(caps_raw)

    if not se_patch:
        handler._json_response(400, {"ok": False, "error": "no writable fields"})
        return

    target = _config_path(handler)
    try:
        patch_config_file(target, {"layout": {"strategy_engine": se_patch}})
    except (ValueError, TypeError) as exc:
        handler._json_response(400, client_error_payload(exc))
        return
    except (OSError, PermissionError):
        handler._json_response(
            500,
            {"ok": False, "error": "E_STUDIO_CONFIG_WRITE", "message": "无法写入 config.yaml"},
        )
        return

    after_cfg = _load_fresh_config(handler)
    after_pack = _default_strategy_pack(after_cfg)
    after_body = _capabilities_response_body(after_cfg, after_pack)

    role = handler.headers.get("X-Template-Role") if handler.headers else None
    host = str(getattr(handler, "studio_host", "") or "")
    _log.info(
        "[lse-flags-admin] capability change by role=%s host=%s: before=%s after=%s",
        role or "unknown",
        host or "unknown",
        {
            "engineEnabled": before_body.get("engineEnabled"),
            "capabilities": before_body.get("capabilities"),
        },
        {
            "engineEnabled": after_body.get("engineEnabled"),
            "capabilities": after_body.get("capabilities"),
        },
    )

    handler._json_response(200, after_body)
