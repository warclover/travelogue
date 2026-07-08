#!/usr/bin/env python3
"""Fix repo-root Path(__file__).parents[N] after tests/ nesting."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"

IMPORT_LINE = "from tests._repo_root import repo_root\n"

PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"Path\(__file__\)\.resolve\(\)\.parents\[1\]"),
        "repo_root(__file__)",
    ),
    (
        re.compile(r"Path\(__file__\)\.resolve\(\)\.parents\[3\]"),
        "repo_root(__file__)",
    ),
]


def needs_repo_root(text: str) -> bool:
    return "repo_root(__file__)" in text or "Path(__file__).resolve().parents[" in text


def rewrite(path: Path) -> bool:
    if path.name in {"_repo_root.py", "conftest.py", "studio_test_helpers.py"}:
        return False
    text = path.read_text(encoding="utf-8")
    new_text = text
    for pattern, repl in PATTERNS:
        new_text = pattern.sub(repl, new_text)
    if new_text == text:
        return False
    if "from tests._repo_root import repo_root" not in new_text:
        if new_text.startswith('"""'):
            end = new_text.find('"""', 3)
            insert_at = end + 3
            if new_text[insert_at : insert_at + 1] == "\n":
                insert_at += 1
            new_text = new_text[:insert_at] + "\n\n" + IMPORT_LINE + new_text[insert_at:]
        else:
            new_text = IMPORT_LINE + "\n" + new_text
    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> int:
    updated = 0
    for path in TESTS.rglob("*.py"):
        if path.name == "test_ingest.py" and path.parent == TESTS:
            continue
        if rewrite(path):
            updated += 1
            print(path.relative_to(ROOT))
    print(f"updated {updated} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
