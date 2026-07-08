#!/usr/bin/env python3
"""AST lint: pipeline field mutations must use domain.pipeline_view helpers (M-C4)."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TRIP_DICT_NAMES = frozenset({"trip", "body", "work", "loaded", "snapshot"})
PIPELINE_MUTATION_KEYS = frozenset({"status", "locks", "runs", "timings", "layoutStatus"})

SCAN_PATHS = (
    ROOT / "travelogue" / "web" / "studio_handlers",
    ROOT / "travelogue" / "web" / "studio_g1.py",
    ROOT / "travelogue" / "web" / "studio_pipeline.py",
    ROOT / "travelogue" / "web" / "copy_patch.py",
    ROOT / "travelogue" / "services",
)

EXEMPT_FILES = frozenset(
    {
        (ROOT / "travelogue" / "services" / "trip.py").resolve(),
        (ROOT / "travelogue" / "services" / "pipeline_state.py").resolve(),
    }
)


def _literal_key(node: ast.expr) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _is_trip_name(node: ast.expr) -> bool:
    return isinstance(node, ast.Name) and node.id in TRIP_DICT_NAMES


def _is_pipeline_setdefault(node: ast.expr) -> bool:
    if not isinstance(node, ast.Call):
        return False
    if not isinstance(node.func, ast.Attribute) or node.func.attr != "setdefault":
        return False
    if not _is_trip_name(node.func.value):
        return False
    if not node.args:
        return False
    return _literal_key(node.args[0]) == "pipeline"


def _is_pipeline_subscript(node: ast.expr) -> bool:
    if not isinstance(node, ast.Subscript):
        return False
    if not _is_trip_name(node.value):
        return False
    return _literal_key(node.slice) == "pipeline"


def _is_pipeline_source(node: ast.expr) -> bool:
    return _is_pipeline_setdefault(node) or _is_pipeline_subscript(node)


def _is_under_pipeline(base: ast.expr, aliases: set[str]) -> bool:
    if isinstance(base, ast.Name) and base.id in aliases:
        return True
    if _is_pipeline_setdefault(base) or _is_pipeline_subscript(base):
        return True
    if isinstance(base, ast.Call):
        if isinstance(base.func, ast.Attribute) and base.func.attr == "setdefault":
            return _is_under_pipeline(base.func.value, aliases)
    if isinstance(base, ast.Subscript):
        return _is_under_pipeline(base.value, aliases)
    return False


def _leaf_subscript_key(node: ast.expr) -> str | None:
    if isinstance(node, ast.Subscript):
        return _literal_key(node.slice)
    return None


class PipelineMutationLintVisitor(ast.NodeVisitor):
    def __init__(self, rel_path: str) -> None:
        self.rel_path = rel_path
        self.violations: list[str] = []
        self._alias_stack: list[set[str]] = [set()]

    @property
    def _aliases(self) -> set[str]:
        merged: set[str] = set()
        for layer in self._alias_stack:
            merged |= layer
        return merged

    def _record_alias(self, name: str) -> None:
        self._alias_stack[-1].add(name)

    def _violation(self, node: ast.AST, *, detail: str) -> None:
        self.violations.append(
            f"{self.rel_path}:{node.lineno}: {detail}; "
            "use travelogue.domain.pipeline_view helpers"
        )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._alias_stack.append(set())
        self.generic_visit(node)
        self._alias_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)  # type: ignore[arg-type]

    def visit_Assign(self, node: ast.Assign) -> None:
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if _is_pipeline_source(node.value):
                self._record_alias(node.targets[0].id)

        for target in node.targets:
            self._check_assign_target(target)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._check_assign_target(node.target)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute) and node.func.attr == "append":
            base = node.func.value
            if _is_under_pipeline(base, self._aliases):
                runs_key = _leaf_subscript_key(base)
                if runs_key == "runs" or (
                    isinstance(base, ast.Call)
                    and base.args
                    and _literal_key(base.args[0]) == "runs"
                ):
                    self._violation(
                        node,
                        detail="direct pipeline.runs.append",
                    )
        self.generic_visit(node)

    def _check_assign_target(self, target: ast.expr) -> None:
        if not isinstance(target, ast.Subscript):
            return

        leaf_key = _literal_key(target.slice)
        if leaf_key not in PIPELINE_MUTATION_KEYS:
            return
        if not _is_under_pipeline(target, self._aliases):
            return
        self._violation(
            target,
            detail=f"direct trip.pipeline.{leaf_key} assignment",
        )


def iter_scan_files() -> list[Path]:
    files: list[Path] = []
    for entry in SCAN_PATHS:
        if entry.is_dir():
            files.extend(sorted(entry.rglob("*.py")))
        elif entry.is_file():
            files.append(entry)
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in files:
        resolved = path.resolve()
        if resolved in seen or resolved in EXEMPT_FILES:
            continue
        seen.add(resolved)
        unique.append(path)
    return unique


def lint_file(path: Path) -> list[str]:
    rel = path.relative_to(ROOT).as_posix()
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=rel)
    visitor = PipelineMutationLintVisitor(rel)
    visitor.visit(tree)
    return visitor.violations


def main() -> int:
    violations: list[str] = []
    for path in iter_scan_files():
        violations.extend(lint_file(path))
    if violations:
        print("\n".join(violations), file=sys.stderr)
        return 1
    print("lint_trip_pipeline_mutations: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
