"""Template platform metrics (PRD §14)."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def metrics_path() -> Path:
    return Path.home() / ".travelogue" / "telemetry" / "template-metrics.jsonl"


def record_template_metric(name: str, **labels: Any) -> None:
    """Append metric event; never raises."""
    try:
        path = metrics_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "name": name,
            **{k: v for k, v in labels.items() if v is not None},
        }
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass


def record_admin_crud(*, action: str, operator: str, template_id: str) -> None:
    record_template_metric(
        "template.admin.crud_count",
        action=action,
        operator=operator,
        templateId=template_id,
    )


def record_admin_replay(*, operator: str, template_id: str, trip_id: str) -> None:
    record_template_metric(
        "template.admin.replay_count",
        operator=operator,
        templateId=template_id,
        tripId=trip_id,
    )


def record_discovery_event(*, template_id: str, kind: str) -> None:
    name = "template.discovery.impression_count" if kind == "impression" else "template.discovery.select_count"
    record_template_metric(name, templateId=template_id)


def record_high_risk_action(*, action: str, operator: str, template_id: str) -> None:
    record_template_metric(
        "template.admin.high_risk_action_count",
        action=action,
        operator=operator,
        templateId=template_id,
    )


def record_admin_rollback(*, level: str, operator: str, template_id: str | None = None) -> None:
    record_template_metric(
        "template.admin.rollback_count",
        level=level,
        operator=operator,
        templateId=template_id or "*",
    )


def record_review_event(*, template_id: str, outcome: str) -> None:
    record_template_metric(
        "template.review.event",
        templateId=template_id,
        outcome=outcome,
    )


def record_permission_denied(*, minimum: str, role: str) -> None:
    record_template_metric(
        "template.admin.permission_denied_count",
        minimum=minimum,
        role=role,
    )


def record_guardrail_violation(*, template_id: str, paths: list[str]) -> None:
    record_template_metric(
        "template.guardrail.violation_block_count",
        templateId=template_id,
        pathCount=len(paths),
    )


def record_route_decision(
    *,
    trip_id: str | None,
    template_id: str,
    mode: str,
    confidence: float,
    fallback_used: bool,
    duration_ms: float | None = None,
) -> None:
    record_template_metric(
        "template.route.decision",
        tripId=trip_id,
        templateId=template_id,
        mode=mode,
        confidence=round(confidence, 4),
        fallbackUsed=fallback_used,
        durationMs=duration_ms,
    )
    if fallback_used:
        record_template_metric("template.route.fallback", tripId=trip_id, templateId=template_id)
    if mode == "manual":
        record_template_metric("template.route.manual_override", tripId=trip_id, templateId=template_id)


def record_render_outcome(*, trip_id: str | None, template_id: str, ok: bool, error_code: str | None = None) -> None:
    if ok:
        record_template_metric("template.render.success", tripId=trip_id, templateId=template_id)
    else:
        record_template_metric(
            "template.render.error",
            tripId=trip_id,
            templateId=template_id,
            errorCode=error_code,
        )


class RouteTimer:
    def __init__(self) -> None:
        self._t0 = time.monotonic()

    @property
    def elapsed_ms(self) -> float:
        return round((time.monotonic() - self._t0) * 1000.0, 2)


def aggregate_metrics(*, window_hours: int = 24) -> dict[str, Any]:
    """Best-effort rollup for admin dashboard."""
    path = metrics_path()
    if not path.is_file():
        return {"windowHours": window_hours, "counts": {}, "rates": {}}
    from datetime import timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    counts: dict[str, int] = {}
    route_total = 0
    fallback = 0
    render_err = 0
    render_ok = 0
    confidences: list[float] = []
    route_durations_ms: list[float] = []
    review_submitted = 0
    review_approved = 0
    max_lines = 20_000
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) > max_lines:
            lines = lines[-max_lines:]
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            at_raw = row.get("at")
            if at_raw:
                try:
                    at = datetime.fromisoformat(str(at_raw).replace("Z", "+00:00"))
                    if at.tzinfo is None:
                        at = at.replace(tzinfo=timezone.utc)
                    if at < cutoff:
                        continue
                except ValueError:
                    pass
            name = str(row.get("name") or "")
            counts[name] = counts.get(name, 0) + 1
            if name == "template.route.decision":
                route_total += 1
                c = row.get("confidence")
                if c is not None:
                    try:
                        confidences.append(float(c))
                    except (TypeError, ValueError):
                        pass
                dm = row.get("durationMs")
                if dm is not None:
                    try:
                        route_durations_ms.append(float(dm))
                    except (TypeError, ValueError):
                        pass
            elif name == "template.route.fallback":
                fallback += 1
            elif name == "template.render.error":
                render_err += 1
            elif name == "template.render.success":
                render_ok += 1
            elif name == "template.review.event":
                outcome = str(row.get("outcome") or "")
                if outcome == "submitted":
                    review_submitted += 1
                elif outcome == "approved":
                    review_approved += 1
    except OSError:
        pass
    render_denom = render_ok + render_err
    confidences.sort()

    def _pct(vals: list[float], p: float) -> float | None:
        if not vals:
            return None
        idx = min(len(vals) - 1, max(0, int(round(p * (len(vals) - 1)))))
        return round(vals[idx], 4)

    route_p95 = _pct(route_durations_ms, 0.95)
    route_p95_slo_ms = 120.0
    return {
        "windowHours": window_hours,
        "counts": counts,
        "rates": {
            "fallback_rate": round(fallback / route_total, 4) if route_total else 0.0,
            "render_error_rate": round(render_err / render_denom, 4) if render_denom else 0.0,
            "manual_override_rate": round(
                counts.get("template.route.manual_override", 0) / route_total, 4
            )
            if route_total
            else 0.0,
            "route_total": route_total,
            "confidence_p50": _pct(confidences, 0.5),
            "confidence_p90": _pct(confidences, 0.9),
            "route_duration_p95_ms": route_p95,
            "route_p95_slo_ms": route_p95_slo_ms,
            "route_p95_within_slo": (
                route_p95 is None or route_p95 <= route_p95_slo_ms
            ),
            "review_pass_rate": round(review_approved / review_submitted, 4)
            if review_submitted
            else None,
        },
    }
