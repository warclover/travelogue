"""ACP W2–W3 · AI ops summary + Intent Brief / Layout Critic handlers."""

from __future__ import annotations

import copy
import html
import logging
import threading
from typing import Any

from travelogue.paths import STUDIO_TEMPLATE_DIR
from travelogue.web.studio_errors import user_message
from travelogue.web.studio_handlers.common import (
    load_trip_or_404,
    respond_if_trip_busy,
    studio_ctx,
    trip_update_or_respond,
)
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol
from travelogue.web.studio_jobs import get_job_store, run_g1_continue_job

_log = logging.getLogger(__name__)


def handle_get_ai_ops_summary(handler: StudioHandlerProtocol) -> None:
    """GET /__travelogue/ai/ops-summary — process-local ACP telemetry."""
    from travelogue.ai.telemetry import ops_summary

    handler._json_response(200, {"ok": True, "agents": ops_summary()})


def _unlock_thresholds_from_cfg() -> Any:
    from travelogue.ai.eval.unlock_gate import UnlockThresholds
    from travelogue.config import get_config

    ev = getattr(getattr(get_config(), "ai_capability", None), "eval", None)
    return UnlockThresholds(
        min_samples=int(getattr(ev, "unlock_min_samples", 30) or 30),
        config_conversion_rate=float(
            getattr(ev, "unlock_config_conversion_rate", 0.40) or 0.40
        ),
        narrate_success_rate=float(
            getattr(ev, "unlock_narrate_success_rate", 0.70) or 0.70
        ),
        channel_copy_rate=float(
            getattr(ev, "unlock_channel_copy_rate", 0.30) or 0.30
        ),
    )


def handle_get_unlock_gate(handler: StudioHandlerProtocol) -> None:
    """GET /__travelogue/ai/unlock-gate — AIR unlock recommendation from live jsonl."""
    from travelogue.ai.eval.unlock_gate import format_unlock_report, run_unlock_gate

    result = run_unlock_gate(thresholds=_unlock_thresholds_from_cfg())
    try:
        from travelogue.ai.telemetry import emit_acp_event

        emit_acp_event("ai_unlock_gate_result", {"verdict": result.verdict})
    except Exception:
        pass
    handler._json_response(
        200,
        {
            "ok": True,
            "unlockGate": result.to_dict(),
            "reportMarkdown": format_unlock_report(result),
        },
    )


def handle_post_unlock_gate(handler: StudioHandlerProtocol) -> None:
    """POST /__travelogue/ai/unlock-gate — compute from fixture metrics body."""
    from travelogue.ai.eval.unlock_gate import (
        UnlockThresholds,
        format_unlock_report,
        metrics_from_dict,
        run_unlock_gate,
    )

    body = handler._read_json_body() or {}
    thr_raw = body.get("thresholds") if isinstance(body.get("thresholds"), dict) else {}
    base = _unlock_thresholds_from_cfg()
    thresholds = UnlockThresholds(
        min_samples=int(
            thr_raw.get("minSamples")
            or thr_raw.get("min_samples")
            or base.min_samples
        ),
        config_conversion_rate=float(
            thr_raw.get("configConversionRate")
            or thr_raw.get("config_conversion_rate")
            or base.config_conversion_rate
        ),
        narrate_success_rate=float(
            thr_raw.get("narrateSuccessRate")
            or thr_raw.get("narrate_success_rate")
            or base.narrate_success_rate
        ),
        channel_copy_rate=float(
            thr_raw.get("channelCopyRate")
            or thr_raw.get("channel_copy_rate")
            or base.channel_copy_rate
        ),
    )
    if body.get("live"):
        result = run_unlock_gate(thresholds=thresholds)
    else:
        metrics_raw = (
            body.get("metrics") if isinstance(body.get("metrics"), dict) else body
        )
        metrics = metrics_from_dict(metrics_raw if isinstance(metrics_raw, dict) else {})
        metrics.source = str(
            (metrics_raw or {}).get("source") if isinstance(metrics_raw, dict) else "request"
        ) or "request"
        result = run_unlock_gate(metrics=metrics, thresholds=thresholds)
    try:
        from travelogue.ai.telemetry import emit_acp_event

        emit_acp_event("ai_unlock_gate_result", {"verdict": result.verdict})
    except Exception:
        pass
    handler._json_response(
        200,
        {
            "ok": True,
            "unlockGate": result.to_dict(),
            "reportMarkdown": format_unlock_report(result),
        },
    )


