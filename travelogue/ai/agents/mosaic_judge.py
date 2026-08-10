"""Mosaic Judge Agent · ACP W3 skeleton (D-ACP-15 post-beam async review).

Does **not** run inside beam search. Callers pass first-pass winner + tie
candidates after layout finishes; Judge may only choose an id already in the
candidate set (AC-ACP-08). Thumbnail/VLM path is deferred until W2.5 product
alignment — this skeleton is text-summary + optional LLM, pixel-free.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from travelogue.ai.budget import budget_for_trip
from travelogue.ai.call import chat_with_timeout
from travelogue.ai.gate import acp_instrumentation_active, check_gate
from travelogue.ai.telemetry import AgentCallRecord, record_agent_call, timed_call
from travelogue.config import AppConfig, get_config
from travelogue.llm.client import parse_json_content
from travelogue.llm.errors import LlmError
from travelogue.llm.ready import probe_llm_ready, resolve_llm_may_call

_log = logging.getLogger(__name__)

AGENT = "mosaic_judge"
PROMPT_VERSION = "mosaic-judge-v1"

SYSTEM_PROMPT = """你是马赛克拼版复核员。给定同一窗口的候选集合与第一阶段确定性赢家，
在候选 id 中选出更优者；不得发明新 id。只输出合法 JSON：
{"chosenCandidateId": "<必须来自候选>", "reason": "短句或 null"}
若无明显更优，原样返回第一阶段赢家。"""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _trip_id(trip: dict[str, Any] | None) -> str:
    if not isinstance(trip, dict):
        return ""
    return str(trip.get("tripId") or trip.get("id") or "")


def _feature(cfg: AppConfig) -> Any:
    return getattr(getattr(cfg, "ai_capability", None), "mosaic_judge", None)


def _feature_enabled(cfg: AppConfig) -> bool:
    mj = _feature(cfg)
    return bool(mj is not None and getattr(mj, "enabled", False))


def tie_epsilon(cfg: AppConfig | None = None) -> float:
    app_cfg = cfg or get_config()
    mj = _feature(app_cfg)
    try:
        return float(getattr(mj, "tie_epsilon", 0.03) if mj is not None else 0.03)
    except (TypeError, ValueError):
        return 0.03


def candidate_ids(candidates: list[Any]) -> list[str]:
    out: list[str] = []
    for c in candidates:
        if isinstance(c, dict) and c.get("id") is not None:
            out.append(str(c["id"]))
        elif isinstance(c, str) and c:
            out.append(c)
    return out


def is_tie_window(
    scores: list[float],
    *,
    epsilon: float,
) -> bool:
    """True when top1/top2 absolute score margin is strictly below epsilon."""
    if len(scores) < 2:
        return False
    ordered = sorted((float(s) for s in scores), reverse=True)
    return (ordered[0] - ordered[1]) < float(epsilon)


def _may_call_llm(cfg: AppConfig) -> tuple[bool, str]:
    if not _feature_enabled(cfg):
        return False, "mosaic_judge_disabled"
    if acp_instrumentation_active(cfg=cfg):
        decision = check_gate(cfg=cfg)
        return decision.allow, decision.reason
    if not resolve_llm_may_call(cfg=cfg):
        return False, "surface_off"
    if not probe_llm_ready(cfg=cfg):
        return False, "no_key"
    return True, "ok"


def _append_log(trip: dict[str, Any] | None, entry: dict[str, Any]) -> None:
    if trip is None:
        return
    curation = trip.setdefault("curation", {})
    if not isinstance(curation, dict):
        trip["curation"] = {}
        curation = trip["curation"]
    log = curation.setdefault("mosaicJudgeLog", [])
    if not isinstance(log, list):
        curation["mosaicJudgeLog"] = []
        log = curation["mosaicJudgeLog"]
    log.append(entry)
    # keep last 40 windows
    if len(log) > 40:
        del log[:-40]


def review_mosaic_tie(
    *,
    window_id: str,
    candidates: list[Any],
    first_pass_candidate_id: str,
    trip: dict[str, Any] | None = None,
    cfg: AppConfig | None = None,
    chat_fn: Callable[[list[dict[str, str]]], str] | None = None,
    persist: bool = True,
    score_margin: float | None = None,
) -> dict[str, Any]:
    """Async post-beam review for one tie window. Never invents candidate ids.

    Returns a log-shaped dict including ``overriddenFromFirstPass``.
    """
    app_cfg = cfg or get_config()
    trip_id = _trip_id(trip)
    ids = candidate_ids(candidates)
    first = str(first_pass_candidate_id)
    eps = tie_epsilon(app_cfg)
    if first and first not in ids:
        ids = [first, *ids]

    def _result(
        chosen: str,
        *,
        source: str,
        reason: str,
        ok: bool,
        latency_ms: float = 0.0,
        started_at: str | None = None,
        finished_at: str | None = None,
    ) -> dict[str, Any]:
        if chosen not in ids:
            chosen = first if first in ids else (ids[0] if ids else first)
        overridden = bool(chosen and first and chosen != first)
        entry = {
            "windowId": str(window_id),
            "chosenCandidateId": chosen,
            "firstPassCandidateId": first,
            "candidateIds": list(ids),
            "tieEpsilon": eps,
            "scoreMargin": score_margin,
            "overriddenFromFirstPass": overridden,
            "source": source,
            "reason": reason,
            "promptVersion": PROMPT_VERSION,
            "reviewedAt": _utc_now_iso(),
        }
        if persist:
            _append_log(trip, entry)
        rec_kwargs: dict[str, Any] = {
            "agent": AGENT,
            "source": source if source in ("llm", "cache", "fallback") else "fallback",
            "ok": ok,
            "latency_ms": latency_ms,
            "reason": reason,
            "trip_id": trip_id,
        }
        if started_at:
            rec_kwargs["started_at"] = started_at
        if finished_at:
            rec_kwargs["finished_at"] = finished_at
        record_agent_call(
            trip,
            AgentCallRecord(**rec_kwargs),
            persist_to_trip=acp_instrumentation_active(cfg=app_cfg) or _feature_enabled(app_cfg),
        )
        return entry

    if not ids:
        return _result(first, source="fallback", reason="empty_candidates", ok=False)

    allow, gate_reason = _may_call_llm(app_cfg)
    if not allow:
        return _result(first, source="fallback", reason=gate_reason, ok=False)

    # Per-trip judge call cap (stricter than global budget; SHD-ACP-01 prep)
    mj = _feature(app_cfg)
    max_calls = int(getattr(mj, "max_calls_per_trip", 4) or 0)
    if trip is not None and max_calls >= 0:
        log = ((trip.get("curation") or {}).get("mosaicJudgeLog") or [])
        llm_n = sum(
            1
            for row in log
            if isinstance(row, dict) and row.get("source") == "llm"
        )
        if llm_n >= max_calls:
            return _result(first, source="fallback", reason="judge_trip_cap", ok=False)

    budget = budget_for_trip(trip_id, cfg=app_cfg)
    if acp_instrumentation_active(cfg=app_cfg) and not budget.try_consume(AGENT):
        return _result(first, source="fallback", reason="budget_exceeded", ok=False)

    summaries: list[dict[str, Any]] = []
    for c in candidates:
        if isinstance(c, dict):
            summaries.append(
                {
                    "id": str(c.get("id") or ""),
                    "score": c.get("score"),
                    "summary": str(c.get("summary") or c.get("label") or "")[:120],
                }
            )
        else:
            summaries.append({"id": str(c), "score": None, "summary": ""})

    user_payload = {
        "windowId": window_id,
        "firstPassCandidateId": first,
        "candidates": summaries,
    }
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": json.dumps(user_payload, ensure_ascii=False, indent=2),
        },
    ]
    try:
        with timed_call() as clock:
            content = chat_with_timeout(messages, cfg=app_cfg, chat_fn=chat_fn)
        parsed = parse_json_content(content)
        if not isinstance(parsed, dict):
            raise LlmError("E_MOSAIC_JUDGE_PARSE", "non-object JSON")
        chosen = str(parsed.get("chosenCandidateId") or "").strip()
        if chosen not in ids:
            # AC-ACP-08 · refuse invented ids
            return _result(
                first,
                source="fallback",
                reason="chosen_not_in_candidates",
                ok=False,
                latency_ms=clock.latency_ms,
                started_at=clock.started_at,
                finished_at=clock.finished_at,
            )
        if not acp_instrumentation_active(cfg=app_cfg):
            budget.force_count(1)
        return _result(
            chosen,
            source="llm",
            reason="ok",
            ok=True,
            latency_ms=clock.latency_ms,
            started_at=clock.started_at,
            finished_at=clock.finished_at,
        )
    except Exception as exc:  # noqa: BLE001 — fail-open
        _log.warning("mosaic judge fail-open for %s/%s: %s", trip_id, window_id, exc)
        return _result(first, source="fallback", reason="exception", ok=False)


def collect_tie_windows_from_logs(
    raw_logs: list[Any] | None,
    *,
    epsilon: float,
) -> list[dict[str, Any]]:
    """Extract tie windows from raw mosaic decision logs (keep top3Scores)."""
    out: list[dict[str, Any]] = []
    for i, row in enumerate(raw_logs or []):
        if not isinstance(row, dict):
            continue
        scores = row.get("top3Scores") or row.get("top3_scores") or []
        patterns = row.get("top3Patterns") or row.get("top3_patterns") or []
        if not isinstance(scores, list) or len(scores) < 2:
            continue
        try:
            score_f = [float(s) for s in scores[:3]]
        except (TypeError, ValueError):
            continue
        if not is_tie_window(score_f, epsilon=epsilon):
            continue
        winner = str(
            row.get("winnerPatternId") or row.get("winner_pattern_id") or ""
        )
        if not winner and patterns:
            winner = str(patterns[0])
        window_id = str(
            row.get("windowId")
            or f"{row.get('segmentId') or 'seg'}:{row.get('windowStart')}:{row.get('windowSize')}:{i}"
        )
        cands = []
        for j, pid in enumerate(patterns):
            cands.append(
                {
                    "id": str(pid),
                    "score": score_f[j] if j < len(score_f) else None,
                    "summary": str(pid),
                }
            )
        if winner and winner not in {c["id"] for c in cands}:
            cands.insert(0, {"id": winner, "score": score_f[0] if score_f else None, "summary": winner})
        out.append(
            {
                "windowId": window_id,
                "firstPassCandidateId": winner,
                "candidates": cands,
                "scoreMargin": round(score_f[0] - score_f[1], 6) if len(score_f) >= 2 else None,
            }
        )
    return out


def run_post_compose_mosaic_judge(
    trip: dict[str, Any],
    raw_logs: list[Any] | None,
    *,
    cfg: AppConfig | None = None,
    chat_fn: Callable[[list[dict[str, str]]], str] | None = None,
    async_schedule: bool = False,
) -> list[dict[str, Any]]:
    """D-ACP-15 stage-2 entry: call only after compose/drain (never in beam).

    When ``async_schedule`` is True, reviews run on a daemon thread and this
    returns []. Otherwise runs inline (tests / dogfood sync).
    """
    app_cfg = cfg or get_config()
    if not _feature_enabled(app_cfg):
        return []
    ties = collect_tie_windows_from_logs(raw_logs, epsilon=tie_epsilon(app_cfg))
    if not ties:
        return []

    def _run() -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for tie in ties:
            try:
                entry = review_mosaic_tie(
                    window_id=str(tie["windowId"]),
                    candidates=list(tie.get("candidates") or []),
                    first_pass_candidate_id=str(tie.get("firstPassCandidateId") or ""),
                    trip=trip,
                    cfg=app_cfg,
                    chat_fn=chat_fn,
                    persist=True,
                    score_margin=tie.get("scoreMargin"),
                )
                results.append(entry)
                try:
                    from travelogue.ai.telemetry import emit_acp_event

                    emit_acp_event(
                        "mosaic_judge_invoked",
                        {
                            "tripId": _trip_id(trip),
                            "tieMargin": tie.get("scoreMargin"),
                            "overridden": bool(entry.get("overriddenFromFirstPass")),
                        },
                    )
                except Exception:  # noqa: BLE001
                    pass
            except Exception:  # noqa: BLE001 — fail-open
                _log.exception("post-compose mosaic judge failed for %s", tie.get("windowId"))
        return results

    if async_schedule:
        import threading

        threading.Thread(
            target=_run,
            daemon=True,
            name=f"mosaic-judge-{_trip_id(trip)}",
        ).start()
        return []
    return _run()
