"""P5-QS-01 · layout quality sprint metrics recorder.

Usage:
  python scripts/phase5_layout_sprint.py --record trips/demo/trip.json
  python scripts/phase5_layout_sprint.py --summary
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SPRINT_JSON = ROOT / "docs" / "acceptance-records" / "phase5-layout-sprint.json"


def _load_sprint() -> dict:
    if SPRINT_JSON.is_file():
        return json.loads(SPRINT_JSON.read_text(encoding="utf-8"))
    return {"recordId": "phase5-layout-sprint", "albums": [], "runs": []}


def _save_sprint(data: dict) -> None:
    SPRINT_JSON.parent.mkdir(parents=True, exist_ok=True)
    SPRINT_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _trip_metrics(trip: dict) -> dict:
    chapters = trip.get("chapters") or []
    screens = sum(len(ch.get("screens") or []) for ch in chapters)
    assets = len(trip.get("assets") or [])
    cover = (trip.get("curation") or {}).get("coverByLayout") or {}
    return {
        "assetCount": assets,
        "chapterCount": len(chapters),
        "screenCount": screens,
        "coverByLayout": cover,
        "degradationReason": (trip.get("curation") or {}).get("degradationReason"),
    }


def _iter_trip_json(root: Path) -> list[Path]:
    root = root.resolve()
    rows: list[Path] = []
    if (root / "trip.json").is_file():
        return [root / "trip.json"]
    if not root.is_dir():
        return rows
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        trip_json = child / "trip.json"
        if trip_json.is_file():
            rows.append(trip_json)
    return rows


def scan_trips(trips_root: Path, *, notes: str = "auto-scan") -> list[dict]:
    entries: list[dict] = []
    for trip_json in _iter_trip_json(trips_root):
        entries.append(record_trip(trip_json, notes=notes))
    return entries


def record_trip(trip_path: Path, *, winner: str | None = None, notes: str = "") -> dict:
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    metrics = _trip_metrics(trip)
    entry = {
        "date": date.today().isoformat(),
        "tripPath": str(trip_path.relative_to(ROOT)).replace("\\", "/"),
        "tripId": trip.get("tripId") or trip_path.parent.name,
        "metrics": metrics,
        "winner": winner,
        "notes": notes,
    }
    data = _load_sprint()
    data.setdefault("runs", []).append(entry)
    wins = sum(1 for r in data["runs"] if r.get("winner") == "tuned")
    total = sum(1 for r in data["runs"] if r.get("winner") in ("tuned", "legacy", "baseline"))
    data["summary"] = {
        "tunedWins": wins,
        "judged": total,
        "passesTarget": wins >= 8 if total >= 10 else None,
    }
    _save_sprint(data)
    return entry


def print_summary() -> int:
    data = _load_sprint()
    summary = data.get("summary") or {}
    print(json.dumps({"runs": len(data.get("runs", [])), **summary}, indent=2, ensure_ascii=False))
    judged = int(summary.get("judged") or 0)
    wins = int(summary.get("tunedWins") or 0)
    if judged >= 10 and wins >= 8:
        return 0
    return 0 if judged < 10 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Record P5-QS-01 layout sprint metrics")
    parser.add_argument("--record", type=Path, help="path to trip.json after curate")
    parser.add_argument("--winner", choices=("tuned", "legacy", "baseline", "tie"))
    parser.add_argument("--notes", default="")
    parser.add_argument("--scan-trips", type=Path, help="record metrics for each trip.json under directory")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    if args.summary:
        return print_summary()
    if args.scan_trips:
        if not args.scan_trips.is_dir():
            print(f"not a directory: {args.scan_trips}", file=sys.stderr)
            return 2
        entries = scan_trips(args.scan_trips)
        print(json.dumps({"recorded": len(entries), "entries": entries}, indent=2, ensure_ascii=False))
        return 0
    if not args.record:
        parser.error("--record or --summary required")
    if not args.record.is_file():
        print(f"trip not found: {args.record}", file=sys.stderr)
        return 2
    entry = record_trip(args.record, winner=args.winner, notes=args.notes)
    print(json.dumps(entry, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
