"""ACP W2–W3 · AI ops summary + Intent Brief / Layout Critic handlers."""

from __future__ import annotations

import copy
import html
import logging
import threading
from typing import Any

from travelogue.paths import STUDIO_TEMPLATE_DIR
from travelogue.web.studio_handlers.common import (
    load_trip_or_404,
    studio_ctx,
    trip_update_or_respond,
)
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol

_log = logging.getLogger(__name__)


def handle_get_ai_ops_summary(handler: StudioHandlerProtocol) -> None:
    """GET /__travelogue/ai/ops-summary — process-local ACP telemetry."""
    from travelogue.ai.telemetry import ops_summary

    handler._json_response(200, {"ok": True, "agents": ops_summary()})


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


def handle_post_layout_critic_accept(handler: StudioHandlerProtocol, trip_id: str) -> None:
    """POST .../ai/layout-critic/accept — mark suggestion accepted (advisory only)."""
    from travelogue.ai.agents.layout_critic import accept_layout_suggestion

    body = handler._read_json_body() or {}
    chapter_id = str(body.get("chapterId") or "").strip()
    pattern_id = body.get("suggestedPatternId") or body.get("patternId")
    pattern_id_s = str(pattern_id).strip() if pattern_id else None
    if not chapter_id:
        handler._json_response(
            400,
            {"ok": False, "error": "E_LAYOUT_CRITIC_ACCEPT", "message": "chapterId required"},
        )
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
    handler._json_response(
        200,
        {
            "ok": True,
            "tripId": trip_id,
            "accepted": probe,
            "note": "advisory_only_no_auto_replan",
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
