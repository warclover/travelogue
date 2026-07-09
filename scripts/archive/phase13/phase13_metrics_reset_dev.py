#!/usr/bin/env python3
"""Reset local dev template metrics (REL-02 prep for clean 72h window)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Reset ~/.travelogue template metrics jsonl")
    parser.add_argument("--yes", action="store_true", help="confirm delete")
    args = parser.parse_args()
    from travelogue.templating.metrics import metrics_path

    path = metrics_path()
    if not path.is_file():
        print(f"no file at {path}")
        return 0
    if not args.yes:
        print(f"would delete {path} — re-run with --yes")
        return 1
    path.unlink()
    print(f"deleted {path}")
    print("then: python scripts/phase13_metrics_window.py --hours 72 --write docs/acceptance-records/phase13-metrics-72h.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
