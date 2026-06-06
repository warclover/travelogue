#!/usr/bin/env python3
"""Validate trip.json — thin wrapper around travelogue.services.validate."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from travelogue.paths import MANIFEST_PATH
from travelogue.services.trip import TripService
from travelogue.services.validate import validate_trip


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate trip.json")
    parser.add_argument("path", type=Path, help="trip.json path")
    parser.add_argument(
        "--level",
        choices=["schema", "manifest", "all"],
        default="all",
    )
    args = parser.parse_args()

    if not args.path.is_file():
        print(f"E_TRIP_NOT_FOUND {args.path}", file=sys.stderr)
        return 1

    trip = TripService().load(args.path)
    print(f"--- {args.path}")
    errors = validate_trip(trip, level=args.level, manifest_path=MANIFEST_PATH)

    warns = [e for e in errors if e.startswith("WARN:")]
    errs = [e for e in errors if not e.startswith("WARN:")]
    for w in warns:
        print(w)
    for e in errs:
        print(e, file=sys.stderr)
    if errs:
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
