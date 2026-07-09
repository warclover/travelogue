"""Phase 4 automated acceptance gate (AC-P4-02/05 · A11Y static · intent suite).

E2e (FirstSuccess featured summary): ``pytest tests/e2e/test_studio_intent_ac_p4_playwright.py``
(CI ``test-e2e`` job). This script covers unit/static checks only.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PYTEST_TARGETS = [
    "tests/unit/web/test_studio_a11y_p4.py",
    "tests/unit/web/test_studio_intent_ac_p4.py",
    "tests/unit/web/test_studio_intent.py",
    "tests/unit/web/test_studio_entry.py",
    "tests/unit/web/test_studio_intent_telemetry.py",
    "tests/unit/curation/test_intent_plan.py",
    "tests/unit/web/test_studio_g1.py",
    "tests/unit/media/test_user_tier.py",
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 4 automated acceptance gate")
    ap.add_argument("--skip-integration", action="store_true", help="skip integration-marked tests")
    args = ap.parse_args()
    cmd = [sys.executable, "-m", "pytest", *PYTEST_TARGETS, "-q"]
    if args.skip_integration:
        cmd.extend(["-m", "not integration"])
    print(" ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
