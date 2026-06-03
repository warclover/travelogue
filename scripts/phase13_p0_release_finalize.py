#!/usr/bin/env python3
"""P0 release finalize: drills → metrics reset → 72h → G8 → checklists (correct order)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "docs" / "acceptance-records"


def _run(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    return subprocess.run(cmd, cwd=ROOT).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 13 P0 release finalize")
    parser.add_argument("--skip-prod-state-drill", action="store_true")
    args = parser.parse_args()

    py = sys.executable
    steps = [
        [py, "scripts/phase13_rollback_drill.py", "--write", str(RECORDS / "phase13-rollback-drill-staging.json")],
    ]
    if not args.skip_prod_state_drill:
        steps.append(
            [
                py,
                "scripts/phase13_rollback_drill.py",
                "--use-project-state",
                "--write",
                str(RECORDS / "phase13-rollback-drill-prod-staging.json"),
            ]
        )
    steps.extend(
        [
            [py, "scripts/phase13_metrics_reset_dev.py", "--yes"],
            [py, "scripts/phase13_metrics_window.py", "--hours", "72", "--write", str(RECORDS / "phase13-metrics-72h.json")],
            [
                py,
                "scripts/phase13_g8_walkthrough_automated.py",
                "--playwright",
                "--sign-if-pass",
                "--write",
                str(RECORDS / "phase13-g8-signoff.json"),
            ],
            [py, "scripts/phase13_g8_automation_check.py", "--merge-signoff", "--write", str(RECORDS / "phase13-g8-signoff.json")],
            [py, "scripts/phase13_gate_signoff.py", "--write", str(RECORDS / "phase13-gate-signoff.json")],
            [py, "scripts/phase13_release_day_checklist.py", "--write", str(RECORDS / "phase13-release-day-checklist.json")],
            [py, "scripts/phase13_release_day_gate_section5.py", "--write", str(RECORDS / "phase13-release-day-gate-section5.json")],
        ]
    )
    for cmd in steps:
        if _run(cmd) != 0:
            return 1
    print("P0 finalize complete (dev). Production: re-run 72h metrics on real traffic without reset.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
