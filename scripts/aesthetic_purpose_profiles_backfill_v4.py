"""Persist v4 purpose pilot profiles into trip.curation.purposePilotProfile."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.config.aesthetic_purpose_profiles import load_purpose_profiles, profile_summary  # noqa: E402

META_KEYS = frozenset({"kind", "role", "humanWinratePctV4p2", "lockedFrom"})


def _strip_meta(raw: dict) -> dict:
    return {k: v for k, v in raw.items() if k not in META_KEYS and v is not None}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backfill purposePilotProfile on v4 trips")
    parser.add_argument(
        "--profiles",
        type=Path,
        default=Path("docs/acceptance-records/aesthetic-purpose-profiles.v4.json"),
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    doc = load_purpose_profiles(args.profiles)
    trips = doc.get("trips") or {}
    for trip_id, raw in trips.items():
        if not isinstance(raw, dict):
            continue
        profile = _strip_meta(raw)
        trip_dir = ROOT / "trips" / trip_id
        trip_path = trip_dir / "trip.json"
        if not trip_path.is_file():
            print("skip missing", trip_path)
            continue
        trip = json.loads(trip_path.read_text(encoding="utf-8"))
        trip.setdefault("curation", {})["purposePilotProfile"] = profile
        if args.dry_run:
            print(trip_id, profile_summary(profile))
            continue
        trip_path.write_text(json.dumps(trip, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("updated", trip_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
