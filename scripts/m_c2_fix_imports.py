#!/usr/bin/env python3
"""Rewrite ``from tests.test_*`` imports after M-C2 bulk migration."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "acceptance-records" / "m-c2-import-manifest.txt"

IMPORT_RE = re.compile(
    r"(?P<prefix>from tests\.)(?P<mod>test_[a-z0-9_]+)(?P<suffix> import .*)"
)


def load_manifest() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        old, new = line.split("\t", 1)
        mapping[old] = new
    return mapping


def rewrite_file(path: Path, mapping: dict[str, str]) -> bool:
    text = path.read_text(encoding="utf-8")
    changed = False

    def repl(match: re.Match[str]) -> str:
        nonlocal changed
        mod = match.group("mod")
        if mod not in mapping:
            return match.group(0)
        changed = True
        return f"{match.group('prefix')}{mapping[mod]}{match.group('suffix')}"

    new_text = IMPORT_RE.sub(repl, text)
    if changed:
        path.write_text(new_text, encoding="utf-8")
    return changed


def main() -> int:
    if not MANIFEST.is_file():
        print(f"missing manifest: {MANIFEST}", file=sys.stderr)
        return 1
    mapping = load_manifest()
    roots = [ROOT / "tests", ROOT / "scripts", ROOT / "travelogue"]
    updated = 0
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*.py"):
            if rewrite_file(path, mapping):
                updated += 1
                print(path.relative_to(ROOT))
    print(f"updated {updated} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
