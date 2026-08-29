#!/usr/bin/env python3
"""RCL W0 · frontend live-path closure lint.

Closure roots are hardcoded (BLK-RCL-09). Inventory lives in
``docs/frontend-live-path.md``. Files in the closure must be registered.
FROZEN files must not be imported from the LIVE closure.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs" / "frontend-live-path.md"

# BLK-RCL-09 · do not add a third root, do not read "or current entry" from HTML.
LIVE_PATH_ROOTS: tuple[str, ...] = (
    "templates/studio/preview-toolbar.js",
    "templates/studio/homepage-v2/bootstrap.js",
)

STATUSES = frozenset({"LIVE", "READER", "FROZEN", "GENERATED"})
_ROW_RE = re.compile(
    r"^\|\s*`([^`]+)`\s*\|\s*(LIVE|READER|FROZEN|GENERATED)\s*\|",
    re.M,
)
_FROM_RE = re.compile(r"""\bfrom\s+['\"]([^'\"]+)['\"]""")
_BARE_IMPORT_RE = re.compile(r"""(?:^|[;\n])\s*import\s+['\"]([^'\"]+)['\"]""")
_DYNAMIC_IMPORT_RE = re.compile(r"""\bimport\(\s*['\"]([^'\"]+)['\"]\s*\)""")
_EXPORT_STAR_RE = re.compile(r"""\bexport\s+\*\s+from\s+['\"]([^'\"]+)['\"]""")


@dataclass(frozen=True)
class InventoryRow:
    path: str
    status: str


