#!/usr/bin/env python3
"""Generate BSP surface measurement report under .cache/book-quality/ (PRD R-BSP-P3-04)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "templates" / "bsp-surface-report.json"
OUT_DIR = ROOT / ".cache" / "book-quality"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run BSP Playwright tests and write surface report stub.")
    parser.add_argument(
        "--trips",
        nargs="*",
        default=["demo-d66fe642a9", "linzhi"],
        help="Trip IDs referenced in the report template",
    )
    parser.add_argument("--skip-tests", action="store_true", help="Only write report skeleton")
    args = parser.parse_args()

    if not args.skip_tests:
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/e2e/test_bsp_surface_playwright.py",
            "-q",
            "--tb=line",
        ]
        print("Running", " ".join(cmd))
        proc = subprocess.run(cmd, cwd=ROOT)
        if proc.returncode != 0:
            return proc.returncode

    template = json.loads(TEMPLATE.read_text(encoding="utf-8")) if TEMPLATE.is_file() else {}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    out_path = OUT_DIR / f"surface-report-{stamp}.json"
    payload = {
        "generatedAt": datetime.now(UTC).isoformat(),
        "pytest": "tests/e2e/test_bsp_surface_playwright.py",
        "status": "pass" if not args.skip_tests else "skeleton",
        "trips": {tid: template.get("trips", {}).get(tid, {}) for tid in args.trips},
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
