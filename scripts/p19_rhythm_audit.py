#!/usr/bin/env python3
"""Audit rhythm hard-constraint violations on golden trips (P19 S3).

Usage:
  python scripts/p19_rhythm_audit.py
  python scripts/p19_rhythm_audit.py demo-2025 demo-1506104ebf
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from travelogue.curation.layout_constraints import audit_rhythm_violations
from travelogue.eval.golden_trips import resolve_existing_golden_trips

from book_quality_baseline import _curate_trip, _p16_cfg
from travelogue.config import get_config


def _audit_trip(trip_id: str, trip_dir: Path, cfg) -> dict[str, Any]:
    trip = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
    work = ROOT / ".cache" / "book-quality" / "rhythm-audit" / trip_id
    body = _curate_trip(trip, work_dir=work, cfg=cfg)
    chapters = body.get("chapters") or []
    violations = audit_rhythm_violations(chapters)
    return {
        "tripId": trip_id,
        "violationCount": len(violations),
        "violations": [v.to_dict() for v in violations],
        "ok": not violations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="P19 rhythm violation audit")
    parser.add_argument("trip_id", nargs="*", help="Subset of golden trips")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / ".cache" / "book-quality" / "rhythm-audit" / "report.json",
    )
    args = parser.parse_args()

    cfg = _p16_cfg(get_config(reload=True))
    rows = resolve_existing_golden_trips(root=ROOT)
    if args.trip_id:
        wanted = set(args.trip_id)
        rows = [r for r in rows if r["tripId"] in wanted]

    results: list[dict[str, Any]] = []
    for row in rows:
        if not row["exists"]:
            results.append({"tripId": row["tripId"], "status": "missing", "ok": False})
            continue
        print(f"Audit {row['tripId']}...")
        results.append(_audit_trip(row["tripId"], Path(row["tripDir"]), cfg))

    report = {
        "trips": results,
        "ok": all(r.get("ok") for r in results if r.get("status") != "missing"),
        "totalViolations": sum(int(r.get("violationCount") or 0) for r in results),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Report: {args.out} · violations={report['totalViolations']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
