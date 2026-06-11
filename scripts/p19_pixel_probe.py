#!/usr/bin/env python3
"""P19 pixel-layer probe CLI (focal CSS + LTE slot aspect + mosaic geometry)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.eval.pixel_probe import run_p19_pixel_probe


def main() -> int:
    parser = argparse.ArgumentParser(description="P19 pixel probe")
    parser.add_argument(
        "--out",
        type=Path,
        help="Optional JSON report path",
    )
    args = parser.parse_args()
    report = run_p19_pixel_probe()
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
