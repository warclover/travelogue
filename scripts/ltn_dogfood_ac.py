#!/usr/bin/env python3
"""LTN dogfood AC runner · AC-B-02 / D-01 proxy / D-02 / D-03.

Default: CI fixture with hero mosaic chapter (no re-curate).
Optional: local trips/*/trip.json when present.

Usage:
  python scripts/ltn_dogfood_ac.py
  python scripts/ltn_dogfood_ac.py --out .cache/ltn-dogfood/report.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.layout_contract.ltn_dogfood import evaluate_dogfood_trip

DEFAULT_FIXTURE = ROOT / "tests/fixtures/ltn/trip.ltn_dogfood_hero_chapter.json"
OPTIONAL_DEMOS = (
    "demo-2025",
    "demo-815dc906d3",
    "demo-eb9a45b3c4",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="LTN dogfood AC checks")
    ap.add_argument(
        "--out",
        default=str(ROOT / ".cache" / "ltn-dogfood" / "report.json"),
    )
    ap.add_argument(
        "--include-demos",
        action="store_true",
        help="Also evaluate trips/<id>/trip.json when present",
    )
    args = ap.parse_args()

    targets: list[tuple[str, Path]] = [("fixture", DEFAULT_FIXTURE)]
    if args.include_demos:
        for tid in OPTIONAL_DEMOS:
            p = ROOT / "trips" / tid / "trip.json"
            if p.is_file():
                targets.append((tid, p))

    trips_out: list[dict] = []
    machine_ok = True
    for label, path in targets:
        if not path.is_file():
            continue
        trip = _load(path)
        row = evaluate_dogfood_trip(trip)
        row["source"] = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
        row["label"] = label
        trips_out.append(row)
        if label == "fixture":
            machine_ok = machine_ok and bool(row.get("machineOk"))
        elif row.get("AC-B-02", {}).get("heroMosaicCount", 0) > 0:
            machine_ok = machine_ok and bool(row.get("machineOk"))

    report = {
        "generatedAt": datetime.now(UTC).isoformat(),
        "prd": "PRD-LAYOUT-TRUST-NARRATIVE-V1 AC-B-02 / AC-D-01..03",
        "machineOk": machine_ok,
        "humanChecklist": {
            "AC-D-01": "Blind rhythm score ≥7 on small sample (proxy is advisory only)",
            "AC-B-02-visual": "Open dual preview; confirm mosaic still reads as 一组",
        },
        "trips": trips_out,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} machineOk={machine_ok} trips={len(trips_out)}")
    return 0 if machine_ok and trips_out else 1


if __name__ == "__main__":
    raise SystemExit(main())
