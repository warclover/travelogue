#!/usr/bin/env python3
"""Local + CI quality gate: schema fixtures + layout/studio regression tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FIXTURES = [
    "schemas/fixtures/trip.example.json",
    "schemas/fixtures/trip.ingest_ready.json",
    "schemas/fixtures/trip.structure_locked.json",
    "schemas/fixtures/trip.copy_locked.json",
    "schemas/fixtures/trip.render_golden.json",
    "schemas/fixtures/trip.linzhi_screens.json",
    "schemas/fixtures/trip.phase10_food_grid.json",
]

REGRESSION_TESTS = [
    "tests/unit/layout_engine/test_layout_search.py",
    "tests/unit/layout_engine/test_layout_scoring.py",
    "tests/unit/web/handlers/test_studio_handlers_trip.py",
    "tests/unit/web/test_studio_subprocess.py",
    "tests/unit/web/test_studio_telemetry.py",
    "tests/unit/config/test_algorithm_profile.py",
    "tests/unit/web/test_studio_aesthetic.py",
]


def _run(cmd: list[str], *, label: str) -> int:
    print(f"\n== {label} ==", flush=True)
    print(" ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=ROOT)
    return proc.returncode


def main() -> int:
    failed = 0
    for rel in FIXTURES:
        path = ROOT / rel
        if not path.is_file():
            print(f"SKIP missing fixture: {rel}", file=sys.stderr)
            failed = 1
            continue
        code = _run(
            [sys.executable, "scripts/validate_trip.py", str(path), "--level", "all"],
            label=f"validate {rel}",
        )
        failed |= code

    code = _run(
        [sys.executable, "-m", "pytest", *REGRESSION_TESTS, "-q"],
        label="regression pytest",
    )
    failed |= code

    replay_script = ROOT / "scripts" / "replay_curate_baseline.py"
    golden = ROOT / "schemas" / "fixtures" / "curate_baseline.golden.json"
    if replay_script.is_file() and golden.is_file():
        code = _run(
            [sys.executable, str(replay_script), "--check", str(golden)],
            label="curate baseline replay",
        )
        failed |= code

    if failed:
        print("\nQUALITY GATE FAILED", file=sys.stderr)
        return 1
    print("\nQUALITY GATE OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
