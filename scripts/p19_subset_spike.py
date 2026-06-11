#!/usr/bin/env python3
"""P19 S5-04 · subset planner spike on a single trip (default demo-1506104ebf).

Usage:
  python scripts/p19_subset_spike.py
  python scripts/p19_subset_spike.py demo-1506104ebf --apply
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from travelogue.config import get_config
from travelogue.curation.clustering import run_clustering_layer
from travelogue.curation.subset_planner import (
    SubsetConfig,
    apply_subset_plan,
    plan_asset_subset,
)
from travelogue.eval.golden_trips import resolve_existing_golden_trips

from book_quality_baseline import _prepare_trip


def main() -> int:
    parser = argparse.ArgumentParser(description="P19 subset planner spike")
    parser.add_argument(
        "trip_id",
        nargs="?",
        default="demo-1506104ebf",
        help="Trip id (default: demo-1506104ebf)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write subsetPlan and mark dropped assets layout-ineligible",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / ".cache" / "book-quality" / "subset-spike.json",
    )
    args = parser.parse_args()

    rows = [r for r in resolve_existing_golden_trips(root=ROOT) if r["tripId"] == args.trip_id]
    if not rows:
        print(f"Trip not found: {args.trip_id}", file=sys.stderr)
        return 1

    row = rows[0]
    trip_path = Path(row["tripDir"]) / "trip.json"
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    body = _prepare_trip(trip)
    work = ROOT / ".cache" / "book-quality" / "subset-spike-work" / args.trip_id
    cfg = get_config(reload=True)
    run_clustering_layer(body, trip_dir=work / "cluster", cfg=cfg)

    plan_cfg = SubsetConfig(enabled=True)
    plan = plan_asset_subset(body, cfg=plan_cfg)
    dropped = 0
    if args.apply:
        dropped = apply_subset_plan(body, plan)

    report = {
        "tripId": args.trip_id,
        "tier": plan.tier,
        "baselinePoolCount": plan.baseline_pool_count,
        "targetKeepPool": plan.target_keep_pool,
        "targetReduction": plan.target_reduction,
        "actualReduction": plan.to_dict()["actualReduction"],
        "keptCount": len(plan.kept_asset_ids),
        "droppedCount": len(plan.dropped_asset_ids),
        "medoidCount": len(plan.medoid_asset_ids),
        "coverageCount": len(plan.coverage_asset_ids),
        "applied": args.apply,
        "layoutEligibleMarked": dropped,
        "subsetPlan": plan.to_dict(),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        f"{args.trip_id}: tier={plan.tier} "
        f"pool={plan.baseline_pool_count} "
        f"target-{plan.target_reduction:.0%} "
        f"actual-{report['actualReduction']:.0%} "
        f"kept={report['keptCount']} dropped={report['droppedCount']}"
    )
    print(f"Report -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
