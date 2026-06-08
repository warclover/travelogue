"""P17 W3b-12 readiness gate · does NOT flip global enabled=true.

Usage:
  python scripts/phase17_w3b12_readiness.py
  python scripts/phase17_w3b12_readiness.py --strict
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.layout_engine.readiness import evaluate_readiness_checks, w3b12_rollout_ready


def _run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 17 W3b-12 readiness checklist")
    parser.add_argument("--strict", action="store_true", help="Exit 1 when not ready")
    args = parser.parse_args()

    checks: dict[str, bool] = {}

    code, _ = _run([sys.executable, "-m", "pytest", "tests/test_p17_controlled_parity.py", "-q"])
    checks["controlledParity"] = code == 0

    code, _ = _run([sys.executable, "-m", "pytest", "tests/test_p17_w3a_gates.py", "-q"])
    checks["quickShareZeroDiff"] = code == 0

    code, _ = _run([sys.executable, "-m", "pytest", "tests/test_p17_w3a_zero_step_e2e.py", "-q"])
    checks["zeroStepE2E"] = code == 0

    code, _ = _run([sys.executable, "scripts/phase17_golden_metrics.py", "--strict"])
    checks["goldenMetricsStrict"] = code == 0

    code, _ = _run([sys.executable, "scripts/phase17_dogfood_admission.py", "--strict"])
    checks["dogfoodAdmissionStrict"] = code == 0

    code, _ = _run(
        [
            sys.executable,
            "scripts/phase17_curate_bench.py",
            "--fixture",
            "golden-mixed-scenes",
            "--fixture",
            "golden-p17-mixed-person",
            "--check",
        ]
    )
    checks["curatePerfBudget"] = code == 0

    readiness = evaluate_readiness_checks(
        golden_strict_passed=checks["goldenMetricsStrict"],
        dogfood_strict_passed=checks["dogfoodAdmissionStrict"],
        perf_within_budget=checks["curatePerfBudget"],
        parity_ok=checks["controlledParity"],
        quick_share_ok=checks["quickShareZeroDiff"],
        zero_step_ok=checks["zeroStepE2E"],
    )
    payload = {
        "rollout": w3b12_rollout_ready(),
        "readiness": readiness,
        "commandChecks": checks,
        "notes": "Passing this script does not enable LSE globally; product sign-off still required.",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.strict and not readiness.get("readyForW3b12Review"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
