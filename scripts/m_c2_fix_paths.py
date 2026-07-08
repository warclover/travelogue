#!/usr/bin/env python3
"""Rewrite hardcoded tests/test_*.py paths in scripts/workflows after M-C2 migration."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "acceptance-records" / "m-c2-import-manifest.txt"

PATH_RE = re.compile(r"tests/test_[a-z0-9_]+\.py")


def load_manifest() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        old, new_mod = line.split("\t", 1)
        old_path = f"tests/{old}.py"
        new_path = "tests/" + new_mod.replace(".", "/") + ".py"
        mapping[old_path] = new_path
    return mapping


def rewrite_file(path: Path, mapping: dict[str, str]) -> bool:
    text = path.read_text(encoding="utf-8")
    changed = False

    def repl(match: re.Match[str]) -> str:
        nonlocal changed
        old = match.group(0)
        new = mapping.get(old, old)
        if new != old:
            changed = True
        return new

    new_text = PATH_RE.sub(repl, text)
    if changed:
        path.write_text(new_text, encoding="utf-8")
    return changed


def main() -> int:
    mapping = load_manifest()
    roots = [ROOT / "scripts", ROOT / ".github", ROOT / "travelogue"]
    updated = 0
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if path.suffix not in {".py", ".yml", ".yaml", ".ps1", ".sh", ".md"}:
                continue
            if path.name == "m-c2-import-manifest.txt":
                continue
            try:
                if rewrite_file(path, mapping):
                    updated += 1
                    print(path.relative_to(ROOT))
            except UnicodeDecodeError:
                continue
    print(f"updated {updated} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
