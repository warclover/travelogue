"""Apply LSE dogfood rollout patch to lse_runtime.json (W3a-04 ops helper)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from travelogue.layout_engine.runtime_store import merge_approved_patch
from travelogue.paths import ROOT


def dogfood_rollout_patch(
    *,
    traffic_percent: float = 0.0,
    allowlist: list[str] | None = None,
) -> dict:
    return {
        "layout_strategy_rollout": {
            "stage": "dogfood",
            "traffic_percent": traffic_percent,
            "cohort_salt": "travelogue-p17-w3a",
            "allowlist_trip_ids": list(allowlist or []),
            "blocklist_trip_ids": [],
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge LSE dogfood rollout into lse_runtime.json")
    parser.add_argument(
        "--store",
        type=Path,
        default=ROOT / "data" / "lse_runtime.json",
        help="lse_runtime.json path",
    )
    parser.add_argument(
        "--traffic-percent",
        type=float,
        default=0.0,
        help="Bucket percent (0 = allowlist only)",
    )
    parser.add_argument(
        "--allowlist",
        nargs="*",
        default=[],
        help="tripId allowlist (default: phase16 dogfood ids)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print patch only")
    parser.add_argument("--change-id", default="lse-dogfood-w3a", help="configHistory change id")
    args = parser.parse_args()

    allow = args.allowlist or [
        "phase16-dogfood-portrait",
        "phase16-dogfood-landscape",
        "phase16-dogfood-mixed",
    ]
    patch = dogfood_rollout_patch(traffic_percent=args.traffic_percent, allowlist=allow)
    if args.dry_run:
        print(json.dumps(patch, ensure_ascii=False, indent=2))
        return 0

    merge_approved_patch(patch, store_path=args.store, change_id=args.change_id)
    print(f"Applied dogfood rollout to {args.store.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
