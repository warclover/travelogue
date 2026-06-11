#!/usr/bin/env python3
"""P19 · new pattern / designer SKU share on golden trips.

Usage:
  python scripts/p19_pattern_share_audit.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from travelogue.eval.golden_trips import resolve_existing_golden_trips

from book_quality_baseline import _curate_trip, _p19_candidate_cfg
from travelogue.config import get_config

_P19_NEW_PATTERNS = frozenset(
    {
        "screen-justified-row",
        "screen-whitespace-hero",
        "screen-spread-folio",
        "screen-asymmetric-hero",
        "screen-full-frame-bsp-3-2",
    }
)
_DESIGNER_SKU = frozenset(
    {
        "screen-spread-folio",
        "screen-asymmetric-hero",
        "screen-whitespace-hero",
    }
)


def _pattern_stats(chapters: list[dict]) -> dict:
    seq: list[str] = []
    for ch in chapters:
        for s in ch.get("screens") or []:
            pid = s.get("patternId")
            if pid:
                seq.append(str(pid))
    total = len(seq)
    if not total:
        return {"screenCount": 0, "newPatternShare": 0.0, "designerSkuShare": 0.0}
    new_count = sum(1 for p in seq if p in _P19_NEW_PATTERNS)
    sku_count = sum(1 for p in seq if p in _DESIGNER_SKU)
    return {
        "screenCount": total,
        "newPatternCount": new_count,
        "newPatternShare": round(new_count / total, 4),
        "designerSkuCount": sku_count,
        "designerSkuShare": round(sku_count / total, 4),
        "patternSequence": seq,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="P19 pattern share audit")
    parser.add_argument("trip_id", nargs="*", help="Subset of golden trips")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / ".cache" / "book-quality" / "pattern-share-audit.json",
    )
    args = parser.parse_args()

    cfg = _p19_candidate_cfg(get_config(reload=True))
    rows = [r for r in resolve_existing_golden_trips(root=ROOT) if r["exists"]]
    if args.trip_id:
        wanted = set(args.trip_id)
        rows = [r for r in rows if r["tripId"] in wanted]

    per_trip: list[dict] = []
    for row in rows:
        tid = row["tripId"]
        trip = json.loads(
            Path(row["tripDir"]).joinpath("trip.json").read_text(encoding="utf-8")
        )
        work = ROOT / ".cache" / "book-quality" / "pattern-share-work" / tid
        body = _curate_trip(trip, work_dir=work, cfg=cfg)
        stats = _pattern_stats(body.get("chapters") or [])
        per_trip.append({"tripId": tid, **stats})
        print(
            f"{tid}: new {stats['newPatternShare']:.1%} "
            f"sku {stats['designerSkuShare']:.1%} screens={stats['screenCount']}"
        )

    new_shares = [t["newPatternShare"] for t in per_trip if t["screenCount"] > 0]
    sku_shares = [t["designerSkuShare"] for t in per_trip if t["screenCount"] > 0]
    report = {
        "trips": [
            {k: v for k, v in t.items() if k != "patternSequence"} for t in per_trip
        ],
        "medianNewPatternShare": round(sorted(new_shares)[len(new_shares) // 2], 4) if new_shares else 0.0,
        "medianDesignerSkuShare": round(sorted(sku_shares)[len(sku_shares) // 2], 4) if sku_shares else 0.0,
        "newPatternIds": sorted(_P19_NEW_PATTERNS),
        "designerSkuIds": sorted(_DESIGNER_SKU),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Median new {report['medianNewPatternShare']:.1%} · sku {report['medianDesignerSkuShare']:.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
