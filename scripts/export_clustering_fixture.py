#!/usr/bin/env python3
"""Export clustering golden fixture from a local trip.json (M12-0).

Usage:
  python scripts/export_clustering_fixture.py trips/linzhi --trip-id golden-kyoto-gps
  python scripts/export_clustering_fixture.py trips/mao --trip-id golden-no-gps --strip-geo

Writes tests/fixtures/clustering/{trip-id}/assets-manifest.json
Manual step: edit segments-golden.json event boundaries after export.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES_ROOT = ROOT / "tests" / "fixtures" / "clustering"


def _export_assets(trip: dict, *, strip_geo: bool) -> list[dict]:
    rows: list[dict] = []
    for asset in trip.get("assets") or []:
        if asset.get("type", "image") == "video":
            continue
        row: dict = {
            "id": asset["id"],
            "type": "image",
            "takenAt": asset.get("takenAt"),
        }
        if not strip_geo and asset.get("geo"):
            row["geo"] = asset["geo"]
        if asset.get("place"):
            row["place"] = asset["place"]
        if asset.get("width"):
            row["width"] = asset["width"]
        if asset.get("height"):
            row["height"] = asset["height"]
        if asset.get("sharpness") is not None:
            row["sharpness"] = asset["sharpness"]
        if asset.get("meanLuma") is not None:
            row["meanLuma"] = asset["meanLuma"]
        if asset.get("dominantTone"):
            row["dominantTone"] = asset["dominantTone"]
        rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Export clustering fixture manifest from trip.json")
    parser.add_argument("trip_dir", type=Path, help="Path to trip folder containing trip.json")
    parser.add_argument("--trip-id", required=True, help="Fixture id under tests/fixtures/clustering/")
    parser.add_argument("--strip-geo", action="store_true", help="Omit geo (no-GPS golden)")
    parser.add_argument("--title", default="", help="Optional description in manifest")
    args = parser.parse_args()

    trip_json = args.trip_dir / "trip.json"
    if not trip_json.is_file():
        raise SystemExit(f"trip.json not found: {trip_json}")

    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    assets = _export_assets(trip, strip_geo=args.strip_geo)
    out_dir = FIXTURES_ROOT / args.trip_id
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "description": args.title or f"Exported from {trip_json}",
        "sourceTrip": str(args.trip_dir),
        "assetCount": len(assets),
        "assets": assets,
    }
    (out_dir / "assets-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    golden_stub = [
        {
            "id": "evt-01",
            "name": "待标注",
            "startDate": "YYYY-MM-DD",
            "endDate": "YYYY-MM-DD",
            "assetIds": [],
            "note": "人工填写 event 边界 · 删除本 note 字段",
        }
    ]
    golden_path = out_dir / "segments-golden.json"
    if not golden_path.is_file():
        golden_path.write_text(
            json.dumps(golden_stub, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    readme = out_dir / "README.md"
    if not readme.is_file():
        readme.write_text(
            f"# {args.trip_id}\n\n"
            f"- 来源：`{args.trip_dir}`\n"
            f"- 编辑 `segments-golden.json` 完成人工 event 标注\n"
            f"- 运行：`pytest tests/test_clustering_spike.py -k {args.trip_id}`\n",
            encoding="utf-8",
        )

    print(f"Wrote {len(assets)} assets -> {out_dir}")


if __name__ == "__main__":
    main()
