#!/usr/bin/env python3
"""End-to-end acceptance for a real trip workspace (schema + layout equiv + telemetry).

Usage:
  python scripts/e2e_trip_acceptance.py linzhi
  python scripts/e2e_trip_acceptance.py linzhi mao --trips-dir trips
  python scripts/e2e_trip_acceptance.py linzhi --no-layout-equiv
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.services.trip import TripService
from travelogue.services.validate import validate_trip
from travelogue.web.studio_telemetry import build_pipeline_telemetry_summary


def _check_render_artifacts(trip_dir: Path, trip: dict) -> list[str]:
    issues: list[str] = []
    status = (trip.get("pipeline") or {}).get("status") or ""
    if status in ("rendered", "exported", "copy_draft", "copy_locked"):
        if not (trip_dir / "index.html").is_file():
            issues.append("pipeline rendered but index.html missing")
    return issues


def accept_trip(
    trip_path: Path,
    *,
    layout_equiv: bool = True,
) -> dict[str, Any]:
    trip_path = trip_path.resolve()
    trip_dir = trip_path.parent
    if not trip_path.is_file():
        return {"tripId": trip_dir.name, "ok": False, "error": "trip.json not found"}

    trip = TripService().load(trip_path)
    trip_id = str(trip.get("tripId") or trip_dir.name)

    errs = [e for e in validate_trip(trip, level="all") if not e.startswith("WARN:")]
    issues = list(errs)
    issues.extend(_check_render_artifacts(trip_dir, trip))

    layout_ok: bool | None = None
    if layout_equiv and not issues:
        from scripts.phase1_layout_equivalence import compare_trip

        result = compare_trip(trip_path, layout="web")
        layout_ok = bool(result.get("equivalent"))
        if not layout_ok:
            issues.append(
                f"phase1 layout equivalence failed "
                f"(legacy={result.get('legacyScreenCount')} scored={result.get('scoredScreenCount')})"
            )

    telemetry = build_pipeline_telemetry_summary(trip)
    return {
        "tripId": trip_id,
        "ok": not issues,
        "issues": issues,
        "layoutEquivalent": layout_ok,
        "pipelineStatus": telemetry.get("pipelineStatus"),
        "telemetry": telemetry,
        "assetCount": len(trip.get("assets") or []),
        "chapterCount": len(trip.get("chapters") or []),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Real-trip e2e acceptance")
    parser.add_argument("trip_ids", nargs="+", help="folder names under trips/")
    parser.add_argument("--trips-dir", type=Path, default=ROOT / "trips")
    parser.add_argument(
        "--no-layout-equiv",
        action="store_true",
        help="skip phase1 aspect-only layout equivalence",
    )
    parser.add_argument("--json", action="store_true", help="print JSON only")
    args = parser.parse_args()

    results: list[dict[str, Any]] = []
    failed = False
    for tid in args.trip_ids:
        path = args.trips_dir / tid / "trip.json"
        report = accept_trip(path, layout_equiv=not args.no_layout_equiv)
        results.append(report)
        if not report["ok"]:
            failed = True

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for r in results:
            status = "PASS" if r["ok"] else "FAIL"
            print(
                f"{status} {r['tripId']}  assets={r.get('assetCount')}  "
                f"chapters={r.get('chapterCount')}  status={r.get('pipelineStatus')}"
            )
            tel = r.get("telemetry") or {}
            timings = tel.get("timingsMs") or {}
            if timings:
                parts = ", ".join(f"{k}={v}" for k, v in sorted(timings.items()))
                print(f"  timings: {parts}")
            for issue in r.get("issues") or []:
                print(f"  ! {issue}")

    out = ROOT / "docs" / "acceptance-records" / "e2e-trip-acceptance.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not args.json:
        print(f"\nWrote {out}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
