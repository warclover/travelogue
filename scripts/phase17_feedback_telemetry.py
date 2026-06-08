"""AC-P17-21 · aggregate layout-feedback.jsonl across trip runs.

Usage:
  python scripts/phase17_feedback_telemetry.py --trips-dir trips
  python scripts/phase17_feedback_telemetry.py --trip-dir trips/demo-2025
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.layout_engine.feedback import read_layout_feedback_events, SIDECAR_NAME


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def aggregate_trip_events(trip_dir: Path) -> dict:
    events = read_layout_feedback_events(trip_dir)
    pairwise = [e for e in events if e.get("pairwiseEligible")]
    by_type: dict[str, int] = {}
    for ev in events:
        et = str(ev.get("editType") or "unknown")
        by_type[et] = by_type.get(et, 0) + 1
    return {
        "tripId": trip_dir.name,
        "sidecar": str((trip_dir / "runs" / SIDECAR_NAME).relative_to(ROOT)),
        "eventCount": len(events),
        "pairwiseEligibleCount": len(pairwise),
        "eventsByType": by_type,
    }


def collect_trip_dirs(root: Path) -> list[Path]:
    if (root / "runs").is_dir() or (root / "trip.json").is_file():
        return [root]
    return sorted(p.parent for p in root.glob("*/trip.json"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate layout-feedback telemetry")
    parser.add_argument("--trips-dir", type=Path, help="Parent of trip folders")
    parser.add_argument("--trip-dir", type=Path, action="append", help="Single trip folder")
    parser.add_argument("--out", type=Path, help="Write JSON report")
    args = parser.parse_args()

    dirs: list[Path] = list(args.trip_dir or [])
    if args.trips_dir:
        dirs.extend(collect_trip_dirs(args.trips_dir))
    dirs = sorted({d.resolve() for d in dirs})

    trips = [aggregate_trip_events(d) for d in dirs if d.is_dir()]
    total_events = sum(t["eventCount"] for t in trips)
    payload = {
        "emittedAt": _now(),
        "tripCount": len(trips),
        "totalEvents": total_events,
        "trips": trips,
        "observable": total_events >= 0,
        "notes": "AC-P17-21 requires export path observable; pairwise labels optional.",
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
