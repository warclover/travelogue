#!/usr/bin/env python3
"""P19 curate timing profile vs P16-default baseline path.

Usage:
  python scripts/p19_curate_profile.py
  python scripts/p19_curate_profile.py demo-2025
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from travelogue.config import AppConfig, get_config
from travelogue.eval.golden_trips import resolve_existing_golden_trips

from book_quality_baseline import _curate_trip, _p16_cfg


def _percentile(samples: list[float], pct: float) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    idx = int(round((pct / 100.0) * (len(ordered) - 1)))
    return ordered[idx]


def _profile_rows(
    rows: list[dict],
    *,
    label: str,
    cfg: AppConfig,
) -> dict:
    timings: list[float] = []
    per_trip: list[dict] = []
    for row in rows:
        tid = row["tripId"]
        trip = json.loads(Path(row["tripDir"]).joinpath("trip.json").read_text(encoding="utf-8"))
        work = ROOT / ".cache" / "book-quality" / "profile-work" / label / tid
        start = time.perf_counter()
        _curate_trip(trip, work_dir=work, cfg=cfg)
        elapsed = time.perf_counter() - start
        timings.append(elapsed)
        per_trip.append({"tripId": tid, "seconds": round(elapsed, 3)})
        print(f"[{label}] {tid}: {elapsed:.2f}s")
    return {
        "label": label,
        "trips": per_trip,
        "count": len(timings),
        "p50Seconds": round(_percentile(timings, 50), 3),
        "p95Seconds": round(_percentile(timings, 95), 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="P19 curate latency profile")
    parser.add_argument("trip_id", nargs="*", help="Subset of golden trips")
    parser.add_argument(
        "--compare-p16",
        action="store_true",
        help="Profile current config vs P16-default baseline on the same trips",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / ".cache" / "book-quality" / "curate-profile.json",
    )
    args = parser.parse_args()

    base_cfg = get_config(reload=True)
    cfg = _p16_cfg(base_cfg) if not args.compare_p16 else base_cfg
    rows = [r for r in resolve_existing_golden_trips(root=ROOT) if r["exists"]]
    if args.trip_id:
        wanted = set(args.trip_id)
        rows = [r for r in rows if r["tripId"] in wanted]

    if not rows:
        print("No trips to profile", file=sys.stderr)
        return 1

    if args.compare_p16:
        current = _profile_rows(rows, label="current", cfg=base_cfg)
        p16 = _profile_rows(rows, label="p16", cfg=_p16_cfg(base_cfg))
        p16_p95 = float(p16["p95Seconds"])
        cur_p95 = float(current["p95Seconds"])
        p95_delta = cur_p95 - p16_p95
        p95_increase_pct = (p95_delta / p16_p95 * 100.0) if p16_p95 > 0 else 0.0
        report = {
            "compareP16": True,
            "current": current,
            "p16Baseline": p16,
            "p95DeltaSeconds": round(p95_delta, 3),
            "p95IncreasePct": round(p95_increase_pct, 2),
            "p95WithinGate": cur_p95 <= p16_p95 * 1.15,
            "gateThreshold": "current_p95 <= p16_p95 * 1.15",
        }
    else:
        report = _profile_rows(rows, label="p16-default", cfg=cfg)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.compare_p16:
        print(
            f"P95 {cur_p95:.3f}s vs p16 {p16_p95:.3f}s "
            f"(+{report['p95IncreasePct']:.1f}%, gate <=15%: {report['p95WithinGate']}) "
            f"-> {args.out}"
        )
    else:
        print(
            f"Report: {report['p50Seconds']}s p50 · {report['p95Seconds']}s p95 -> {args.out}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
