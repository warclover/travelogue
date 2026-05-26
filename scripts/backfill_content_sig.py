"""Backfill contentSig on existing trip assets for cross-ingest MD5 dedupe.

Usage:
  python scripts/backfill_content_sig.py linzhi mao
  python scripts/backfill_content_sig.py --trips-dir ./trips kyoto-2025
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.media.ingest import content_signature


def _resolve_source(trip_dir: Path, asset: dict) -> Path | None:
    for key in ("sourceFile", "displayFile"):
        rel = asset.get(key)
        if not rel:
            continue
        path = trip_dir / str(rel).replace("\\", "/")
        if path.is_file():
            return path
    return None


def backfill_trip(trip_path: Path, *, overwrite: bool = False) -> dict:
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    trip_dir = trip_path.parent
    updated = 0
    skipped = 0
    missing = 0
    for asset in trip.get("assets") or []:
        if asset.get("type") != "image":
            continue
        if asset.get("contentSig") and not overwrite:
            skipped += 1
            continue
        src = _resolve_source(trip_dir, asset)
        if not src:
            missing += 1
            continue
        asset["contentSig"] = content_signature(src)
        updated += 1
    if updated:
        trip_path.write_text(
            json.dumps(trip, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    total = sum(1 for a in trip.get("assets") or [] if a.get("type") == "image")
    with_sig = sum(1 for a in trip.get("assets") or [] if a.get("contentSig"))
    return {
        "tripId": trip.get("tripId"),
        "updated": updated,
        "skipped": skipped,
        "missingSource": missing,
        "withContentSig": with_sig,
        "totalImages": total,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill contentSig on trip assets")
    parser.add_argument("trip_ids", nargs="+")
    parser.add_argument("--trips-dir", type=Path, default=ROOT / "trips")
    parser.add_argument("--overwrite", action="store_true", help="Recompute even when contentSig exists")
    args = parser.parse_args()
    for tid in args.trip_ids:
        path = args.trips_dir / tid / "trip.json"
        if not path.is_file():
            print(f"SKIP {tid} (no trip.json)")
            continue
        r = backfill_trip(path, overwrite=args.overwrite)
        print(
            f"{tid}: updated={r['updated']} skipped={r['skipped']} "
            f"missing={r['missingSource']} withSig={r['withContentSig']}/{r['totalImages']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
