"""Backfill asset.curation.cohort from trip.intent.featuredSubjects (no re-ingest)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.config import get_config
from travelogue.curation.cohort_faces import apply_cohort_tags


def backfill_trip(trip_path: Path, *, cfg_path: Path | None = None) -> dict:
    cfg = get_config(cfg_path)
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    summary = apply_cohort_tags(trip, trip_dir=trip_path.parent, cfg=cfg)
    trip_path.write_text(json.dumps(trip, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary or {"skipped": True}


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill cohort tags on trip assets")
    parser.add_argument("trip_ids", nargs="+")
    parser.add_argument("--trips-dir", type=Path, default=ROOT / "trips")
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args()
    for tid in args.trip_ids:
        path = args.trips_dir / tid / "trip.json"
        if not path.is_file():
            print(f"SKIP {tid}")
            continue
        r = backfill_trip(path, cfg_path=args.config)
        print(f"{tid}: {json.dumps(r, ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
