"""SHD-ACP-01 · recommend mosaic Judge tie_epsilon from score margins."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TieEpsilonStats:
    window_count: int
    trip_count: int
    margins: list[float]
    p50: float | None
    p90: float | None
    recommended_epsilon: float
    triggers_at_recommended: int
    mean_triggers_per_trip: float


def _percentile(sorted_vals: list[float], p: float) -> float | None:
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def margins_from_logs(raw_logs: list[Any] | None) -> list[float]:
    out: list[float] = []
    for row in raw_logs or []:
        if not isinstance(row, dict):
            continue
        scores = row.get("top3Scores") or row.get("top3_scores") or []
        if not isinstance(scores, list) or len(scores) < 2:
            continue
        try:
            a, b = float(scores[0]), float(scores[1])
        except (TypeError, ValueError):
            continue
        out.append(abs(a - b))
    return out


def compute_tie_epsilon_stats(
    logs_by_trip: dict[str, list[Any]] | list[Any],
    *,
    default_epsilon: float = 0.03,
    target_trigger_rate: float = 0.15,
) -> TieEpsilonStats:
    """Recommend ε so that roughly ``target_trigger_rate`` of windows are ties.

    Also reports mean triggers/trip at the recommended ε (SHD-ACP-01).
    """
    if isinstance(logs_by_trip, list):
        logs_by_trip = {"_": logs_by_trip}
    all_margins: list[float] = []
    per_trip_margins: dict[str, list[float]] = {}
    for tid, logs in logs_by_trip.items():
        m = margins_from_logs(logs)
        per_trip_margins[str(tid)] = m
        all_margins.extend(m)
    ordered = sorted(all_margins)
    p50 = _percentile(ordered, 50)
    p90 = _percentile(ordered, 90)
    if not ordered:
        return TieEpsilonStats(
            window_count=0,
            trip_count=len(logs_by_trip),
            margins=[],
            p50=None,
            p90=None,
            recommended_epsilon=float(default_epsilon),
            triggers_at_recommended=0,
            mean_triggers_per_trip=0.0,
        )
    # Choose smallest ε whose cumulative fraction >= target (from low margins).
    target_n = max(1, int(round(len(ordered) * max(0.0, min(1.0, target_trigger_rate)))))
    recommended = ordered[min(target_n - 1, len(ordered) - 1)]
    recommended = max(0.005, min(0.2, float(recommended)))
    triggers = sum(1 for m in ordered if m < recommended)
    trip_triggers = [
        sum(1 for m in ms if m < recommended) for ms in per_trip_margins.values()
    ]
    mean_t = sum(trip_triggers) / max(1, len(trip_triggers))
    return TieEpsilonStats(
        window_count=len(ordered),
        trip_count=len(logs_by_trip),
        margins=ordered,
        p50=p50,
        p90=p90,
        recommended_epsilon=round(recommended, 4),
        triggers_at_recommended=triggers,
        mean_triggers_per_trip=round(mean_t, 3),
    )
