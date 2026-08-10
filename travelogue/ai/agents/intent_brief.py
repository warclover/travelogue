"""Intent Brief Agent · ACP W2 / P0 (AGENT-ARCHITECTURE §17.4).

Input is a structured trip summary (no pixels). Output is advisory JSON written
to ``trip.intent.intentBrief``. Fail-open: returns ``source=fallback`` and does
not wipe an existing brief unless ``force`` replaces a successful LLM result.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from travelogue.ai.budget import budget_for_trip
from travelogue.ai.cache import content_sig, read_cached, write_cached
from travelogue.ai.gate import acp_instrumentation_active, check_gate
from travelogue.ai.telemetry import AgentCallRecord, record_agent_call, timed_call
from travelogue.config import AppConfig, get_config
from travelogue.ai.call import chat_with_timeout
from travelogue.llm.client import parse_json_content
from travelogue.llm.errors import LlmError
from travelogue.llm.ready import probe_llm_ready, resolve_llm_may_call

_log = logging.getLogger(__name__)

AGENT = "intent_brief"
PROMPT_VERSION = "intent-brief-v1"

SYSTEM_PROMPT = """你是旅行视觉游记的编辑助理。根据用户备注与相册元数据摘要，抽取结构化编辑意图。
只输出合法 JSON，不要 markdown。字段：
{
  "titleHint": "短标题建议或 null",
  "tone": "relaxed|documentary|quiet documentary|其他简短语气或 null",
  "peakMoments": ["高潮短语", "..."],
  "cullPolicy": {
    "dropScreenshots": true/false/null,
    "keepEmotionalBlur": true/false/null,
    "keepPortraits": true/false/null,
    "foodPriority": true/false/null
  },
  "clusterHints": {
    "preferFewerChapters": true/false/null
  },
  "layoutHints": {
    "arc": "five_beat|null",
    "peakChapterIndex": 1-based整数或 null,
    "preferMosaic": true/false/null
  },
  "narrativeHints": {
    "hookTheme": "短主题或 null"
  }
}
规则：不要编造未在摘要中出现的地名/事件；不确定就用 null 或空数组；peakChapterIndex 仅在能合理推断时给出。"""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _trip_id(trip: dict[str, Any]) -> str:
    return str(trip.get("tripId") or trip.get("id") or "")


def build_intent_brief_summary(trip: dict[str, Any]) -> dict[str, Any]:
    """Build a pixel-free summary for the LLM (D-ACP-07)."""
    intent = trip.get("intent") if isinstance(trip.get("intent"), dict) else {}
    user_notes = str(trip.get("userNotes") or intent.get("userNotes") or "").strip()
    travel_notes = str(intent.get("travelNotes") or "").strip()
    plan = intent.get("travelPlan") if isinstance(intent.get("travelPlan"), dict) else {}
    assets = trip.get("assets") if isinstance(trip.get("assets"), list) else []
    places: list[str] = []
    for a in assets[:400]:
        if not isinstance(a, dict):
            continue
        for key in ("place", "city", "locationName"):
            val = a.get(key)
            if isinstance(val, str) and val.strip():
                places.append(val.strip())
    # unique preserve order
    seen: set[str] = set()
    place_top: list[str] = []
    for p in places:
        if p in seen:
            continue
        seen.add(p)
        place_top.append(p)
        if len(place_top) >= 12:
            break
    voice = trip.get("voice") if isinstance(trip.get("voice"), dict) else {}
    transcript = str(voice.get("transcript") or "").strip()
    if len(transcript) > 400:
        transcript = transcript[:400] + "…"
    return {
        "userNotes": user_notes[:500],
        "travelNotes": travel_notes[:500],
        "planSummary": str(plan.get("summary") or "")[:200],
        "planCities": list(plan.get("cities") or [])[:10] if isinstance(plan.get("cities"), list) else [],
        "assetCount": len(assets),
        "placeSamples": place_top,
        "voiceTranscriptExcerpt": transcript,
        "metaTitle": str((trip.get("meta") or {}).get("title") or "")[:40],
    }


def _normalize_brief(raw: dict[str, Any], *, confidence: float, source: str) -> dict[str, Any]:
    cull = raw.get("cullPolicy") if isinstance(raw.get("cullPolicy"), dict) else {}
    cluster = raw.get("clusterHints") if isinstance(raw.get("clusterHints"), dict) else {}
    layout = raw.get("layoutHints") if isinstance(raw.get("layoutHints"), dict) else {}
    narrative = raw.get("narrativeHints") if isinstance(raw.get("narrativeHints"), dict) else {}
    peaks = raw.get("peakMoments") if isinstance(raw.get("peakMoments"), list) else []
    peak_idx = layout.get("peakChapterIndex")
    try:
        peak_idx_n = int(peak_idx) if peak_idx is not None else None
    except (TypeError, ValueError):
        peak_idx_n = None
    return {
        "titleHint": (str(raw["titleHint"]).strip()[:40] if raw.get("titleHint") else None),
        "tone": (str(raw["tone"]).strip()[:40] if raw.get("tone") else None),
        "peakMoments": [str(p).strip()[:40] for p in peaks if str(p).strip()][:8],
        "cullPolicy": {
            "dropScreenshots": cull.get("dropScreenshots"),
            "keepEmotionalBlur": cull.get("keepEmotionalBlur"),
            "keepPortraits": cull.get("keepPortraits"),
            "foodPriority": cull.get("foodPriority"),
        },
        "clusterHints": {
            "preferFewerChapters": cluster.get("preferFewerChapters"),
        },
        "layoutHints": {
            "arc": layout.get("arc"),
            "peakChapterIndex": peak_idx_n,
            "preferMosaic": layout.get("preferMosaic"),
        },
        "narrativeHints": {
            "hookTheme": (
                str(narrative["hookTheme"]).strip()[:40]
                if narrative.get("hookTheme")
                else None
            ),
        },
        "source": source,
        "confidence": float(confidence),
        "promptVersion": PROMPT_VERSION,
        "generatedAt": _utc_now_iso(),
    }


def _fallback_brief(*, reason: str) -> dict[str, Any]:
    return _normalize_brief({}, confidence=0.0, source="fallback") | {"reason": reason}


def _feature_enabled(cfg: AppConfig) -> bool:
    acp = getattr(cfg, "ai_capability", None)
    if acp is None:
        return False
    ib = getattr(acp, "intent_brief", None)
    return bool(ib is not None and getattr(ib, "enabled", False))


def _may_call_llm(cfg: AppConfig) -> tuple[bool, str]:
    if not _feature_enabled(cfg):
        return False, "intent_brief_disabled"
    if acp_instrumentation_active(cfg=cfg):
        decision = check_gate(cfg=cfg)
        return decision.allow, decision.reason
    if not resolve_llm_may_call(cfg=cfg):
        return False, "surface_off"
    if not probe_llm_ready(cfg=cfg):
        return False, "no_key"
    return True, "ok"


def run_intent_brief(
    trip: dict[str, Any],
    *,
    cfg: AppConfig | None = None,
    chat_fn: Callable[[list[dict[str, str]]], str] | None = None,
    force: bool = False,
    persist: bool = True,
    cache_dir: Any | None = None,
) -> dict[str, Any]:
    """Run Intent Brief once. Returns the brief dict (always includes source).

    When ``persist`` is True and the call succeeds (llm/cache), writes
    ``trip.intent.intentBrief``. Fallback never clears an existing brief unless
    ``force`` and we somehow got a better result (fallback still won't overwrite).
    """
    app_cfg = cfg or get_config()
    trip_id = _trip_id(trip)
    summary = build_intent_brief_summary(trip)
    allow, reason = _may_call_llm(app_cfg)
    if not allow:
        brief = _fallback_brief(reason=reason)
        record_agent_call(
            trip,
            AgentCallRecord(
                agent=AGENT,
                source="fallback",
                ok=False,
                latency_ms=0.0,
                reason=reason,
                trip_id=trip_id,
            ),
            persist_to_trip=acp_instrumentation_active(cfg=app_cfg) or _feature_enabled(app_cfg),
        )
        return brief

    if not force:
        existing = (trip.get("intent") or {}).get("intentBrief")
        if isinstance(existing, dict) and existing.get("source") in ("llm", "cache"):
            return dict(existing)

    budget = budget_for_trip(trip_id, cfg=app_cfg)
    if acp_instrumentation_active(cfg=app_cfg) and not budget.try_consume(AGENT):
        brief = _fallback_brief(reason="budget_exceeded")
        record_agent_call(
            trip,
            AgentCallRecord(
                agent=AGENT,
                source="fallback",
                ok=False,
                latency_ms=0.0,
                reason="budget_exceeded",
                trip_id=trip_id,
            ),
            persist_to_trip=True,
        )
        return brief

    sig = content_sig(summary, prompt_version=PROMPT_VERSION)
    cache_root = cache_dir
    if cache_root is None:
        acp = getattr(app_cfg, "ai_capability", None)
        cache_root = getattr(getattr(acp, "cache", None), "dir", None) or ".cache/ai"
    from pathlib import Path

    cache_path = Path(cache_root)
    cached = read_cached(cache_path, agent=AGENT, sig=sig)
    if cached is not None and not force:
        brief = _normalize_brief(cached, confidence=float(cached.get("confidence") or 0.75), source="cache")
        if persist:
            intent = trip.setdefault("intent", {})
            if not isinstance(intent, dict):
                trip["intent"] = {"version": "1"}
                intent = trip["intent"]
            if "version" not in intent:
                intent["version"] = "1"
            intent["intentBrief"] = brief
        record_agent_call(
            trip,
            AgentCallRecord(
                agent=AGENT,
                source="cache",
                ok=True,
                latency_ms=0.0,
                reason="cache_hit",
                trip_id=trip_id,
            ),
            persist_to_trip=True,
        )
        if not acp_instrumentation_active(cfg=app_cfg):
            budget.force_count(1)
        return brief

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "摘要：\n" + json.dumps(summary, ensure_ascii=False, indent=2),
        },
    ]
    try:
        with timed_call() as clock:
            content = chat_with_timeout(messages, cfg=app_cfg, chat_fn=chat_fn)
        parsed = parse_json_content(content)
        if not isinstance(parsed, dict):
            raise LlmError("E_INTENT_BRIEF_PARSE", "non-object JSON")
        brief = _normalize_brief(parsed, confidence=0.8, source="llm")
        write_cached(cache_path, agent=AGENT, sig=sig, payload=brief)
        if persist:
            intent = trip.setdefault("intent", {})
            if not isinstance(intent, dict):
                trip["intent"] = {"version": "1"}
                intent = trip["intent"]
            if "version" not in intent:
                intent["version"] = "1"
            intent["intentBrief"] = brief
        record_agent_call(
            trip,
            AgentCallRecord(
                agent=AGENT,
                source="llm",
                ok=True,
                latency_ms=clock.latency_ms,
                reason="ok",
                trip_id=trip_id,
                started_at=clock.started_at,
                finished_at=clock.finished_at,
            ),
            persist_to_trip=True,
        )
        if not acp_instrumentation_active(cfg=app_cfg):
            budget.force_count(1)
        return brief
    except Exception as exc:  # noqa: BLE001 — fail-open
        _log.warning("intent brief fail-open for %s: %s", trip_id, exc)
        brief = _fallback_brief(reason="exception")
        record_agent_call(
            trip,
            AgentCallRecord(
                agent=AGENT,
                source="fallback",
                ok=False,
                latency_ms=0.0,
                reason="exception",
                trip_id=trip_id,
            ),
            persist_to_trip=True,
        )
        return brief