def handle_ai_ops_admin_page(handler: StudioHandlerProtocol) -> None:
    """GET /ai-ops-admin — internal ACP ops console."""
    html_path = STUDIO_TEMPLATE_DIR / "ai-ops-admin.html"
    if not html_path.is_file():
        handler.send_error(404)
        return
    page = html_path.read_text(encoding="utf-8")
    if handler.studio_token:
        token = html.escape(handler.studio_token, quote=True)
        meta = f'<meta name="studio-token" content="{token}" />'
        if '<meta name="studio-token"' not in page:
            page = page.replace("<head>", "<head>\n  " + meta, 1)
    data = page.encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("Cache-Control", "no-cache")
    handler.end_headers()
    handler.wfile.write(data)


def handle_post_intent_brief(handler: StudioHandlerProtocol, trip_id: str) -> None:
    """POST /__travelogue/trips/{id}/ai/intent-brief — run or re-run Intent Brief."""
    from travelogue.ai.agents.intent_brief import run_intent_brief
    from travelogue.config import get_config

    body = handler._read_json_body() or {}
    force = bool(body.get("force") or body.get("regenerate"))
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip0 = loaded
    trip_json = trip_dir / "trip.json"
    ctx = studio_ctx(handler)
    trip_work = copy.deepcopy(trip0)
    brief = run_intent_brief(trip_work, cfg=get_config(), force=force, persist=True)
    payload = copy.deepcopy(brief)

    def mutator(t: dict) -> dict[str, Any]:
        if brief.get("source") in ("llm", "cache"):
            intent = t.setdefault("intent", {})
            if not isinstance(intent, dict):
                intent = {"version": "1"}
                t["intent"] = intent
            if "version" not in intent:
                intent["version"] = "1"
            intent["intentBrief"] = copy.deepcopy(payload)
        return payload

    ok, _ = trip_update_or_respond(handler, ctx.trip_service(), trip_json, mutator)
    if not ok:
        return
    handler._json_response(
        200,
        {"ok": True, "tripId": trip_id, "intentBrief": payload, "source": payload.get("source")},
    )


def handle_post_layout_critic(handler: StudioHandlerProtocol, trip_id: str) -> None:
    """POST /__travelogue/trips/{id}/ai/layout-critic — run Layout Critic."""
    from travelogue.ai.agents.layout_critic import run_layout_critic
    from travelogue.config import get_config

    body = handler._read_json_body() or {}
    force = bool(body.get("force") or body.get("regenerate"))
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip0 = loaded
    trip_json = trip_dir / "trip.json"
    ctx = studio_ctx(handler)
    trip_work = copy.deepcopy(trip0)
    result = run_layout_critic(trip_work, cfg=get_config(), force=force, persist=True)
    suggestions = copy.deepcopy(result.get("suggestions") or [])

    def mutator(t: dict) -> dict[str, Any]:
        if result.get("source") in ("llm", "cache"):
            curation = t.setdefault("curation", {})
            if not isinstance(curation, dict):
                curation = {}
                t["curation"] = curation
            curation["layoutSuggestions"] = copy.deepcopy(suggestions)
        return {"suggestions": suggestions, "source": result.get("source")}

    ok, _ = trip_update_or_respond(handler, ctx.trip_service(), trip_json, mutator)
    if not ok:
        return
    handler._json_response(
        200,
        {
            "ok": True,
            "tripId": trip_id,
            "layoutSuggestions": suggestions,
            "source": result.get("source"),
            "reason": result.get("reason"),
        },
    )


