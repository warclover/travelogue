"""Audit photo-cull gap for a trip (206 vs 165 style breakdown)."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    trip_id = sys.argv[1] if len(sys.argv) > 1 else "demo-1506104ebf"
    trip_path = ROOT / "trips" / trip_id / "trip.json"
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    assets = trip.get("assets") or []
    images = [a for a in assets if str(a.get("type") or "image") == "image"]
    pool = [a for a in images if not a.get("excludeReason")]
    excluded = [a for a in images if a.get("excludeReason")]

    cs = (trip.get("curation") or {}).get("cullSummary") or {}
    by_reason = Counter(a.get("excludeReason") for a in excluded)

    print(f"trip: {trip_id}")
    print(f"title: {(trip.get('meta') or {}).get('title')}")
    print(f"total image assets: {len(images)}")
    print(f"layout pool (no excludeReason): {len(pool)}")
    print(f"excluded: {len(excluded)}")
    print()
    if cs:
        print("cullSummary:")
        for k in (
            "scanned",
            "featuredCount",
            "layoutEligibleCount",
            "keepRatioFloor",
            "floorTargetNonFeatured",
            "scoreKeepApplied",
            "excludedByCull",
            "excludedByReason",
            "pass3Skipped",
            "cullMode",
        ):
            if k in cs:
                print(f"  {k}: {cs[k]}")
        print()
    print("excludeReason counts:")
    for reason, n in sorted(by_reason.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {reason}: {n}")

    quota = [a for a in excluded if a.get("excludeReason") == "cull_quota"]
    if quota:
        quota.sort(key=lambda a: (a.get("quality") or {}).get("cullRank", 9999))
        lo = (quota[0].get("quality") or {}).get("cullRank")
        hi = (quota[-1].get("quality") or {}).get("cullRank")
        print(f"\ncull_quota rank range: {lo} .. {hi} (n={len(quota)})")
        keep_n = (cs.get("scoreKeepApplied") or cs.get("floorTargetNonFeatured"))
        if keep_n:
            print(f"keep_top (pass3): {keep_n}")

    for reason in ("media_class", "blur", "duplicate_group"):
        subset = [a for a in excluded if a.get("excludeReason") == reason]
        if not subset:
            continue
        print(f"\n{reason} samples:")
        for a in subset[:5]:
            q = a.get("quality") or {}
            print(
                f"  {a['id']} mediaClass={a.get('mediaClass')} "
                f"sharp={(q.get('sharpness') or q.get('cullSharpness'))} "
                f"explain={q.get('cullExplain')}"
            )
        if len(subset) > 5:
            print(f"  ... +{len(subset) - 5} more")

    floor = cs.get("keepRatioFloor", 0.9)
    scanned = cs.get("scanned", len(images))
    import math

    computed_floor = math.ceil(float(floor) * int(scanned))
    print(f"\nfloor math: ceil({floor} * {scanned}) = {computed_floor}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
