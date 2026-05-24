#!/usr/bin/env python3
"""Cross-platform A/B: legacy vs screens Web layout (see scripts/compare-web-layout.ps1)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from travelogue.render.compare_web import compare_web_layout


def main() -> int:
    parser = argparse.ArgumentParser(description="Render index-legacy.html + index-screens.html")
    parser.add_argument("trip", type=Path, help="trip.json or trip directory")
    parser.add_argument("--out", type=Path, default=None, help="output directory (default: trip dir)")
    args = parser.parse_args()

    trip_path = args.trip
    if trip_path.is_dir():
        trip_path = trip_path / "trip.json"
    if not trip_path.is_file():
        print(f"E_TRIP_NOT_FOUND {trip_path}", file=sys.stderr)
        return 1

    result = compare_web_layout(trip_path, out_dir=args.out)
    print(f"OK legacy  {result.legacy_html}")
    print(f"OK screens {result.screens_html}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
