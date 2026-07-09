#!/usr/bin/env python3
"""Phase 14 automated acceptance gate (pytest subset + summary JSON)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

PHASE14_TESTS = [
    "tests/unit/web/test_studio_home_v2.py::test_studio_home_v2_phase14_dual_mode_smoke",
    "tests/unit/web/handlers/test_studio_handlers_import_export.py",
    "tests/unit/web/test_studio_intent.py",
    "tests/unit/layout_engine/test_layout_density.py",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 14 acceptance gate")
    parser.add_argument(
        "--write",
        type=Path,
        default=REPO / "docs" / "acceptance-records" / "phase14-test-summary.json",
    )
    parser.add_argument("--pytest-args", default="-q", help="Extra pytest args")
    args = parser.parse_args()

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *PHASE14_TESTS,
        *args.pytest_args.split(),
    ]
    proc = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, encoding="utf-8", errors="replace")
    summary = {
        "generatedAt": datetime.now(UTC).isoformat(),
        "phase": "P14-DualMode",
        "pytestCommand": " ".join(cmd),
        "exitCode": proc.returncode,
        "passed": proc.returncode == 0,
        "stdoutTail": proc.stdout[-4000:] if proc.stdout else "",
        "stderrTail": proc.stderr[-2000:] if proc.stderr else "",
        "manualRemaining": [
            "AC-P14-08 full-chain manual soak",
            "Four viewport screenshots for sign-off",
        ],
    }
    args.write.parent.mkdir(parents=True, exist_ok=True)
    args.write.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result_msg = json.dumps({"passed": summary["passed"], "write": str(args.write)}, ensure_ascii=True)
    print(result_msg)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