def handle_post_layout_feedback(handler: StudioHandlerProtocol, trip_id: str) -> None:
    """POST .../ai/layout-feedback — G1「这章不对」(curation.layoutFeedback)."""
    from datetime import datetime, timezone

    body = handler._read_json_body() or {}
    chapter_id = str(body.get("chapterId") or "").strip()
    reason = str(body.get("reason") or "").strip()
    allowed = {
        "too_many_photos",
        "too_few_photos",
        "wrong_order",
        "style_mismatch",
        "other",
    }
    if not chapter_id or reason not in allowed:
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_LAYOUT_FEEDBACK",
                "message": "chapterId + valid reason required",
            },
        )
        return
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, _trip0 = loaded
    trip_json = trip_dir / "trip.json"
    ctx = studio_ctx(handler)
    noted = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = {"chapterId": chapter_id, "reason": reason, "notedAt": noted}

    def mutator(t: dict) -> dict[str, Any]:
        curation = t.setdefault("curation", {})
        if not isinstance(curation, dict):
            curation = {}
            t["curation"] = curation
        rows = curation.setdefault("layoutFeedback", [])
        if not isinstance(rows, list):
            rows = []
            curation["layoutFeedback"] = rows
        # replace same chapter prior note
        curation["layoutFeedback"] = [
            r
            for r in rows
            if not (isinstance(r, dict) and str(r.get("chapterId") or "") == chapter_id)
        ] + [entry]
        return entry

    ok, _ = trip_update_or_respond(handler, ctx.trip_service(), trip_json, mutator)
    if not ok:
        return
    handler._json_response(200, {"ok": True, "tripId": trip_id, "layoutFeedback": entry})


def handle_post_layout_critic_accept(handler: StudioHandlerProtocol, trip_id: str) -> None:
    """POST .../ai/layout-critic/accept — mark accepted + chapter screens replan (ACP §5.3)."""
    from travelogue.ai.agents.layout_critic import accept_layout_suggestion

    body = handler._read_json_body() or {}
    chapter_id = str(body.get("chapterId") or "").strip()
    pattern_id = body.get("suggestedPatternId") or body.get("patternId")
    pattern_id_s = str(pattern_id).strip() if pattern_id else None
    skip_replan = bool(body.get("skipReplan"))
    if not chapter_id:
        handler._json_response(
            400,
            {"ok": False, "error": "E_LAYOUT_CRITIC_ACCEPT", "message": "chapterId required"},
        )
        return
    if respond_if_trip_busy(handler, trip_id):
        return
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip0 = loaded
    trip_json = trip_dir / "trip.json"
    ctx = studio_ctx(handler)
    probe = accept_layout_suggestion(
        copy.deepcopy(trip0),
        chapter_id=chapter_id,
        suggested_pattern_id=pattern_id_s,
    )
    if probe is None:
        handler._json_response(
            404,
            {
                "ok": False,
                "error": "E_LAYOUT_CRITIC_ACCEPT",
                "message": "suggestion not found",
            },
        )
        return

    def mutator(t: dict) -> dict[str, Any]:
        hit = accept_layout_suggestion(
            t, chapter_id=chapter_id, suggested_pattern_id=pattern_id_s
        )
        return hit or probe

    ok, _ = trip_update_or_respond(handler, ctx.trip_service(), trip_json, mutator)
    if not ok:
        return
    try:
        from travelogue.ai.telemetry import emit_acp_event

        emit_acp_event(
            "layout_critic_suggestion_accepted",
            {"chapterId": chapter_id, "tripId": trip_id},
        )
    except Exception:
        pass

    if skip_replan:
        handler._json_response(
            200,
            {
                "ok": True,
                "tripId": trip_id,
                "accepted": probe,
                "replan": False,
            },
        )
        return

    svc = ctx.trip_service()

    def runner() -> dict[str, Any]:
        from travelogue.render.engine import render_trip_surfaces
        from travelogue.services.layout_accept import apply_accepted_suggestion_to_chapter

        trip = svc.load(trip_json)
        other_ids = [
            str(ch.get("id") or "")
            for ch in (trip.get("chapters") or [])
            if isinstance(ch, dict) and str(ch.get("id") or "") != chapter_id
        ]
        other_snapshots = {
            str(ch.get("id") or ""): copy.deepcopy(ch)
            for ch in (trip.get("chapters") or [])
            if isinstance(ch, dict) and str(ch.get("id") or "") != chapter_id
        }
        result = apply_accepted_suggestion_to_chapter(
            trip,
            chapter_id=chapter_id,
            suggested_pattern_id=pattern_id_s,
            cfg=ctx.cfg,
        )

        def persist(t: dict) -> None:
            # Keep pipeline lock status; only swap chapters screens from work copy.
            if "chapters" in trip:
                t["chapters"] = trip["chapters"]
            if "curation" in trip:
                t["curation"] = trip["curation"]
            # Guard: restore any chapter that was accidentally dropped
            by_id = {
                str(ch.get("id") or ""): ch
                for ch in (t.get("chapters") or [])
                if isinstance(ch, dict)
            }
            for oid in other_ids:
                if oid and oid not in by_id and oid in other_snapshots:
                    t.setdefault("chapters", []).append(other_snapshots[oid])

        svc.update(trip_json, persist)
        if result.get("ok"):
            render_trip_surfaces(
                trip_json,
                trip_dir,
                export_mode="draft",
                validate=False,
                update_pipeline=False,
                cfg=ctx.cfg,
            )
        return {
            "tripId": trip_id,
            "chapterId": chapter_id,
            "accepted": probe,
            "replan": result,
        }

    store = get_job_store()
    job = store.create_g1_continue_job()
    if job is None:
        handler._json_response(
            409,
            {
                "ok": False,
                "error": "E_STUDIO_JOB_BUSY",
                "message": user_message("E_STUDIO_JOB_BUSY"),
                "accepted": probe,
            },
        )
        return
    store.update(job, trip_id=trip_id)
    threading.Thread(
        target=lambda: run_g1_continue_job(job, runner=runner),
        daemon=True,
        name=f"layout-accept-{trip_id}",
    ).start()
    handler._json_response(
        202,
        {
            "ok": True,
            "tripId": trip_id,
            "jobId": job.job_id,
            "accepted": probe,
            "replan": True,
        },
    )


