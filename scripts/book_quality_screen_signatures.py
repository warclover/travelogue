#!/usr/bin/env python3
"""Compute screen signatures for P19 golden trips (S2 zero-diff gate).

Usage:
  python scripts/book_quality_screen_signatures.py
  python scripts/book_quality_screen_signatures.py --compare .cache/book-quality/baseline/manifest.json
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

from travelogue.config import AppConfig, get_config
from travelogue.eval.golden_trips import resolve_existing_golden_trips
from travelogue.eval.screen_sampler import screens_signature

from book_quality_baseline import _curate_trip, _p16_cfg
from lse_flags_curate_compare import _pattern_sequence, _screen_signatures


def _signatures_for_trip(trip_id: str, trip_dir: Path, cfg: AppConfig) -> dict[str, Any]:
    trip = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
    work = ROOT / ".cache" / "book-quality" / "signatures-work" / trip_id
    body = _curate_trip(trip, work_dir=work, cfg=cfg)
    chapters = body.get("chapters") or []
    return {
        "tripId": trip_id,
        "screensSignature": screens_signature(chapters, trip_id=trip_id),
        "patternSequence": _pattern_sequence(chapters),
        "screenSignatures": _screen_signatures(chapters),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="P19 screen signature batch")
    parser.add_argument("--out", type=Path, default=ROOT / ".cache" / "book-quality" / "screens-signatures")
    parser.add_argument("--compare", type=Path, help="Baseline manifest.json for diff report")
    args = parser.parse_args()

    cfg = _p16_cfg(get_config(reload=True))
    args.out.mkdir(parents=True, exist_ok=True)

    rows = [r for r in resolve_existing_golden_trips(root=ROOT) if r["exists"]]
    current: list[dict[str, Any]] = []
    for row in rows:
        tid = row["tripId"]
        print(f"Signature {tid}...")
        sig = _signatures_for_trip(tid, Path(row["tripDir"]), cfg)
        current.append(sig)

    out_path = args.out / "signatures.json"
    out_path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")

    if args.compare and args.compare.is_file():
        baseline = json.loads(args.compare.read_text(encoding="utf-8"))
        base_map = {t["tripId"]: t.get("screenSignatures") for t in baseline.get("trips") or []}
        mismatches = []
        for row in current:
            tid = row["tripId"]
            if base_map.get(tid) != row["screenSignatures"]:
                mismatches.append(tid)
        report = {"mismatches": mismatches, "ok": not mismatches}
        report_path = args.out / "diff_report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Diff: {len(mismatches)} mismatches -> {report_path}")
        return 1 if mismatches else 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
