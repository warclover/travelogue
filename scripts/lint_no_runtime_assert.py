#!/usr/bin/env python3
"""AST lint: forbid Python ``assert`` statements under travelogue/ (ASH-P-01).

Runtime ``assert`` is stripped under ``-O`` / ``PYTHONOPTIMIZE``. Use explicit
``raise`` or named domain guards instead. See docs/PRD-ASSERTION-HARDENING-V1.md.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOW_MARKER = "ash: allow-assert"


def lint_file(path: Path) -> list[str]:
    rel = path.relative_to(ROOT).as_posix()
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=rel)
    except SyntaxError as exc:
        return [f"{rel}: syntax error: {exc}"]

    lines = source.splitlines()
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assert):
            continue
        lineno = node.lineno
        if 1 <= lineno <= len(lines) and ALLOW_MARKER in lines[lineno - 1]:
            continue
        violations.append(
            f"{rel}:{lineno}: runtime assert forbidden (ASH-P-01); "
            f"use raise or domain guard (see docs/TESTING.md §9)"
        )
    return violations


def main() -> int:
    violations: list[str] = []
    travelogue = ROOT / "travelogue"
    for path in sorted(travelogue.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        violations.extend(lint_file(path))
    if violations:
        print("\n".join(violations), file=sys.stderr)
        return 1
    print("lint_no_runtime_assert: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
