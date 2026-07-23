#!/usr/bin/env python3
"""QFX · aggregate local/CI gate (AC-QFX-24).

Runs the narrow command list from PRD §11.1 + M3 unit contracts.
Does NOT run full Playwright e2e.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STEPS: list[tuple[str, list[str]]] = [
    ("CSC recipe baseline", [sys.executable, "scripts/lint_csc_recipe_baseline.py"]),
    ("CSC god-module ratchet", [sys.executable, "scripts/lint_csc_god_module_ratchet.py"]),
    ("layout_engine facade", [sys.executable, "scripts/lint_layout_engine_facade.py"]),
    ("UI Detail static --strict", [sys.executable, "scripts/studio_ui_detail_static_audit.py", "--strict"]),
    (
        "QFX unit contracts",
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/unit/web/test_ai_surface_gate.py",
            "tests/unit/web/test_studio_ui_detail_static_audit.py",
            "tests/unit/web/test_ui_detail_harness_metrics.py",
            "tests/unit/domain/test_photo_keep_mode.py",
            "tests/unit/export/test_longshot_current.py",
            "tests/unit/config/test_l1_dom_equals_happy_path.py",
            "tests/unit/curation/test_keep_all_skips_low_res.py",
        ],
    ),
]


def main() -> int:
    failed = 0
    for label, cmd in STEPS:
        print(f"\n==> {label}")
        print(" ".join(cmd))
        proc = subprocess.run(cmd, cwd=ROOT)
        if proc.returncode != 0:
            print(f"FAIL: {label} (exit {proc.returncode})", file=sys.stderr)
            failed += 1
    if failed:
        print(f"\nquality_fixpack_gate: {failed} step(s) failed", file=sys.stderr)
        return 1
    print("\nquality_fixpack_gate: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
