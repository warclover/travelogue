"""Recompute quality.sharpness (v2) for assets in a trip directory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def migrate_trip(trip_dir: Path, *, dry_run: bool = False) -> dict:
    from PIL import Image

    from travelogue.media.sharpness import sharpness_score, sharpness_score_v2

    trip_path = trip_dir / "trip.json"
    if not trip_path.is_file():
        raise FileNotFoundError(trip_path)
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    updated = 0
    for asset in trip.get("assets") or []:
        if asset.get("type") == "video":
            continue
        rel = asset.get("sourceFile") or asset.get("path") or ""
        src = trip_dir / str(rel).lstrip("/\\")
        if not src.is_file():
            continue
        roi = asset.get("salientBox") if isinstance(asset.get("salientBox"), dict) else None
        with Image.open(src) as im:
            v1 = sharpness_score(im)
            v2 = sharpness_score_v2(im, roi=roi)
        q = asset.setdefault("quality", {})
        if not isinstance(q, dict):
            continue
        if not dry_run:
            q["sharpnessLegacy"] = q.get("sharpness", v1)
            q["sharpness"] = round(v2, 2)
            q["sharpnessVersion"] = "v2"
        updated += 1
    if not dry_run:
        trip_path.write_text(json.dumps(trip, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"trip": str(trip_dir), "updated": updated, "dryRun": dry_run}


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate trip sharpness to v2")
    parser.add_argument("trip_dir", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        stats = migrate_trip(args.trip_dir.resolve(), dry_run=args.dry_run)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
