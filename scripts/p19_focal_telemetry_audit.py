#!/usr/bin/env python3
"""Audit focalPoint coverage on P19 golden trips (AC-P19-02 telemetry proxy)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.eval.golden_trips import resolve_existing_golden_trips


def main() -> int:
    out = ROOT / ".cache" / "book-quality" / "focal-telemetry-audit.json"
    rows: list[dict] = []
    for row in resolve_existing_golden_trips(root=ROOT):
        tid = row["tripId"]
        trip_dir = Path(row["tripDir"])
        if not row["exists"]:
            rows.append({"tripId": tid, "status": "missing"})
            continue
        trip = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
        assets = [a for a in (trip.get("assets") or []) if a.get("type") == "image"]
        with_fp = sum(1 for a in assets if a.get("focalPoint"))
        total = len(assets)
        rate = round(with_fp / total, 4) if total else 0.0
        rows.append(
            {
                "tripId": tid,
                "status": "ok",
                "imageAssets": total,
                "withFocalPoint": with_fp,
                "focalPointRate": rate,
                "missingFocalPoint": total - with_fp,
            }
        )

    total_assets = sum(r.get("imageAssets", 0) for r in rows)
    total_with = sum(r.get("withFocalPoint", 0) for r in rows)
    summary = {
        "imageAssets": total_assets,
        "withFocalPoint": total_with,
        "focalPointRate": round(total_with / total_assets, 4) if total_assets else 0.0,
        "renderContextField": "focalFromAsset on slot entries (render/context.py)",
        "note": "Slot-level missing focal uses default 0.5/0.45; focalFromAsset=false in render context.",
    }
    report = {"trips": rows, "summary": summary}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Golden focal coverage: {summary['withFocalPoint']}/{summary['imageAssets']} ({summary['focalPointRate']})")
    print(f"Report: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
