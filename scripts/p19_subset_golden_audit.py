#!/usr/bin/env python3
"""P19 S6 · subset reduction audit on all golden trips (planner only, no apply).

Usage:
  python scripts/p19_subset_golden_audit.py
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from travelogue.config import get_config
from travelogue.curation.clustering import run_clustering_layer
from travelogue.curation.subset_planner import SubsetConfig, plan_asset_subset
from travelogue.eval.golden_trips import resolve_existing_golden_trips

from book_quality_baseline import _prepare_trip


def main() -> int:
    parser = argparse.ArgumentParser(description="P19 subset golden audit")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / ".cache" / "book-quality" / "subset-golden-audit.json",
    )
    args = parser.parse_args()

    cfg = get_config(reload=True)
    plan_cfg = SubsetConfig(enabled=True)
    rows = [r for r in resolve_existing_golden_trips(root=ROOT) if r["exists"]]
    per_trip: list[dict] = []

    for row in rows:
        tid = row["tripId"]
        trip = json.loads(Path(row["tripDir"]).joinpath("trip.json").read_text(encoding="utf-8"))
        body = _prepare_trip(trip)
        work = ROOT / ".cache" / "book-quality" / "subset-audit-work" / tid
        run_clustering_layer(body, trip_dir=work / "cluster", cfg=cfg)
        plan = plan_asset_subset(body, cfg=plan_cfg)
        actual = plan.to_dict()["actualReduction"]
        per_trip.append(
            {
                "tripId": tid,
                "tier": plan.tier,
                "baselinePoolCount": plan.baseline_pool_count,
                "actualReduction": actual,
                "targetReduction": plan.target_reduction,
            }
        )
        print(f"{tid}: tier={plan.tier} pool={plan.baseline_pool_count} actual-{actual:.1%}")

    reductions = [t["actualReduction"] for t in per_trip if t["baselinePoolCount"] > 0]
    median = statistics.median(reductions) if reductions else 0.0
    report = {
        "trips": per_trip,
        "medianActualReduction": round(median, 4),
        "withinGate": 0.25 <= median <= 0.40,
        "count": len(per_trip),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Median reduction {median:.1%} (gate 25-40%: {report['withinGate']}) -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
