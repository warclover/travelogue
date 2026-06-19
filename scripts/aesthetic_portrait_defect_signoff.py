#!/usr/bin/env python3
"""P3-4 · dogfood portrait defect rates on key slots (AC-PC-D1~D3 proxy).

Usage:
  python scripts/aesthetic_portrait_defect_signoff.py \\
    --trip demo-1a737d6205:trips/demo-1a737d6205 \\
    --write docs/acceptance-records/portrait-defect-dogfood.v3.json

  python scripts/aesthetic_portrait_defect_signoff.py \\
    --input docs/acceptance-records/portrait-defect-dogfood.v3.json \\
    --baseline docs/acceptance-records/portrait-defect-dogfood.baseline.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.curation.portrait_defect_metrics import (  # noqa: E402
    aggregate_defect_rates,
    analyze_slot_defects,
    compare_to_baseline,
)

DEFAULT_TRIPS = (
    "demo-fc8b3a5c08:trips/demo-fc8b3a5c08",
    "demo-1a737d6205:trips/demo-1a737d6205",
    "demo-2025-6:trips/demo-2025-6",
)


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def _load_trip(trip_dir: Path) -> dict[str, Any]:
    trip_json = trip_dir / "trip.json"
    if not trip_json.is_file():
        raise FileNotFoundError(f"missing trip.json: {trip_json}")
    return json.loads(trip_json.read_text(encoding="utf-8"))


def _parse_trip_spec(raw: str) -> tuple[str, Path]:
    if ":" in raw:
        trip_id, rel = raw.split(":", 1)
        return trip_id.strip(), _resolve(Path(rel.strip()))
    return raw.strip(), _resolve(Path("trips") / raw.strip())


def build_report(*, trip_specs: list[str]) -> dict[str, Any]:
    trips_out: list[dict[str, Any]] = []
    for spec in trip_specs:
        trip_id, trip_dir = _parse_trip_spec(spec)
        trip = _load_trip(trip_dir)
        trip.setdefault("tripId", trip_id)
        trips_out.append(analyze_slot_defects(trip))
    aggregate = aggregate_defect_rates(trips_out)
    return {
        "version": "1",
        "recordedAt": datetime.now(UTC).isoformat(),
        "notes": "AC-PC-D1~D3 proxy · portrait key-slot defect rate (automated portrait block)",
        "trips": trips_out,
        "aggregate": aggregate,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Portrait defect dogfood signoff (P3-4)")
    parser.add_argument(
        "--trip",
        action="append",
        dest="trips",
        help="tripId:path/to/trip-dir (repeatable; default: 3 dogfood trips)",
    )
    parser.add_argument("--write", type=Path, help="write JSON report")
    parser.add_argument("--input", type=Path, help="existing report JSON (skip trip load)")
    parser.add_argument("--baseline", type=Path, help="baseline JSON for rate comparison")
    parser.add_argument("--json", action="store_true", help="print report to stdout")
    args = parser.parse_args()

    if args.input:
        report = json.loads(_resolve(args.input).read_text(encoding="utf-8"))
    else:
        specs = args.trips or list(DEFAULT_TRIPS)
        try:
            report = build_report(trip_specs=specs)
        except FileNotFoundError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            print("Hint: pass --trip tripId:path or --input existing JSON", file=sys.stderr)
            return 2

    if args.baseline:
        baseline = json.loads(_resolve(args.baseline).read_text(encoding="utf-8"))
        report["baselineComparison"] = compare_to_baseline(report.get("aggregate") or {}, baseline)
        report["acceptance"] = {
            "AC-PC-D-proxy": {
                "passed": report["baselineComparison"]["passed"],
                "note": "current defectRate <= baseline per slot (cover/hero/moment/all)",
            }
        }

    if args.write:
        out = _resolve(args.write)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {out}")

    if args.json or not args.write:
        print(json.dumps(report, indent=2, ensure_ascii=False))

    if report.get("acceptance", {}).get("AC-PC-D-proxy", {}).get("passed") is False:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
