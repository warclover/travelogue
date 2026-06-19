"""Backfill trip.curation.purposeProfileKind from v4 profile registry (DS-3)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.config.aesthetic_purpose_profiles import (  # noqa: E402
    infer_purpose_profile_kind,
    load_purpose_profiles,
    profile_summary,
    purpose_profile_for_trip,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backfill purposeProfileKind on trips")
    parser.add_argument(
        "--profiles",
        type=Path,
        default=Path("docs/acceptance-records/aesthetic-purpose-profiles.v4.json"),
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    doc = load_purpose_profiles(args.profiles)
    trip_map = dict(doc.get("tripKindMap") or {})
    trip_map.update(
        {
            tid: str(raw.get("kind"))
            for tid, raw in (doc.get("trips") or {}).items()
            if isinstance(raw, dict) and raw.get("kind")
        }
    )

    for trip_id, kind in sorted(trip_map.items()):
        trip_dir = ROOT / "trips" / trip_id
        trip_path = trip_dir / "trip.json"
        if not trip_path.is_file():
            print("skip missing", trip_path)
            continue
        trip = json.loads(trip_path.read_text(encoding="utf-8"))
        curation = trip.setdefault("curation", {})
        curation["purposeProfileKind"] = kind
        resolved = purpose_profile_for_trip(trip, profiles_doc=doc)
        if resolved:
            curation["purposePilotProfile"] = profile_summary(resolved)
        inferred = infer_purpose_profile_kind(trip)
        if args.dry_run:
            print(trip_id, "kind=", kind, "inferred=", inferred, profile_summary(resolved or {}))
            continue
        trip_path.write_text(json.dumps(trip, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("updated", trip_path, kind)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
