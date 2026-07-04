#!/usr/bin/env python3
"""URO P0-c · usage_rules off/on eval report (AC-URO-04 diagnostic · AC-URO-BLIND prep).

Usage:
  python scripts/usage_rules_eval_report.py --fixture golden-mixed-scenes
  python scripts/usage_rules_eval_report.py linzhi demo-2019
  python scripts/usage_rules_eval_report.py --golden
  python scripts/usage_rules_eval_report.py --golden --strict
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.usage_rules_eval_common import (
    AC_URO_BLIND_THRESHOLD,
    aggregate_eval_rows,
    evaluate_trip_off_on,
    load_trip,
)
from travelogue.curation.usage_rules.metrics import (
    URO_FIXTURE_TRIP_IDS,
    URO_GOLDEN_TRIP_IDS,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="URO usage_rules off/on eval report (P0-c)")
    parser.add_argument("trip_ids", nargs="*", help="Trip ids or fixture ids")
    parser.add_argument("--trips-dir", type=Path, default=ROOT / "trips")
    parser.add_argument("--fixture", action="store_true", help="Load tests/fixtures/clustering/{id}")
    parser.add_argument(
        "--golden",
        action="store_true",
        help="Run BQP golden set (skip missing trips, fallback fixtures)",
    )
    parser.add_argument("--work-dir", type=Path, default=ROOT / ".cache" / "usage-rules-eval")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "docs" / "acceptance-records" / "usage-rules-eval-report.json",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 if any trip has layoutSnapshotEqual=false (off baseline drift)",
    )
    args = parser.parse_args()

    trip_ids = list(args.trip_ids)
    if args.golden and not trip_ids:
        trip_ids = list(URO_GOLDEN_TRIP_IDS) + list(URO_FIXTURE_TRIP_IDS)

    if not trip_ids:
        parser.error("Provide trip_ids or --golden")

    rows: list[dict] = []
    for tid in trip_ids:
        trip = load_trip(tid, trips_dir=args.trips_dir, use_fixture=args.fixture)
        if trip is None:
            print(f"SKIP {tid} (not found)", flush=True)
            continue
        print(f"URO eval {tid} ...", flush=True)
        row = evaluate_trip_off_on(tid, trip, work_dir=args.work_dir / tid)
        rows.append(row)
        print(
            f"  snapshot_equal={row['layoutSnapshotEqual']}  "
            f"hero_mismatch {row['off'].get('heroMismatchRate')} → {row['on'].get('heroMismatchRate')}  "
            f"ur_rejects={row['on'].get('usageRuleRejectCount')}",
            flush=True,
        )

    if not rows:
        print("No trips evaluated.", file=sys.stderr)
        return 1

    payload = {
        "recordId": "usage-rules-eval-report",
        "feature": "URO",
        "gate": "AC-URO-BLIND-prep",
        "blindThreshold": AC_URO_BLIND_THRESHOLD,
        "aggregate": aggregate_eval_rows(rows),
        "trips": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {args.out}")

    if args.strict and any(not r.get("layoutSnapshotEqual") for r in rows):
        print("STRICT FAIL: layoutSnapshotEqual=false for some trips", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
