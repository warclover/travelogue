#!/usr/bin/env python3
"""LTN R-E2 · weekly dashboard from existing trip.json (no re-curate).

Reads chapters + curation.mosaicDecisionLog; writes aggregate JSON.

Usage:
  python scripts/ltn_weekly_dashboard.py
  python scripts/ltn_weekly_dashboard.py demo-2025 --out .cache/ltn-weekly/report.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.layout_engine.mosaic.ltn_weekly import compute_ltn_weekly_metrics

DEFAULT_TARGETS = (
    "demo-65db8fd377",
    "demo-eb9a45b3c4",
    "demo-2025",
    "demo-815dc906d3",
)


def _load_trip(target: str) -> tuple[str, dict]:
    p = Path(target)
    if p.is_file():
        data = json.loads(p.read_text(encoding="utf-8"))
        return p.stem, data
    trip_path = ROOT / "trips" / target / "trip.json"
    if not trip_path.is_file():
        raise FileNotFoundError(f"trip not found: {target}")
    data = json.loads(trip_path.read_text(encoding="utf-8"))
    return target, data


def main() -> int:
    ap = argparse.ArgumentParser(description="LTN weekly dashboard (read-only)")
    ap.add_argument(
        "targets",
        nargs="*",
        default=list(DEFAULT_TARGETS),
        help="trip ids under trips/ or path to trip.json",
    )
    ap.add_argument(
        "--out",
        default=str(ROOT / ".cache" / "ltn-weekly" / "report.json"),
        help="output JSON path",
    )
    ap.add_argument(
        "--strict-c01",
        action="store_true",
        help="include AC-C-01 isolation-replay strict rate (expensive)",
    )
    ap.add_argument(
        "--ac-c01-baseline",
        type=float,
        default=None,
        help="optional baseline rate for relative ↓≥50%% gate (with --strict-c01)",
    )
    args = ap.parse_args()

    trips_out: list[dict] = []
    skipped: list[str] = []
    for t in args.targets:
        try:
            trip_id, trip = _load_trip(t)
        except (OSError, json.JSONDecodeError, FileNotFoundError) as exc:
            skipped.append(f"{t}: {exc}")
            continue
        metrics = compute_ltn_weekly_metrics(
            trip,
            include_ac_c01_strict=bool(args.strict_c01),
            ac_c01_baseline_rate=args.ac_c01_baseline,
        )
        trips_out.append({"tripId": trip_id, "metrics": metrics})

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": "trip.json (no re-curate)",
        "prd": "PRD-LAYOUT-TRUST-NARRATIVE-V1 §12 / R-E2",
        "tripCount": len(trips_out),
        "trips": trips_out,
        "skipped": skipped,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {out_path} ({len(trips_out)} trips, {len(skipped)} skipped)")
    return 0 if trips_out else 1


if __name__ == "__main__":
    raise SystemExit(main())
