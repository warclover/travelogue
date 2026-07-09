#!/usr/bin/env python3
"""M-C2 guard: block new top-level tests/test_*.py outside unit/integration/e2e."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
BASELINE = ROOT / "docs" / "acceptance-records" / "m-c2-top-level-baseline.txt"


def top_level_test_files() -> set[str]:
    return {p.name for p in TESTS.glob("test_*.py") if p.is_file()}


def load_baseline() -> set[str]:
    if not BASELINE.is_file():
        raise FileNotFoundError(f"missing baseline: {BASELINE}")
    lines = BASELINE.read_text(encoding="utf-8").splitlines()
    return {line.strip() for line in lines if line.strip() and not line.startswith("#")}


def main() -> int:
    current = top_level_test_files()
    allowed = load_baseline()
    unexpected = current - allowed
    if unexpected:
        print(
            "lint_test_layout: new top-level tests/ files (move under tests/unit/, "
            "tests/integration/, or tests/e2e/):\n"
            + "\n".join(f"  - tests/{name}" for name in sorted(unexpected)),
            file=sys.stderr,
        )
        return 1
    print(f"lint_test_layout: OK ({len(current)} top-level files frozen)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
