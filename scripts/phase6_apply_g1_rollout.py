"""Phase 6 G1 10% rollout config CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply Phase 6 G1 10% rollout config patch")
    parser.add_argument("--config", type=Path, default=None, help="config.yaml path")
    parser.add_argument("--traffic-percent", type=float, default=10.0)
    parser.add_argument("--cohort-salt", default="p6-g1-2026-05")
    parser.add_argument("--allowlist-trip-id", action="append", default=[], dest="allowlist")
    parser.add_argument("--dry-run", action="store_true", help="print patch only")
    parser.add_argument("--write", action="store_true", help="merge patch into config.yaml")
    args = parser.parse_args()

    if not args.dry_run and not args.write:
        parser.error("pass --dry-run or --write")

    sys.path.insert(0, str(ROOT))
    from travelogue.curation.phase6_rollout import apply_g1_rollout_config, g1_rollout_patch

    patch = g1_rollout_patch(
        traffic_percent=args.traffic_percent,
        cohort_salt=args.cohort_salt,
        allowlist_trip_ids=args.allowlist or None,
    )
    if args.dry_run:
        print(json.dumps(patch, indent=2, ensure_ascii=False))
        return 0

    path = apply_g1_rollout_config(
        args.config,
        traffic_percent=args.traffic_percent,
        cohort_salt=args.cohort_salt,
        allowlist_trip_ids=args.allowlist or None,
    )
    print(json.dumps({"applied": str(path), "patch": patch}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