def maybe_run_intent_brief_async(trip_id: str) -> None:
    """Fire-and-forget Intent Brief after import (studio_jobs hook)."""

    def _worker() -> None:
        try:
            from travelogue.ai.agents.intent_brief import run_intent_brief
            from travelogue.config import get_config
            from travelogue.services.trip import TripService

            cfg = get_config()
            ib = getattr(getattr(cfg, "ai_capability", None), "intent_brief", None)
            if ib is None or not getattr(ib, "enabled", False):
                return
            if not trip_id:
                return
            trip_json = cfg.trips_dir / trip_id / "trip.json"
            if not trip_json.is_file():
                return
            svc = TripService(cfg.trips_dir.parent)
            trip = svc.load(trip_json)
            brief = run_intent_brief(trip, cfg=cfg, force=False, persist=True)
            if brief.get("source") not in ("llm", "cache"):
                return

            def mutator(t: dict) -> None:
                intent = t.setdefault("intent", {})
                if not isinstance(intent, dict):
                    intent = {"version": "1"}
                    t["intent"] = intent
                if "version" not in intent:
                    intent["version"] = "1"
                intent["intentBrief"] = copy.deepcopy(brief)

            svc.update(trip_json, mutator)
        except Exception:
            _log.exception("async intent brief failed for %s", trip_id)

    threading.Thread(target=_worker, daemon=True, name=f"intent-brief-{trip_id}").start()


def maybe_run_layout_critic_async(trip_id: str) -> None:
    """Fire-and-forget Layout Critic after curate (studio_jobs / curate hook)."""

    def _worker() -> None:
        try:
            from travelogue.ai.agents.layout_critic import run_layout_critic
            from travelogue.config import get_config
            from travelogue.services.trip import TripService

            cfg = get_config()
            lc = getattr(getattr(cfg, "ai_capability", None), "layout_critic", None)
            if lc is None or not getattr(lc, "enabled", False):
                return
            if not trip_id:
                return
            trip_json = cfg.trips_dir / trip_id / "trip.json"
            if not trip_json.is_file():
                return
            svc = TripService(cfg.trips_dir.parent)
            trip = svc.load(trip_json)
            result = run_layout_critic(trip, cfg=cfg, force=False, persist=True)
            if result.get("source") not in ("llm", "cache"):
                return
            suggestions = copy.deepcopy(result.get("suggestions") or [])

            def mutator(t: dict) -> None:
                curation = t.setdefault("curation", {})
                if not isinstance(curation, dict):
                    curation = {}
                    t["curation"] = curation
                curation["layoutSuggestions"] = suggestions

            svc.update(trip_json, mutator)
        except Exception:
            _log.exception("async layout critic failed for %s", trip_id)

    threading.Thread(target=_worker, daemon=True, name=f"layout-critic-{trip_id}").start()
