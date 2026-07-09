#!/usr/bin/env python3
"""Place ``from tests._repo_root import repo_root`` after __future__ imports."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
IMPORT = "from tests._repo_root import repo_root"


def fix_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if IMPORT not in text:
        return False
    lines = text.splitlines(keepends=True)
    # Drop misplaced import lines
    filtered = [ln for ln in lines if ln.strip() != IMPORT]
    text = "".join(filtered)
    if IMPORT in text:
        return False
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    insert_at = 0
    if (
        tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
    ):
        insert_at = tree.body[0].end_lineno or 0
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            insert_at = node.end_lineno or insert_at
    out_lines = text.splitlines(keepends=True)
    block = [IMPORT + "\n"]
    if insert_at < len(out_lines) and out_lines[insert_at : insert_at + 1] != ["\n"]:
        block.append("\n")
    new_lines = out_lines[:insert_at] + block + out_lines[insert_at:]
    new_text = "".join(new_lines)
    if new_text == text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> int:
    n = 0
    for path in TESTS.rglob("*.py"):
        if fix_file(path):
            n += 1
    print(f"fixed import order in {n} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
