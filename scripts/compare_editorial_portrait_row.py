#!/usr/bin/env python3
"""Dogfood A/B: legacy person-triple vs editorial portrait row (PRD PR-5)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from travelogue.render.compare_editorial_portrait_row import compare_editorial_portrait_row


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render index-editorial-compare.html with legacy vs editorial panels"
    )
    parser.add_argument("trip", type=Path, help="trip.json or trip directory")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="output directory (default: <trip>/editorial-compare)",
    )
    args = parser.parse_args()

    trip_path = args.trip
    if trip_path.is_dir():
        trip_path = trip_path / "trip.json"
    if not trip_path.is_file():
        print(f"E_TRIP_NOT_FOUND {trip_path}", file=sys.stderr)
        return 1

    result = compare_editorial_portrait_row(trip_path, out_dir=args.out)
    print(f"OK wrapper  {result.wrapper_html}")
    print(f"OK legacy   {result.legacy_panel}")
    print(f"OK editorial {result.editorial_panel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
