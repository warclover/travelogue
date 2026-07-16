#!/usr/bin/env python3
"""Run AC-AAD-04 must-green nodeids (docs/acceptance-records/aad-must-green-nodeids.txt)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIST = ROOT / "docs" / "acceptance-records" / "aad-must-green-nodeids.txt"


def _nodeids() -> list[str]:
    out: list[str] = []
    for line in LIST.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out.append(s)
    return out


def main() -> int:
    ids = _nodeids()
    if not ids:
        print("no nodeids in", LIST, file=sys.stderr)
        return 2
    cmd = [sys.executable, "-m", "pytest", *ids, "-q", "--tb=line"]
    print(" ".join(cmd))
    return subprocess.call(cmd, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
