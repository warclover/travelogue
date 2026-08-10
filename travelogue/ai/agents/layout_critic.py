"""Layout Critic Agent · ACP W3 / P1 (AGENT-ARCHITECTURE §17 · AC-ACP-07).

Reads per-chapter screen summaries (no pixels). Writes advisory
``curation.layoutSuggestions[]``. Fail-open; never mutates ``chapters[]``.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from travelogue.ai.budget import budget_for_trip
from travelogue.ai.cache import content_sig, read_cached, write_cached
from travelogue.ai.gate import acp_instrumentation_active, check_gate, timeout_sec
from travelogue.ai.telemetry import AgentCallRecord, record_agent_call, timed_call
from travelogue.config import AppConfig, get_config
from travelogue.layout_contract.active_set import schema_all_pattern_ids
from travelogue.layout_contract.orientations import aspect_kind_for_asset
from travelogue.llm.client import chat_completion, parse_json_content
from travelogue.llm.errors import LlmError
from travelogue.llm.ready import probe_llm_ready, resolve_llm_may_call

_log = logging.getLogger(__name__)

AGENT = "layout_critic"
PROMPT_VERSION = "layout-critic-v1"
SUGGESTION_HARD_MAX = 36
SUGGESTION_SOFT_MAX = 28
MAX_SUGGESTIONS = 8

SYSTEM_PROMPT = """你是旅行视觉游记的排版顾问。根据各章屏摘要给出少量可执行建议。
只输出合法 JSON，不要 markdown：
{
  "suggestions": [
    {
      "chapterId": "章 id",
      "suggestedPatternId": "必须是白名单内已有 patternId",
      "suggestion": "短文案，优先≤28字，硬顶36字",
      "confidence": 0.0-1.0
    }
  ]
}
规则：
- 不得输出完整 screens[]；不得发明白名单外的 patternId
- 不确定就返回空 suggestions
- 建议应可操作（如「第2章竖图多，可改 gallery」）
- 每趟最多 8 条，优先高置信度"""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _trip_id(trip: dict[str, Any]) -> str:
    return str(trip.get("tripId") or trip.get("id") or "")


def _asset_index(trip: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for a in trip.get("assets") or []:
        if isinstance(a, dict) and a.get("id"):
            out[str(a["id"])] = a
    return out


def _screen_asset_ids(screen: dict[str, Any]) -> list[str]:
    aids = screen.get("assetIds")
    if isinstance(aids, list) and aids:
        return [str(x) for x in aids if x]
    slots = screen.get("slots")
    if isinstance(slots, list):
        out: list[str] = []
        for sl in slots:
            if isinstance(sl, dict) and sl.get("assetId"):
                out.append(str(sl["assetId"]))
        if out:
            return out
    items = screen.get("items")
    if isinstance(items, list):
        out = []
        for it in items:
            if isinstance(it, dict) and it.get("assetId"):
                out.append(str(it["assetId"]))
        return out
    return []


def build_chapter_screen_summaries(trip: dict[str, Any]) -> list[dict[str, Any]]:
    """Pixel-free per-chapter layout summary for the LLM (D-ACP-07)."""
    by_id = _asset_index(trip)
    chapters_out: list[dict[str, Any]] = []
    for ch in trip.get("chapters") or []:
        if not isinstance(ch, dict) or not ch.get("id"):
            continue
        screens_raw = ch.get("screens") if isinstance(ch.get("screens"), list) else []
        screens: list[dict[str, Any]] = []
        orient_counts = {"portrait": 0, "landscape": 0, "square": 0, "other": 0}
        mosaic_n = 0
        for sc in screens_raw[:24]:
            if not isinstance(sc, dict):
                continue
            pid = str(sc.get("patternId") or "")
            aids = _screen_asset_ids(sc)
            aspects: list[str] = []
            for aid in aids[:12]:
                asset = by_id.get(aid)
                kind = aspect_kind_for_asset(asset) if asset else "square"
                if kind in ("portrait", "tall"):
                    orient_counts["portrait"] += 1
                    aspects.append("portrait")
                elif kind == "landscape":
                    orient_counts["landscape"] += 1
                    aspects.append("landscape")
                elif kind == "square":
                    orient_counts["square"] += 1
                    aspects.append("square")
                else:
                    orient_counts["other"] += 1
                    aspects.append(kind)
            is_mosaic = "mosaic" in pid or len(aids) >= 3
            if is_mosaic:
                mosaic_n += 1
            screens.append(
                {
                    "patternId": pid,
                    "photoCount": len(aids),
                    "aspects": aspects[:8],
                    "mosaic": is_mosaic,
                }
            )
        chapters_out.append(
            {
                "chapterId": str(ch["id"]),
                "title": str(ch.get("title") or "")[:24],
                "screenCount": len(screens),
                "mosaicScreenCount": mosaic_n,
                "orientationCounts": orient_counts,
                "screens": screens,
            }
        )
    return chapters_out


def pattern_whitelist(
    trip: dict[str, Any],
    *,
    extra: Iterable[str] | None = None,
) -> set[str]:
    """Union of schema patternIds + patterns already on the trip (+ optional extras)."""
    allowed = set(schema_all_pattern_ids())
    for ch in trip.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        for sc in ch.get("screens") or []:
            if isinstance(sc, dict) and sc.get("patternId"):
                allowed.add(str(sc["patternId"]))
        if ch.get("patternId"):
            allowed.add(str(ch["patternId"]))
    if extra:
        allowed.update(str(x) for x in extra if x)
    return {p for p in allowed if p}


def _clip_suggestion(text: str) -> str:
    s = " ".join(str(text).split())
    if len(s) <= SUGGESTION_HARD_MAX:
        return s
    return s[: SUGGESTION_HARD_MAX - 1] + "…"


def _normalize_suggestions(
    raw_items: list[Any],
    *,
    whitelist: set[str],
    chapter_ids: set[str],
    source: str,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        ch_id = str(item.get("chapterId") or "").strip()
        if not ch_id or (chapter_ids and ch_id not in chapter_ids):
            continue
        pid = str(item.get("suggestedPatternId") or item.get("patternId") or "").strip()
        if not pid or pid not in whitelist:
            continue
        text = _clip_suggestion(str(item.get("suggestion") or item.get("text") or ""))
        if not text:
            continue
        try:
            conf = float(item.get("confidence") if item.get("confidence") is not None else 0.6)
        except (TypeError, ValueError):
            conf = 0.6
        conf = max(0.0, min(1.0, conf))
        out.append(
            {
                "chapterId": ch_id,
                "suggestedPatternId": pid,
                "suggestion": text,
                "accepted": False,
                "confidence": conf,
                "source": source,
            }
        )
        if len(out) >= MAX_SUGGESTIONS:
            break
    return out


def _feature_enabled(cfg: AppConfig) -> bool:
    acp = getattr(cfg, "ai_capability", None)
    if acp is None:
        return False
    lc = getattr(acp, "layout_critic", None)
    return bool(lc is not None and getattr(lc, "enabled", False))


def _may_call_llm(cfg: AppConfig) -> tuple[bool, str]:
    if not _feature_enabled(cfg):
        return False, "layout_critic_disabled"
    if acp_instrumentation_active(cfg=cfg):
        decision = check_gate(cfg=cfg)
        return decision.allow, decision.reason
    if not resolve_llm_may_call(cfg=cfg):
        return False, "surface_off"
    if not probe_llm_ready(cfg=cfg):
        return False, "no_key"
    return True, "ok"


def _persist_suggestions(trip: dict[str, Any], suggestions: list[dict[str, Any]]) -> None:
    curation = trip.setdefault("curation", {})
    if not isinstance(curation, dict):
        trip["curation"] = {}
        curation = trip["curation"]
    curation["layoutSuggestions"] = list(suggestions)


def run_layout_critic(
    trip: dict[str, Any],
    *,
    cfg: AppConfig | None = None,
    chat_fn: Callable[[list[dict[str, str]]], str] | None = None,
    force: bool = False,
    persist: bool = True,
    cache_dir: Any | None = None,
    whitelist: set[str] | None = None,
) -> dict[str, Any]:
    """Run Layout Critic once. Returns ``{suggestions, source, ...}``.

    Fallback never clears existing LLM/cache suggestions unless ``force``.
    """
    app_cfg = cfg or get_config()
    trip_id = _trip_id(trip)
    summaries = build_chapter_screen_summaries(trip)
    chapter_ids = {str(c["chapterId"]) for c in summaries}
    allow_set = whitelist if whitelist is not None else pattern_whitelist(trip)
    allow, reason = _may_call_llm(app_cfg)
    persist_telem = acp_instrumentation_active(cfg=app_cfg) or _feature_enabled(app_cfg)

    if not allow:
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
            persist_to_trip=persist_telem,
        )
        return {
            "suggestions": [],
            "source": "fallback",
            "reason": reason,
            "promptVersion": PROMPT_VERSION,
            "generatedAt": _utc_now_iso(),
        }

    if not force:
        existing = (trip.get("curation") or {}).get("layoutSuggestions")
        if isinstance(existing, list) and existing:
            sources = {str(x.get("source") or "") for x in existing if isinstance(x, dict)}
            if sources & {"llm", "cache"}:
                return {
                    "suggestions": [dict(x) for x in existing if isinstance(x, dict)],
                    "source": "existing",
                    "promptVersion": PROMPT_VERSION,
                    "generatedAt": _utc_now_iso(),
                }

    budget = budget_for_trip(trip_id, cfg=app_cfg)
    if acp_instrumentation_active(cfg=app_cfg) and not budget.try_consume(AGENT):
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
        return {
            "suggestions": [],
            "source": "fallback",
            "reason": "budget_exceeded",
            "promptVersion": PROMPT_VERSION,
            "generatedAt": _utc_now_iso(),
        }

    payload = {
        "chapters": summaries,
        "allowedPatternIds": sorted(allow_set)[:120],
    }
    sig = content_sig(payload, prompt_version=PROMPT_VERSION)
    cache_root = cache_dir
    if cache_root is None:
        acp = getattr(app_cfg, "ai_capability", None)
        cache_root = getattr(getattr(acp, "cache", None), "dir", None) or ".cache/ai"
    cache_path = Path(cache_root)
    cached = read_cached(cache_path, agent=AGENT, sig=sig)
    if cached is not None and not force:
        raw_list = cached.get("suggestions") if isinstance(cached, dict) else None
        suggestions = _normalize_suggestions(
            raw_list if isinstance(raw_list, list) else [],
            whitelist=allow_set,
            chapter_ids=chapter_ids,
            source="cache",
        )
        if persist:
            _persist_suggestions(trip, suggestions)
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
        return {
            "suggestions": suggestions,
            "source": "cache",
            "promptVersion": PROMPT_VERSION,
            "generatedAt": _utc_now_iso(),
        }

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "屏摘要与白名单：\n"
            + json.dumps(payload, ensure_ascii=False, indent=2),
        },
    ]
    try:
        with timed_call() as clock:
            if chat_fn is not None:
                content = chat_fn(messages)
            else:
                _ = timeout_sec(cfg=app_cfg)
                content = chat_completion(messages)
        parsed = parse_json_content(content)
        if not isinstance(parsed, dict):
            raise LlmError("E_LAYOUT_CRITIC_PARSE", "non-object JSON")
        raw_list = parsed.get("suggestions")
        if not isinstance(raw_list, list):
            raise LlmError("E_LAYOUT_CRITIC_PARSE", "missing suggestions[]")
        suggestions = _normalize_suggestions(
            raw_list,
            whitelist=allow_set,
            chapter_ids=chapter_ids,
            source="llm",
        )
        write_cached(
            cache_path,
            agent=AGENT,
            sig=sig,
            payload={"suggestions": suggestions},
        )
        if persist:
            _persist_suggestions(trip, suggestions)
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
        return {
            "suggestions": suggestions,
            "source": "llm",
            "promptVersion": PROMPT_VERSION,
            "generatedAt": _utc_now_iso(),
        }
    except Exception as exc:  # noqa: BLE001 — fail-open
        _log.warning("layout critic fail-open for %s: %s", trip_id, exc)
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
        return {
            "suggestions": [],
            "source": "fallback",
            "reason": "exception",
            "promptVersion": PROMPT_VERSION,
            "generatedAt": _utc_now_iso(),
        }


def accept_layout_suggestion(
    trip: dict[str, Any],
    *,
    chapter_id: str,
    suggested_pattern_id: str | None = None,
) -> dict[str, Any] | None:
    """Mark a matching suggestion accepted (advisory only; no chapters mutate)."""
    curation = trip.get("curation")
    if not isinstance(curation, dict):
        return None
    items = curation.get("layoutSuggestions")
    if not isinstance(items, list):
        return None
    ch = str(chapter_id)
    for item in items:
        if not isinstance(item, dict):
            continue
        if str(item.get("chapterId") or "") != ch:
            continue
        if suggested_pattern_id and str(item.get("suggestedPatternId") or "") != str(
            suggested_pattern_id
        ):
            continue
        item["accepted"] = True
        return dict(item)
    return None
