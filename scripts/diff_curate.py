"""NR-P3-01 optional CLI · compare Phase 2 baseline vs clustering-enabled curate.

Usage:
  python scripts/diff_curate.py --fixture golden-mixed-scenes
  python scripts/diff_curate.py trips/mao/trip.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.phase3_ig2_report import evaluate_trip, load_fixture_trip


def _chapter_sets(trip: dict) -> list[frozenset[str]]:
    return [frozenset(ch.get("assetIds") or []) for ch in trip.get("chapters") or []]


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare baseline vs P3-Full layout metrics")
    parser.add_argument("target", help="fixture id or path to trip.json")
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--work-dir", type=Path, default=ROOT / ".cache" / "diff-curate")
    args = parser.parse_args()

    if args.fixture:
        trip = load_fixture_trip(args.target)
        trip_id = args.target
    else:
        path = Path(args.target)
        trip = json.loads(path.read_text(encoding="utf-8"))
        trip_id = trip.get("tripId") or path.parent.name

    report = evaluate_trip(trip, trip_id=trip_id, work_dir=args.work_dir / trip_id)
    baseline = report["baseline"]
    full = report["p3Full"]
    out = {
        "tripId": trip_id,
        "baselineChapters": baseline["chapterCount"],
        "p3FullChapters": full["chapterCount"],
        "passesIG1": report["passesIG1"],
        "passesIG2": report["passesIG2"],
        "passesC09": report["passesC09"],
        "metrics": {
            "baseline": baseline,
            "p3Full": full,
        },
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    ok = out["passesIG1"] and out["passesIG2"] and out["passesC09"]
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
