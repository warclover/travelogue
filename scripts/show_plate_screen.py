#!/usr/bin/env python3
"""Print patternId + slots for folio Plate · NN (global screen index)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from travelogue.config import get_config


def main() -> int:
    parser = argparse.ArgumentParser(description="Show layout screen for Plate · NN")
    parser.add_argument("trip_id", help="Trip id (folder name under trips/)")
    parser.add_argument(
        "plate",
        type=int,
        nargs="?",
        default=2,
        help="Plate number (global screen index, default 2)",
    )
    args = parser.parse_args()
    trip_path = get_config().trips_dir / args.trip_id / "trip.json"
    if not trip_path.is_file():
        print(f"Not found: {trip_path}", file=sys.stderr)
        return 1
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    target = args.plate
    idx = 0
    hit: dict | None = None
    hit_ch: int | None = None
    for ch in trip.get("chapters") or []:
        ch_idx = ch.get("index")
        for sc in ch.get("screens") or []:
            idx += 1
            if idx == target:
                hit = sc
                hit_ch = ch_idx
                break
        if hit:
            break
    if not hit:
        print(f"No screen at Plate · {target:02d} (only {idx} screens)", file=sys.stderr)
        return 1
    print(f"Plate · {target:02d}  chapter={hit_ch}  patternId={hit.get('patternId')}")
    for sl in hit.get("slots") or []:
        aid = sl.get("assetId", "")
        asset = next((a for a in trip.get("assets") or [] if a.get("id") == aid), {})
        w, h = asset.get("width"), asset.get("height")
        ak = asset.get("aspectKind") or "?"
        print(
            f"  slot {sl.get('slot')} role={sl.get('role')} fit={sl.get('fit')} "
            f"assetId={aid} aspectKind={ak} size={w}x{h}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
