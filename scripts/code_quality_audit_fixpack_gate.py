#!/usr/bin/env python3
"""CQA · aggregate local/CI gate (AC-CQA-23).

Runs the narrow command list for Code Quality Audit Fixpack.
Does NOT run full Playwright e2e.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STEPS: list[tuple[str, list[str]]] = [
    ("CQA god-module ratchet", [sys.executable, "scripts/lint_cqa_god_module_ratchet.py"]),
    ("CQA contract grep", [sys.executable, "scripts/lint_cqa_contract_grep.py"]),
    (
        "CQA M1/M2 unit contracts",
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/unit/web/test_cqa_lan_session.py",
            "tests/unit/web/test_cqa_llm_ping_isolation.py",
            "tests/unit/media/test_derivatives_ondemand_cqa.py",
            "tests/unit/export/test_cqa_longshot_upload.py",
            "tests/unit/export/test_longshot_current.py",
            "tests/unit/web/test_cqa_force_import_gate.py",
            "tests/unit/config/test_cqa_patch_config_atomic.py",
            "tests/unit/layout_engine/test_cqa_quality_pool_hoist.py",
            "tests/unit/curation/test_shot_grouping.py::test_rerun_clears_orphan_shot_group_fields",
        ],
    ),
    (
        "CQA FE contracts",
        [
            "node",
            "--test",
            "tests/js/cqa-llm-status-lifecycle.test.mjs",
            "tests/js/cqa-export-chapter-contracts.test.mjs",
            "tests/js/longshot-export-panel.test.mjs",
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
        print(f"\ncode_quality_audit_fixpack_gate: {failed} step(s) failed", file=sys.stderr)
        return 1
    print("\ncode_quality_audit_fixpack_gate: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
