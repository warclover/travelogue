#!/usr/bin/env python3
"""Run Phase 15 offline acceptance bundle (replay + eval + gate + pytest hint)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "docs" / "acceptance-records"


def _run(cmd: list[str], label: str) -> int:
    print(f"\n=== {label} ===", flush=True)
    print(" ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=ROOT)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-pytest", action="store_true")
    ap.add_argument("--with-local-trips", action="store_true")
    args = ap.parse_args()

    py = sys.executable
    steps: list[tuple[str, list[str]]] = [
        (
            "replay scenarios",
            [py, "scripts/phase15_replay_scenarios.py", "--write", str(RECORDS / "phase15-replay-scenarios.json")],
        ),
        (
            "mosaic5 eval",
            [py, "scripts/phase15_mosaic_eval.py", "--write", str(RECORDS / "phase15-mosaic-eval.json")],
        ),
        (
            "curate replay (fixture)",
            [
                py,
                "scripts/phase15_curate_replay.py",
                "golden-mixed-scenes",
                "--fixture",
                "--write",
                str(RECORDS / "phase15-curate-replay.json"),
            ],
        ),
        (
            "unified gate",
            [py, "scripts/phase15_unified_gate.py"],
        ),
    ]
    if args.with_local_trips:
        local_out = RECORDS / "phase15-curate-replay-local.json"
        steps.insert(
            -1,
            (
                "curate replay (local trips)",
                [
                    py,
                    "scripts/phase15_curate_replay.py",
                    "mao",
                    "maomi",
                    "linzhi",
                    "--write",
                    str(local_out),
                ],
            ),
        )

    rc = 0
    for label, cmd in steps:
        code = _run(cmd, label)
        if code != 0:
            rc = code

    if not args.skip_pytest:
        code = _run([py, "-m", "pytest", "tests/", "-k", "mosaic", "-q"], "pytest mosaic")
        if code != 0:
            rc = code

    if rc == 0:
        print("\nPASS Phase 15 acceptance bundle", flush=True)
    else:
        print("\nFAIL Phase 15 acceptance bundle", flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
