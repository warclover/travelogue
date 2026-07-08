#!/usr/bin/env python3
"""LSE cross-import regression gate (ADR-015 · M-B4 follow-up).

Fails if total layout_engine ↔ curation edges exceed ceiling (default: current baseline).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
BASELINE = ROOT / "docs" / "acceptance-records" / "lse-cross-import-baseline.json"
DEFAULT_CEILING = 10


def _edge_total(report: dict[str, object]) -> int:
    return int(report.get("totalCrossEdges", report.get("total_edges", 0)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-edges",
        type=int,
        default=None,
        help="Fail if total cross-import edges exceed this count",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Refresh baseline JSON when edge count decreased",
    )
    args = parser.parse_args()

    from scripts.lse_cross_import_stats import scan_edges, summarize

    report = summarize(scan_edges())
    total = _edge_total(report)
    ceiling = args.max_edges
    if ceiling is None and BASELINE.is_file():
        ceiling = _edge_total(json.loads(BASELINE.read_text(encoding="utf-8")))
    if ceiling is None:
        ceiling = DEFAULT_CEILING

    if args.update_baseline:
        if BASELINE.is_file():
            old_total = _edge_total(json.loads(BASELINE.read_text(encoding="utf-8")))
            if total > old_total:
                print(f"refusing baseline update: {total} > {old_total}", file=sys.stderr)
                return 1
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"baseline updated: {total} edges")
        return 0

    print(f"LSE cross-import edges: {total} (ceiling {ceiling})")
    if total > ceiling:
        print("REGRESSION: edge count above ceiling", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
