#!/usr/bin/env python3
"""AST lint: trip dict saves must use TripService.update outside services/trip.py."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = ROOT / "travelogue" / "services" / "trip.py"
TRIP_DICT_NAMES = frozenset({"trip", "body", "work", "loaded", "snapshot"})
SVC_NAMES = frozenset({"svc", "trip_svc", "trip_service"})


class TripSaveLintVisitor(ast.NodeVisitor):
    def __init__(self, rel_path: str) -> None:
        self.rel_path = rel_path
        self.violations: list[str] = []

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute) and node.func.attr == "save":
            if self._is_forbidden_trip_save(node):
                self.violations.append(
                    f"{self.rel_path}:{node.lineno}: use TripService.update or "
                    "persist_trip_snapshot instead of direct save"
                )
        self.generic_visit(node)

    def _is_forbidden_trip_save(self, node: ast.Call) -> bool:
        if node.args:
            first = node.args[0]
            if isinstance(first, ast.Name) and first.id in TRIP_DICT_NAMES:
                return True
        if isinstance(node.func, ast.Attribute):
            base = node.func.value
            if isinstance(base, ast.Name) and base.id in SVC_NAMES:
                return True
            if isinstance(base, ast.Call) and node.args:
                first = node.args[0]
                if isinstance(first, ast.Name) and first.id in TRIP_DICT_NAMES:
                    return True
        return False


def lint_file(path: Path) -> list[str]:
    if path.resolve() == ALLOWED.resolve():
        return []
    rel = path.relative_to(ROOT).as_posix()
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=rel)
    visitor = TripSaveLintVisitor(rel)
    visitor.visit(tree)
    return visitor.violations


def main() -> int:
    violations: list[str] = []
    travelogue = ROOT / "travelogue"
    for path in sorted(travelogue.rglob("*.py")):
        violations.extend(lint_file(path))
    if violations:
        print("\n".join(violations), file=sys.stderr)
        return 1
    print("lint_trip_save_calls: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