def strip_js_comments(source: str) -> str:
    """Strip // and /* */ outside string / template literals."""
    out: list[str] = []
    i = 0
    n = len(source)
    quote: str | None = None
    template_expr = 0
    while i < n:
        ch = source[i]
        nxt = source[i + 1] if i + 1 < n else ""
        if quote:
            out.append(ch)
            if ch == "\\" and quote != "`":
                if i + 1 < n:
                    out.append(source[i + 1])
                    i += 2
                    continue
            if quote == "`" and ch == "$" and nxt == "{":
                out.append(nxt)
                template_expr += 1
                i += 2
                continue
            if quote == "`" and ch == "}" and template_expr:
                template_expr -= 1
                i += 1
                continue
            if ch == quote and not (quote == "`" and template_expr):
                quote = None
            i += 1
            continue
        if ch in {'"', "'", "`"}:
            quote = ch
            out.append(ch)
            i += 1
            continue
        if ch == "/" and nxt == "/":
            i += 2
            while i < n and source[i] not in "\n":
                i += 1
            continue
        if ch == "/" and nxt == "*":
            i += 2
            while i < n - 1 and not (source[i] == "*" and source[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def extract_import_specs(source: str) -> list[str]:
    text = strip_js_comments(source)
    specs: list[str] = []
    specs.extend(_FROM_RE.findall(text))
    specs.extend(_BARE_IMPORT_RE.findall(text))
    specs.extend(_DYNAMIC_IMPORT_RE.findall(text))
    specs.extend(_EXPORT_STAR_RE.findall(text))
    return specs


def resolve_specifier(src: Path, spec: str, root: Path = ROOT) -> Path | None:
    if not spec.startswith("."):
        return None
    raw = (src.parent / spec).resolve()
    candidates = [raw]
    if raw.suffix == "":
        candidates += [raw.with_suffix(".js"), raw / "index.js"]
    for candidate in candidates:
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            continue
        if candidate.is_file():
            return candidate
    return None


def walk_live_closure(root: Path = ROOT, roots: tuple[str, ...] = LIVE_PATH_ROOTS) -> set[str]:
    if tuple(roots) != LIVE_PATH_ROOTS:
        raise ValueError("live-path roots must be the two hardcoded constants")
    seen: set[str] = set()
    queue = [root / rel for rel in roots]
    missing: list[str] = []
    while queue:
        path = queue.pop()
        rel = path.relative_to(root).as_posix()
        if rel in seen:
            continue
        if not path.is_file():
            missing.append(rel)
            continue
        seen.add(rel)
        text = path.read_text(encoding="utf-8")
        for spec in extract_import_specs(text):
            dest = resolve_specifier(path, spec, root=root)
            if dest is None:
                continue
            drel = dest.relative_to(root).as_posix()
            if drel not in seen:
                queue.append(dest)
    if missing:
        raise FileNotFoundError("live-path root missing: " + ", ".join(missing))
    return seen


def importers_of(root: Path, closure: set[str]) -> dict[str, list[str]]:
    edges: dict[str, list[str]] = {rel: [] for rel in closure}
    for rel in closure:
        src = root / rel
        for spec in extract_import_specs(src.read_text(encoding="utf-8")):
            dest = resolve_specifier(src, spec, root=root)
            if dest is None:
                continue
            drel = dest.relative_to(root).as_posix()
            if drel in edges and rel not in edges[drel]:
                edges[drel].append(rel)
    return edges


def parse_inventory(text: str) -> list[InventoryRow]:
    rows: list[InventoryRow] = []
    seen: set[str] = set()
    for match in _ROW_RE.finditer(text):
        rel = match.group(1).replace("\\", "/").strip()
        status = match.group(2)
        if rel in seen:
            raise ValueError(f"duplicate inventory row: {rel}")
        seen.add(rel)
        rows.append(InventoryRow(path=rel, status=status))
    return rows


def check_live_path(
    root: Path = ROOT,
    inventory_text: str | None = None,
    inventory_path: Path = INVENTORY,
) -> list[str]:
    if inventory_text is None:
        if not inventory_path.is_file():
            return [f"missing inventory: {inventory_path.as_posix()}"]
        inventory_text = inventory_path.read_text(encoding="utf-8")
    try:
        rows = parse_inventory(inventory_text)
    except ValueError as exc:
        return [str(exc)]
    if not rows:
        return ["inventory has no status rows"]
    by_path = {row.path: row for row in rows}
    violations: list[str] = []
    try:
        closure = walk_live_closure(root)
    except (FileNotFoundError, ValueError) as exc:
        return [str(exc)]
    for rel in sorted(closure):
        row = by_path.get(rel)
        if row is None:
            violations.append(f"unregistered live-path file: {rel}")
            continue
        if row.status == "FROZEN":
            violations.append(f"FROZEN imported by LIVE closure: {rel}")
    edges = importers_of(root, closure)
    for row in rows:
        if row.status != "FROZEN":
            continue
        # Extra FROZEN rows are fine; only fail if a LIVE-closure file imports them.
        # walk_live_closure already excludes FROZEN-only islands. Recheck edges
        # in case the file is listed FROZEN but also reachable (caught above).
        _ = edges
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dump-closure",
        action="store_true",
        help="Print the LIVE closure and exit (for inventory refresh)",
    )
    args = parser.parse_args(argv)

    if args.dump_closure:
        closure = walk_live_closure()
        edges = importers_of(ROOT, closure)
        for rel in sorted(closure):
            who = ", ".join(edges.get(rel) or ["(root)"])
            print(f"{rel}\t{who}")
        return 0

    if tuple(LIVE_PATH_ROOTS) != (
        "templates/studio/preview-toolbar.js",
        "templates/studio/homepage-v2/bootstrap.js",
    ):
        print("LIVE_PATH_ROOTS drifted from BLK-RCL-09 constants", file=sys.stderr)
        return 1

    violations = check_live_path()
    print(f"roots: {', '.join(LIVE_PATH_ROOTS)}")
    print(f"closure: {len(walk_live_closure())} files")
    if violations:
        print("REGRESSION: frontend live-path closure", file=sys.stderr)
        for row in violations:
            print(f"  {row}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
