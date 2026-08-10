"""ACP telemetry · write ``pipeline.runs[]`` + process-local summary · D-ACP-05."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

Source = Literal["llm", "cache", "fallback"]

_SUMMARY_LOCK = threading.Lock()
_SUMMARY: dict[str, dict[str, Any]] = {}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class AgentCallRecord:
    agent: str
    source: Source
    ok: bool
    latency_ms: float
    model: str = ""
    reason: str = ""
    trip_id: str = ""
    started_at: str = field(default_factory=_utc_now_iso)
    finished_at: str = field(default_factory=_utc_now_iso)


def record_agent_call(
    trip: dict[str, Any] | None,
    record: AgentCallRecord,
    *,
    persist_to_trip: bool | None = None,
) -> None:
    """Append a ``pipeline.runs[]`` entry when *trip* is provided; always update summary.

    When ``persist_to_trip`` is None, persist only if ACP instrumentation is active
    (W1a zero-regression: default ``ai_capability.enabled=False`` must not inflate
    ``pipeline.runs`` on legacy narrate / title_art paths).
    """
    _update_summary(record)
    if trip is None:
        return
    if persist_to_trip is None:
        try:
            from travelogue.ai.gate import acp_instrumentation_active

            persist_to_trip = acp_instrumentation_active()
        except Exception:  # noqa: BLE001
            persist_to_trip = False
    if not persist_to_trip:
        return
    try:
        from travelogue.domain.pipeline_view import append_pipeline_run
    except Exception:  # noqa: BLE001 — telemetry must never break callers
        return
    run: dict[str, Any] = {
        "runId": f"ai-{record.agent}-{record.started_at}",
        "agent": record.agent,
        "startedAt": record.started_at,
        "finishedAt": record.finished_at,
    }
    if record.model:
        run["model"] = record.model
    note_parts = [
        f"source={record.source}",
        f"ok={record.ok}",
        f"latencyMs={round(record.latency_ms, 1)}",
    ]
    if record.reason:
        note_parts.append(f"reason={record.reason}")
    run["note"] = " ".join(note_parts)
    try:
        append_pipeline_run(trip, run)
    except Exception:  # noqa: BLE001
        return


def _update_summary(record: AgentCallRecord) -> None:
    with _SUMMARY_LOCK:
        slot = _SUMMARY.setdefault(
            record.agent,
            {
                "calls": 0,
                "ok": 0,
                "fallback": 0,
                "cache": 0,
                "latencyMsSum": 0.0,
            },
        )
        slot["calls"] += 1
        if record.source == "fallback" or not record.ok:
            slot["fallback"] += 1
        elif record.source == "cache":
            slot["cache"] += 1
        if record.ok:
            slot["ok"] += 1
        slot["latencyMsSum"] += float(record.latency_ms)


def ops_summary() -> dict[str, Any]:
    """Process-local aggregate for future ``/ai-ops-admin`` (W2)."""
    with _SUMMARY_LOCK:
        out: dict[str, Any] = {}
        for agent, slot in _SUMMARY.items():
            calls = int(slot["calls"])
            out[agent] = {
                "calls": calls,
                "ok": int(slot["ok"]),
                "fallback": int(slot["fallback"]),
                "cache": int(slot["cache"]),
                "avgLatencyMs": (
                    round(float(slot["latencyMsSum"]) / calls, 1) if calls else 0.0
                ),
            }
        return out


def clear_ops_summary() -> None:
    """Test helper."""
    with _SUMMARY_LOCK:
        _SUMMARY.clear()


class timed_call:
    """Context manager measuring latency for telemetry."""

    def __init__(self) -> None:
        self.t0 = 0.0
        self.latency_ms = 0.0
        self.started_at = ""
        self.finished_at = ""

    def __enter__(self) -> timed_call:
        self.started_at = _utc_now_iso()
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *exc: object) -> None:
        self.latency_ms = (time.perf_counter() - self.t0) * 1000.0
        self.finished_at = _utc_now_iso()
