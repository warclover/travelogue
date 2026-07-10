#!/usr/bin/env python3
"""AST lint: layout_contract stays a layer-0 kernel (P2-C).

Rules:
- May only import stdlib, same-package modules, or other layer-0 packages
  (util / types / domain / constants / paths / errors / manifest_limits).
- Must not import curation, layout_engine, web, templating, services, media, etc.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "travelogue" / "layout_contract"

# Layer-0 peers allowed beside layout_contract itself (TECH-ARCH §18.1).
ALLOWED_TRAVELLOGUE_PREFIXES = (
    "travelogue.layout_contract",
    "travelogue.util",
    "travelogue.types",
    "travelogue.domain",
    "travelogue.constants",
    "travelogue.paths",
    "travelogue.errors",
    "travelogue.manifest_limits",
)

# Explicit denylist for clearer diagnostics (subset of non-layer-0 packages).
FORBIDDEN_PREFIXES = (
    "travelogue.curation",
    "travelogue.layout_engine",
    "travelogue.layout_templates",
    "travelogue.web",
    "travelogue.templating",
    "travelogue.cli",
    "travelogue.desktop",
    "travelogue.orchestrator",
    "travelogue.render",
    "travelogue.export",
    "travelogue.services",
    "travelogue.media",
    "travelogue.vision",
    "travelogue.llm",
    "travelogue.config",
)


def _is_allowed_travelogue(mod: str) -> bool:
    return any(
        mod == p or mod.startswith(p + ".") for p in ALLOWED_TRAVELLOGUE_PREFIXES
    )


def _is_forbidden(mod: str) -> bool:
    return any(mod == p or mod.startswith(p + ".") for p in FORBIDDEN_PREFIXES)


def _imported_modules(tree: ast.AST) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                found.append((node.lineno, node.module))
    return found


def lint_file(path: Path) -> list[str]:
    rel = path.relative_to(ROOT).as_posix()
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=rel)
    violations: list[str] = []
    for lineno, mod in _imported_modules(tree):
        if not mod.startswith("travelogue"):
            continue
        if _is_allowed_travelogue(mod):
            continue
        if _is_forbidden(mod):
            violations.append(
                f"{rel}:{lineno}: layout_contract must not import {mod} "
                "(layer-0 kernel · P2-C)"
            )
        else:
            violations.append(
                f"{rel}:{lineno}: layout_contract import of {mod} is not on the "
                "layer-0 allowlist (P2-C)"
            )
    return violations


def lint_package(package: Path = PACKAGE) -> list[str]:
    violations: list[str] = []
    for path in sorted(package.rglob("*.py")):
        violations.extend(lint_file(path))
    return violations


def main() -> int:
    violations = lint_package()
    if violations:
        print("\n".join(violations), file=sys.stderr)
        return 1
    print("lint_layout_contract_surface: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
