#!/usr/bin/env python3
"""M21 dogfood automated gate (M21-TEST-MATRIX §1 · M21-0 upload/resume subset).

Fast path (CI validate): unit + gate tests only.
Full path (local / nightly): adds M21-0 Playwright + rollback drill.

Usage:
    python scripts/m21_dogfood_gate.py --skip-e2e
    python scripts/m21_dogfood_gate.py
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

UNIT_TARGETS = [
    "tests/unit/web/test_studio_home_v2.py",
    "tests/unit/web/test_studio_homepage_gate.py",
    "tests/unit/web/test_studio_homepage_gate_security.py",
]

M21_0_E2E = [
    "tests/e2e/test_studio_home_v2_ac_playwright.py::test_ac_hp2_16_refresh_resumes_import",
    "tests/e2e/test_studio_home_v2_ac_playwright.py::test_ac_hp2_failed_retry_upload_reopens_sheet",
    "tests/e2e/test_studio_home_v2_ac_playwright.py::test_ac_hp2_resume_clears_stale_upload_pending",
]


def _run(cmd: list[str], *, label: str) -> int:
    print(f"\n== {label} ==", flush=True)
    print(" ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=ROOT)


def main() -> int:
    ap = argparse.ArgumentParser(description="M21 dogfood automated gate")
    ap.add_argument("--skip-e2e", action="store_true", help="skip Playwright + rollback drill")
    args = ap.parse_args()

    py = sys.executable
    rc = 0

    code = _run([py, "-m", "pytest", *UNIT_TARGETS, "-q"], label="M21 unit + gate")
    rc |= code

    code = _run([py, "scripts/m21_deploy_smoke.py", "--spawn"], label="deploy route smoke")
    rc |= code

    if args.skip_e2e:
        return rc

    code = _run(
        [py, "-m", "pytest", *M21_0_E2E, "-q", "-m", "e2e and playwright_serial"],
        label="M21-0 upload/resume e2e",
    )
    rc |= code

    code = _run([py, "scripts/studio_homepage_rollback_drill.py"], label="rollback drill")
    rc |= code

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
