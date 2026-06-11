#!/usr/bin/env python3
"""P19 · explicit_single fallback rate on golden trips (S3 Gate <5%).

Usage:
  python scripts/p19_explicit_fallback_audit.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from travelogue.eval.golden_trips import resolve_existing_golden_trips

from book_quality_baseline import _curate_trip, _p19_candidate_cfg
from travelogue.config import get_config


def _audit_mosaic_logs(logs: list[dict]) -> dict[str, Any]:
    explicit = 0
    total_windows = len(logs)
    reasons: dict[str, int] = {}
    for entry in logs:
        path = str(entry.get("plannerPath") or "")
        reason = str(entry.get("fallbackReason") or "")
        if path == "explicit_single" or reason == "EXPLICIT_SINGLE_RHYTHM":
            explicit += 1
            key = reason or path
            reasons[key] = reasons.get(key, 0) + 1
    rate = explicit / total_windows if total_windows else 0.0
    return {
        "mosaicWindows": total_windows,
        "explicitFallbackCount": explicit,
        "explicitFallbackRate": round(rate, 4),
        "fallbackReasons": reasons,
    }


def _audit_layout_decision_logs(logs: list[dict]) -> dict[str, Any]:
    explicit = 0
    total_buckets = 0
    reasons: dict[str, int] = {}
    for entry in logs:
        for event in entry.get("events") or []:
            if event.get("type") != "beam_pick":
                continue
            total_buckets += 1
            path = str(event.get("plannerPath") or "")
            reason = str(event.get("fallbackReason") or "")
            if path == "explicit_single" or reason == "EXPLICIT_SINGLE_RHYTHM":
                explicit += 1
                key = reason or path
                reasons[key] = reasons.get(key, 0) + 1
    rate = explicit / total_buckets if total_buckets else 0.0
    return {
        "bucketDecisions": total_buckets,
        "explicitFallbackCount": explicit,
        "explicitFallbackRate": round(rate, 4),
        "fallbackReasons": reasons,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="P19 explicit fallback audit")
    parser.add_argument("trip_id", nargs="*", help="Subset of golden trips")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / ".cache" / "book-quality" / "explicit-fallback-audit.json",
    )
    parser.add_argument(
        "--max-rate",
        type=float,
        default=0.05,
        help="Gate threshold for explicit fallback rate",
    )
    args = parser.parse_args()

    cfg = _p19_candidate_cfg(get_config(reload=True))
    rows = [r for r in resolve_existing_golden_trips(root=ROOT) if r["exists"]]
    if args.trip_id:
        wanted = set(args.trip_id)
        rows = [r for r in rows if r["tripId"] in wanted]

    per_trip: list[dict[str, Any]] = []
    for row in rows:
        tid = row["tripId"]
        trip = json.loads(
            Path(row["tripDir"]).joinpath("trip.json").read_text(encoding="utf-8")
        )
        work = ROOT / ".cache" / "book-quality" / "fallback-audit-work" / tid
        body = _curate_trip(trip, work_dir=work, cfg=cfg)
        curation = body.get("curation") or {}
        mosaic_logs = list(curation.get("mosaicDecisionLog") or [])
        layout_logs = list(curation.get("layoutDecisionLog") or [])
        mosaic_audit = _audit_mosaic_logs(mosaic_logs)
        layout_audit = _audit_layout_decision_logs(layout_logs)
        total_units = mosaic_audit["mosaicWindows"] + layout_audit["bucketDecisions"]
        explicit = mosaic_audit["explicitFallbackCount"] + layout_audit["explicitFallbackCount"]
        rate = explicit / total_units if total_units else 0.0
        screens = sum(len(ch.get("screens") or []) for ch in body.get("chapters") or [])
        per_trip.append(
            {
                "tripId": tid,
                "screenCount": screens,
                "mosaicWindows": mosaic_audit["mosaicWindows"],
                "bucketDecisions": layout_audit["bucketDecisions"],
                "explicitFallbackCount": explicit,
                "explicitFallbackRate": round(rate, 4),
                "fallbackReasons": {
                    **mosaic_audit["fallbackReasons"],
                    **layout_audit["fallbackReasons"],
                },
            }
        )
        print(
            f"{tid}: explicit {explicit}/{total_units} "
            f"({rate:.1%}) screens={screens}"
        )

    rates = [t["explicitFallbackRate"] for t in per_trip if t["mosaicWindows"] + t["bucketDecisions"] > 0]
    median_rate = sorted(rates)[len(rates) // 2] if rates else 0.0
    report = {
        "trips": per_trip,
        "medianExplicitFallbackRate": round(median_rate, 4),
        "maxRateGate": args.max_rate,
        "withinGate": median_rate <= args.max_rate,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Median rate {median_rate:.1%} (gate <= {args.max_rate:.0%}) -> {args.out}")
    return 0 if report["withinGate"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
