#!/usr/bin/env python3
"""LRG · repair common trip.json schema drift blocking render (demo dogfood).

Fixes:
  - Missing ``screenId`` on chapter screens (schema required field).
  - Optional write-back with ``--in-place`` (default: print summary only).

Usage:
  python scripts/lrg_repair_trip_json.py trips/demo-815dc906d3/trip.json
  python scripts/lrg_repair_trip_json.py trips/demo-815dc906d3/trip.json --in-place
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def backfill_missing_screen_ids(trip: dict) -> list[str]:
    """Assign placeholder screenId values where absent; returns ids written."""
    fixed: list[str] = []
    for ch_idx, ch in enumerate(trip.get("chapters") or []):
        if not isinstance(ch, dict):
            continue
        ch_id = str(ch.get("id") or ch.get("chapterId") or f"ch-{ch_idx + 1:02d}")
        for sc_idx, screen in enumerate(ch.get("screens") or []):
            if not isinstance(screen, dict):
                continue
            if screen.get("screenId"):
                continue
            new_id = f"{ch_id}-sc-gap-{sc_idx:02d}"
            screen["screenId"] = new_id
            fixed.append(new_id)
    return fixed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="LRG trip.json schema repair helper")
    ap.add_argument("trip_json", type=Path, help="path to trip.json")
    ap.add_argument(
        "--in-place",
        action="store_true",
        help="write repaired trip.json back to disk (default: dry-run summary only)",
    )
    args = ap.parse_args(argv)

    path = args.trip_json.resolve()
    if not path.is_file():
        print(f"[error] not found: {path}", file=sys.stderr)
        return 1

    trip = json.loads(path.read_text(encoding="utf-8"))
    fixed = backfill_missing_screen_ids(trip)
    if not fixed:
        print(f"OK {path.name} · no missing screenId entries")
    else:
        print(f"found {len(fixed)} missing screenId entries:")
        for sid in fixed:
            print(f"  - {sid}")

    if args.in_place and fixed:
        path.write_text(json.dumps(trip, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path}")

    if fixed and not args.in_place:
        print("dry-run only — re-run with --in-place to apply")

    from travelogue.services.validate import validate_trip

    errs = [e for e in validate_trip(trip) if not e.startswith("WARN:")]
    if errs:
        print(f"validate still reports {len(errs)} error(s) after repair:", file=sys.stderr)
        for err in errs[:8]:
            print(f"  {err}", file=sys.stderr)
        if len(errs) > 8:
            print(f"  … and {len(errs) - 8} more", file=sys.stderr)
        return 1 if not fixed else 0

    print("validate: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
