#!/usr/bin/env python3
"""CQA · contract grep gate (AC-03 / AC-17).

Fails when forbidden write paths reappear in product code.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (glob roots, pattern, note)
CHECKS: list[tuple[list[str], str, str]] = [
    (
        ["travelogue/web", "travelogue/llm"],
        r"read_user_llm_secrets\s*=",
        "module-level secrets monkey-patch (AC-CQA-03)",
    ),
    (
        ["travelogue"],
        r"trackOverrideByVariant\s*=",
        "MSA byVariant write (AC-CQA-17)",
    ),
]


def _iter_py(roots: list[str]) -> list[Path]:
    out: list[Path] = []
    for rel in roots:
        base = ROOT / rel
        if base.is_file() and base.suffix == ".py":
            out.append(base)
            continue
        if not base.is_dir():
            continue
        out.extend(p for p in base.rglob("*.py") if p.is_file())
    return out


def main() -> int:
    failed = 0
    for roots, pattern, note in CHECKS:
        rx = re.compile(pattern)
        hits: list[str] = []
        for path in _iter_py(roots):
            text = path.read_text(encoding="utf-8")
            for i, line in enumerate(text.splitlines(), 1):
                if rx.search(line):
                    rel = path.relative_to(ROOT).as_posix()
                    hits.append(f"{rel}:{i}: {line.strip()}")
        if hits:
            failed += 1
            print(f"FAIL: {note}", file=sys.stderr)
            for h in hits:
                print(f"  {h}", file=sys.stderr)
        else:
            print(f"ok: {note}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
