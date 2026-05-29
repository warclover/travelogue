"""P5-8.1 · P-EVAL layout blind-review helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PEVAL_RECORD = Path(__file__).resolve().parents[2] / "docs" / "acceptance-records" / "phase5-peval.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def beam_pick_changed_count(curation: dict[str, Any] | None) -> int:
    """Count day-buckets where beam search changed screen plan vs legacy."""
    if not curation:
        return 0
    logs = curation.get("layoutDecisionLog")
    if not isinstance(logs, list):
        return 0
    changed = 0
    for entry in logs:
        if not isinstance(entry, dict):
            continue
        for event in entry.get("events") or []:
            if isinstance(event, dict) and event.get("type") == "beam_pick" and event.get("changed"):
                changed += 1
    return changed


def build_layout_peval_objective(
    legacy_trip: dict[str, Any],
    beam_trip: dict[str, Any],
    *,
    weights_preset: str,
    identical: bool,
    legacy_metrics: dict[str, Any],
    beam_metrics: dict[str, Any],
) -> dict[str, Any]:
    """Objective metrics for sealed key.json / acceptance record."""
    beam_curation = beam_trip.get("curation") or {}
    return {
        "protocol": "P5-PEVAL",
        "weightsPreset": weights_preset,
        "identicalToLegacy": identical,
        "legacyScreens": legacy_metrics.get("screenCount"),
        "beamScreens": beam_metrics.get("screenCount"),
        "legacyMetrics": legacy_metrics,
        "beamMetrics": beam_metrics,
        "beamPickChanged": beam_pick_changed_count(beam_curation),
        "degradationReason": beam_curation.get("degradationReason"),
        "arcProfile": beam_curation.get("arcProfile"),
    }


def load_peval_record(path: Path | None = None) -> dict[str, Any]:
    target = path or PEVAL_RECORD
    if target.is_file():
        data = json.loads(target.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    return {
        "recordId": "phase5-peval",
        "phase": "P5-8.1",
        "protocol": "P-EVAL",
        "description": "Phase 5 layout blind review: legacy default vs P5 beam (PHASE3B + R1)",
        "criteria": {
            "layoutBlind": {
                "name": "排版盲评 · beam 胜率",
                "threshold": "≥55% prefer beam on judged pairs",
                "status": "Pending manual review",
            },
            "G-P5-03": {
                "name": "排版质量冲刺",
                "record": "phase5-layout-sprint.json",
                "threshold": "≥8/10 tuned wins",
            },
            "phase4Intent": {
                "name": "Intent P-EVAL",
                "record": "phase4-intent.json",
            },
        },
        "pairs": [],
    }


def append_peval_pair(
    entry: dict[str, Any],
    *,
    path: Path | None = None,
) -> dict[str, Any]:
    """Append one blind-review pair; de-dupe by tripId."""
    target = path or PEVAL_RECORD
    data = load_peval_record(target)
    pairs = data.setdefault("pairs", [])
    trip_id = entry.get("tripId")
    if trip_id:
        pairs[:] = [p for p in pairs if p.get("tripId") != trip_id]
    pairs.append(entry)
    data["updatedAt"] = _utc_now()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return entry
