"""Phase 6 pipeline performance proxy (AC-P6-06).

Usage:
  python scripts/phase6_pipeline_perf.py
  python scripts/phase6_pipeline_perf.py --write
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD_PATH = ROOT / "docs" / "acceptance-records" / "phase6-quality-eval.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 6 pipeline perf proxy on CI fixtures")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--record", type=Path, default=RECORD_PATH)
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT))
    from scripts.phase6_benchmark_run import eval_pipeline_perf, merge_into_record, run_benchmark

    stats = eval_pipeline_perf()
    print(json.dumps(stats, indent=2, ensure_ascii=False))

    if args.write and args.record.is_file():
        report = run_benchmark(skip_cluster_noise=True)
        report["AC-P6-06"] = stats
        merge_into_record(report, args.record)

    return 0 if stats.get("passed") is not False else 1


if __name__ == "__main__":
    raise SystemExit(main())
