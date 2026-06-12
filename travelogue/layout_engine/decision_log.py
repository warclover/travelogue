"""Unified LSE decision log · sidecar projection (PRD §4.3, audit C)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from travelogue.layout_engine.explain import build_explain
from travelogue.util.datetime_ import utc_now_iso

SCHEMA_VERSION = 1
SIDECAR_NAME = "layout-decisions.jsonl"


@dataclass(frozen=True)
class StrategyTrace:
    strategy_id: str
    strategy_revision: int
    weights_hash: str
    algorithm_version: str

    def to_header(self) -> dict[str, Any]:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "strategyId": self.strategy_id,
            "strategyRevision": self.strategy_revision,
            "weightsHash": self.weights_hash,
            "algorithmVersion": self.algorithm_version,
        }


def layout_state_snapshot(state: Any | None) -> dict[str, Any] | None:
    if state is None:
        return None
    return {
        "nine_used": int(getattr(state, "nine_used", 0)),
        "nine_max": int(getattr(state, "nine_max", 0)),
        "nine_min": int(getattr(state, "nine_min", 0)),
        "last_kind": str(getattr(state, "last_kind", "none")),
        "layout_density": str(getattr(state, "layout_density", "balanced")),
    }


def project_mosaic_window(
    raw: dict[str, Any],
    *,
    trace: StrategyTrace | None = None,
    chapter_id: str | None = None,
) -> dict[str, Any]:
    """Map MosaicWindowLog dict → unified sidecar event."""
    patterns = list(raw.get("top3Patterns") or [])
    scores = list(raw.get("top3Scores") or [])
    candidates: list[dict[str, Any]] = []
    if patterns and scores and len(patterns) == len(scores):
        for pid, score in zip(patterns, scores):
            candidates.append(
                {
                    "patternId": pid,
                    "score": round(float(score), 4),
                    "reasons": [],
                }
            )
    elif raw.get("winnerPatternId"):
        candidates.append(
            {
                "patternId": str(raw["winnerPatternId"]),
                "score": round(float(raw.get("winnerScore") or 0.0), 4),
                "reasons": list(raw.get("winnerReasonCodes") or []),
            }
        )

    rejected: list[dict[str, str]] = []
    for item in raw.get("geometryRejectedTemplates") or []:
        if isinstance(item, dict) and item.get("templateId"):
            rejected.append(
                {
                    "patternId": str(item["templateId"]),
                    "reason": str(item.get("reason") or "geometry_invalid"),
                }
            )
    for item in raw.get("rejectedTemplates") or []:
        if isinstance(item, dict) and item.get("templateId"):
            rejected.append(
                {
                    "patternId": str(item["templateId"]),
                    "reason": str(item.get("reason") or "rejected"),
                }
            )

    winner = raw.get("winnerPatternId")
    picked = (
        {
            "patternId": str(winner),
            "score": round(float(raw.get("winnerScore") or 0.0), 4),
        }
        if winner
        else None
    )

    ch_id = chapter_id or str(raw.get("segmentId") or raw.get("chapterId") or "")
    explain = build_explain(
        raw.get("winnerPenalties"),
        weights=raw.get("scoringWeights"),
        penalty_weights=raw.get("scoringPenaltyWeights"),
    )
    slot_fallback = raw.get("slotAssignmentFallback")
    event: dict[str, Any] = {
        "chapterId": ch_id,
        "segmentId": str(raw.get("segmentId") or ch_id),
        "window": {
            "start": int(raw.get("windowStart") or 0),
            "size": int(raw.get("windowSize") or 0),
        },
        "candidates": candidates,
        "rejected": rejected,
        "picked": picked,
        "layoutState": None,
        "explain": explain,
        "meta": {
            "source": "mosaic_window",
            "plannerPath": str(raw.get("plannerPath") or "mosaic"),
            "fallbackReason": raw.get("fallbackReason") or slot_fallback,
            "slotAssignmentFallback": slot_fallback,
            "emittedAt": utc_now_iso(),
        },
    }
    if trace is not None:
        event.update(trace.to_header())
    else:
        wh = raw.get("weightsHash")
        if wh:
            event["weightsHash"] = wh
        if raw.get("scorerVersion"):
            event["algorithmVersion"] = raw["scorerVersion"]
        event["schemaVersion"] = SCHEMA_VERSION
    return event


def project_beam_bucket(
    raw: dict[str, Any],
    *,
    trace: StrategyTrace | None = None,
) -> list[dict[str, Any]]:
    """Map LayoutDecisionLog chapter dict → unified sidecar events."""
    chapter_id = str(raw.get("chapterId") or "")
    events_out: list[dict[str, Any]] = []
    for ev in raw.get("events") or []:
        if not isinstance(ev, dict):
            continue
        score = ev.get("score") if isinstance(ev.get("score"), dict) else {}
        picked_score = float(score.get("total") or 0.0)
        event: dict[str, Any] = {
            "chapterId": chapter_id,
            "segmentId": chapter_id,
            "window": {"start": 0, "size": 0},
            "candidates": [],
            "rejected": [],
            "picked": {
                "patternId": str(ev.get("variant") or "beam"),
                "score": round(picked_score, 4),
            },
            "layoutState": None,
            "explain": {"topFactors": [], "penalties": []},
            "meta": {
                "source": "beam_bucket",
                "plannerPath": str(ev.get("plannerPath") or "beam"),
                "fallbackUsed": bool(ev.get("fallbackUsed")),
                "fallbackReason": ev.get("fallbackReason"),
                "consecutivePatternFilterBypassed": ev.get(
                    "consecutivePatternFilterBypassed"
                ),
                "filteredCandidateCount": ev.get("filteredCandidateCount"),
                "maxConsecutiveStreak": ev.get("maxConsecutiveStreak"),
                "candidateCount": ev.get("candidateCount"),
                "emittedAt": ev.get("at") or utc_now_iso(),
            },
        }
        if trace is not None:
            event.update(trace.to_header())
        else:
            event["schemaVersion"] = SCHEMA_VERSION
        events_out.append(event)
    return events_out


def ingest_mosaic_logs(
    logs: list[dict[str, Any]],
    *,
    trace: StrategyTrace | None = None,
) -> list[dict[str, Any]]:
    return [project_mosaic_window(entry, trace=trace) for entry in logs if entry]


def ingest_beam_logs(
    logs: list[dict[str, Any]],
    *,
    trace: StrategyTrace | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for entry in logs:
        if isinstance(entry, dict):
            out.extend(project_beam_bucket(entry, trace=trace))
    return out


def sidecar_path(trip_dir: Path) -> Path:
    return trip_dir / "runs" / SIDECAR_NAME


def write_sidecar(
    trip_dir: Path,
    events: list[dict[str, Any]],
    *,
    max_events: int = 2000,
) -> dict[str, Any]:
    """Write unified events to runs/layout-decisions.jsonl; return trip summary fields."""
    if not events:
        return {"eventCount": 0}
    runs = trip_dir / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    path = sidecar_path(trip_dir)
    trimmed = events[-max_events:] if max_events > 0 else events
    lines = [json.dumps(ev, ensure_ascii=False, separators=(",", ":")) for ev in trimmed]
    payload = ("\n".join(lines) + "\n").encode("utf-8")
    path.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()[:16]
    return {
        "decisionLogPath": f"runs/{SIDECAR_NAME}",
        "decisionLogDigest": f"sha256:{digest}",
        "eventCount": len(trimmed),
    }


def strategy_trace_from_pack(pack: Any, *, revision: int = 0) -> StrategyTrace:
    return StrategyTrace(
        strategy_id=str(pack.id),
        strategy_revision=int(revision),
        weights_hash=str(pack.weights_hash("default")),
        algorithm_version=str(pack.algorithm_version),
    )
