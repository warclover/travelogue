"""Title-art Route C / OCR adapter · ACP M3 (W1a).

Does **not** import ``cover_engine`` (D-ACP-01). Callers inject the existing
``generate_raw`` / ``ocr_verify`` callables; this module adds gate / budget /
telemetry around them.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from travelogue.ai.budget import TripLlmBudget, budget_for_trip
from travelogue.ai.gate import acp_instrumentation_active, check_gate
from travelogue.ai.telemetry import AgentCallRecord, record_agent_call, timed_call

T = TypeVar("T")

AGENT_ROUTE_C = "title_art_route_c"
AGENT_OCR = "title_art_ocr_verify"


class AcpSkipRouteC(RuntimeError):
    """ACP gate/budget blocked Route C — caller should fall back to Route B."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _trip_id(trip: dict[str, Any] | None) -> str:
    if not isinstance(trip, dict):
        return ""
    return str(trip.get("tripId") or trip.get("id") or "")


def call_generate_raw(
    generate_raw: Callable[..., T],
    *args: Any,
    trip: dict[str, Any] | None = None,
    budget: TripLlmBudget | None = None,
    cfg: Any | None = None,
    telemetry_model: str = "",
    **kwargs: Any,
) -> T:
    """Invoke Route C ``generate_raw`` under ACP instrumentation.

    When ``ai_capability.enabled`` is False (W1a default), this is a pure
    pass-through plus optional telemetry — zero behavior change.

    When enabled, enforces D-ACP-14 gate + D-ACP-04 budget; blocked calls raise
    :class:`AcpSkipRouteC` so engine fail-opens to Route B.
    """
    active = acp_instrumentation_active(cfg=cfg)
    if active:
        decision = check_gate(cfg=cfg)
        if not decision.allow:
            record_agent_call(
                trip,
                AgentCallRecord(
                    agent=AGENT_ROUTE_C,
                    source="fallback",
                    ok=False,
                    latency_ms=0.0,
                    model=telemetry_model,
                    reason=decision.reason,
                    trip_id=_trip_id(trip),
                ),
            )
            raise AcpSkipRouteC(decision.reason)
        b = budget or budget_for_trip(_trip_id(trip), cfg=cfg)
        if not b.try_consume(AGENT_ROUTE_C):
            record_agent_call(
                trip,
                AgentCallRecord(
                    agent=AGENT_ROUTE_C,
                    source="fallback",
                    ok=False,
                    latency_ms=0.0,
                    model=telemetry_model,
                    reason="budget_exceeded",
                    trip_id=_trip_id(trip),
                ),
            )
            raise AcpSkipRouteC("budget_exceeded")

    err: BaseException | None = None
    result: T | None = None
    with timed_call() as clock:
        try:
            result = generate_raw(*args, **kwargs)
        except BaseException as exc:  # noqa: BLE001 — re-raised after telemetry
            err = exc
    record_agent_call(
        trip,
        AgentCallRecord(
            agent=AGENT_ROUTE_C,
            source="llm",
            ok=err is None,
            latency_ms=clock.latency_ms,
            model=telemetry_model,
            reason="ok" if err is None else "exception",
            trip_id=_trip_id(trip),
            started_at=clock.started_at,
            finished_at=clock.finished_at,
        ),
    )
    if err is not None:
        raise err
    if not active and budget is None and trip is not None:
        # Soft-count for observability when ACP gate is off.
        budget_for_trip(_trip_id(trip), cfg=cfg).force_count(1)
    assert result is not None
    return result


def call_ocr_verify(
    ocr_verify: Callable[..., bool],
    *args: Any,
    trip: dict[str, Any] | None = None,
    budget: TripLlmBudget | None = None,
    cfg: Any | None = None,
    telemetry_model: str = "",
    **kwargs: Any,
) -> bool:
    """Invoke OCR verify under ACP telemetry (and budget when ACP enabled)."""
    active = acp_instrumentation_active(cfg=cfg)
    if active:
        decision = check_gate(cfg=cfg)
        if not decision.allow:
            record_agent_call(
                trip,
                AgentCallRecord(
                    agent=AGENT_OCR,
                    source="fallback",
                    ok=False,
                    latency_ms=0.0,
                    model=telemetry_model,
                    reason=decision.reason,
                    trip_id=_trip_id(trip),
                ),
            )
            return False
        b = budget or budget_for_trip(_trip_id(trip), cfg=cfg)
        if not b.try_consume(AGENT_OCR):
            record_agent_call(
                trip,
                AgentCallRecord(
                    agent=AGENT_OCR,
                    source="fallback",
                    ok=False,
                    latency_ms=0.0,
                    model=telemetry_model,
                    reason="budget_exceeded",
                    trip_id=_trip_id(trip),
                ),
            )
            return False

    matched = False
    err: BaseException | None = None
    with timed_call() as clock:
        try:
            matched = bool(ocr_verify(*args, **kwargs))
        except BaseException as exc:  # noqa: BLE001 — OCR fail-open to False
            err = exc
    record_agent_call(
        trip,
        AgentCallRecord(
            agent=AGENT_OCR,
            source="llm",
            ok=err is None and matched,
            latency_ms=clock.latency_ms,
            model=telemetry_model,
            reason=(
                "exception"
                if err is not None
                else ("ok" if matched else "mismatch")
            ),
            trip_id=_trip_id(trip),
            started_at=clock.started_at,
            finished_at=clock.finished_at,
        ),
    )
    return False if err is not None else matched
