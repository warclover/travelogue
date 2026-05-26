"""Backfill meanLuma + dominantTone on existing trip assets (Phase 3b)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.media.color_metrics import dominant_tone_hex, mean_luma


def backfill_trip(trip_path: Path) -> dict:
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    trip_dir = trip_path.parent
    updated = 0
    skipped = 0
    for asset in trip.get("assets") or []:
        if asset.get("type") != "image":
            continue
        src = asset.get("sourceFile") or asset.get("displayFile")
        if not src:
            skipped += 1
            continue
        img_path = trip_dir / src.replace("/", "\\").replace("\\", "/")
        if not img_path.is_file():
            alt = trip_dir / (asset.get("displayFile") or "")
            img_path = alt if alt.is_file() else img_path
        if not img_path.is_file():
            skipped += 1
            continue
        with Image.open(img_path) as img:
            img = ImageOps.exif_transpose(img)
            q = dict(asset.get("quality") or {})
            q["meanLuma"] = round(mean_luma(img), 4)
            asset["quality"] = q
            asset["dominantTone"] = dominant_tone_hex(img)
        updated += 1
    trip_path.write_text(json.dumps(trip, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"tripId": trip.get("tripId"), "updated": updated, "skipped": skipped}


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill color metrics on trip assets")
    parser.add_argument("trip_ids", nargs="+")
    parser.add_argument("--trips-dir", type=Path, default=ROOT / "trips")
    args = parser.parse_args()
    for tid in args.trip_ids:
        path = args.trips_dir / tid / "trip.json"
        if not path.is_file():
            print(f"SKIP {tid}")
            continue
        r = backfill_trip(path)
        print(f"{tid}: updated={r['updated']} skipped={r['skipped']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
