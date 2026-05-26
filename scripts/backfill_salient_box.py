"""Backfill salientBox on existing trip assets (Phase 3b+).

Uses OpenCV Haar face detection when available; writes normalized box + focalPoint.

Usage:
  python scripts/backfill_salient_box.py mao linzhi
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.media.subject_detect import analyze_subject, _opencv_available


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
    opencv = _opencv_available()
    updated = 0
    skipped = 0
    faces = 0
    for asset in trip.get("assets") or []:
        if asset.get("type") != "image":
            continue
        if asset.get("salientBox") and not overwrite:
            skipped += 1
            continue
        img_path = _resolve_source(trip_dir, asset)
        if not img_path:
            skipped += 1
            continue
        with Image.open(img_path) as img:
            img = ImageOps.exif_transpose(img)
            subj = analyze_subject(img, enabled=True)
        if subj.salient_box:
            asset["salientBox"] = subj.salient_box
            asset["focalPoint"] = {"x": subj.focal[0], "y": subj.focal[1]}
            faces += 1
        elif overwrite and "salientBox" in asset:
            asset.pop("salientBox", None)
        updated += 1
    trip_path.write_text(json.dumps(trip, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    total = sum(1 for a in trip.get("assets") or [] if a.get("type") == "image")
    with_box = sum(1 for a in trip.get("assets") or [] if a.get("salientBox"))
    return {
        "tripId": trip.get("tripId"),
        "opencv": opencv,
        "processed": updated,
        "skipped": skipped,
        "facesDetected": faces,
        "withSalientBox": with_box,
        "totalImages": total,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill salientBox on trip assets")
    parser.add_argument("trip_ids", nargs="+")
    parser.add_argument("--trips-dir", type=Path, default=ROOT / "trips")
    parser.add_argument("--overwrite", action="store_true", help="Re-detect even when salientBox exists")
    args = parser.parse_args()
    if not _opencv_available():
        print("WARN: OpenCV not installed — salientBox backfill will no-op")
    for tid in args.trip_ids:
        path = args.trips_dir / tid / "trip.json"
        if not path.is_file():
            print(f"SKIP {tid}")
            continue
        r = backfill_trip(path, overwrite=args.overwrite)
        print(
            f"{tid}: processed={r['processed']} faces={r['facesDetected']} "
            f"withBox={r['withSalientBox']}/{r['totalImages']} opencv={r['opencv']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
