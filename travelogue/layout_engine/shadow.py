"""LSE shadow dual-track: record candidate layout without mutating trip (PRD §9.2 · W3b-09)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from travelogue.config import AppConfig
from travelogue.layout_engine.sandbox import cfg_lse_sandbox_pair, sandbox_replay_trip
from travelogue.util.datetime_ import utc_now_iso

SHADOW_SIDECAR = "lse-shadow.json"
PERF_BUDGET_PCT = 15.0


def _mosaic5_rate(dist: dict[str, float]) -> float:
    return float(dist.get("screen-mosaic-5-main-hero-plus-4") or 0.0)


def shadow_metrics(report: dict[str, Any]) -> dict[str, Any]:
    base_dist = (report.get("baseline") or {}).get("patternDistribution") or {}
    cand_dist = (report.get("candidate") or {}).get("patternDistribution") or {}
    return {
        "patternDiversityBaseline": len(base_dist),
        "patternDiversityCandidate": len(cand_dist),
        "mosaic5ExposureBaseline": round(_mosaic5_rate(base_dist), 4),
        "mosaic5ExposureCandidate": round(_mosaic5_rate(cand_dist), 4),
        "diffRate": report.get("diffRate"),
        "changedCount": (report.get("diff") or {}).get("changedCount"),
    }


def shadow_lse_replay_trip(
    trip: dict,
    *,
    trip_id: str,
    baseline_cfg: AppConfig,
    candidate_cfg: AppConfig,
    work_dir: Path,
    write_sidecar: bool = True,
) -> dict[str, Any]:
    """Replay LSE off vs on; optionally persist telemetry sidecar (does not modify trip.json)."""
    report = sandbox_replay_trip(
        trip,
        baseline_cfg=baseline_cfg,
        candidate_cfg=candidate_cfg,
        work_dir=work_dir,
    )
    payload: dict[str, Any] = {
        "shadowActive": True,
        "recordOnly": True,
        "tripId": trip_id,
        "mode": "lse_off_vs_on",
        "emittedAt": utc_now_iso(),
        "metrics": shadow_metrics(report),
        **report,
    }
    if write_sidecar:
        sidecar_dir = work_dir.parent
        sidecar_dir.mkdir(parents=True, exist_ok=True)
        path = sidecar_dir / SHADOW_SIDECAR
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        payload["sidecarPath"] = str(path)
    return payload


def shadow_lse_from_cfg(
    trip: dict,
    *,
    trip_id: str,
    base_cfg: AppConfig,
    work_dir: Path,
    write_sidecar: bool = True,
) -> dict[str, Any]:
    baseline_cfg, candidate_cfg = cfg_lse_sandbox_pair(base_cfg)
    return shadow_lse_replay_trip(
        trip,
        trip_id=trip_id,
        baseline_cfg=baseline_cfg,
        candidate_cfg=candidate_cfg,
        work_dir=work_dir,
        write_sidecar=write_sidecar,
    )
