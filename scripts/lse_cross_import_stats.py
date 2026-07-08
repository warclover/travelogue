#!/usr/bin/env python3
"""Count layout_engine ↔ curation cross-import edges (ADR-015 · M-B0 baseline).

Uses AST to include top-level and function-scoped imports. Reports direct
module-to-module edges across the two package roots.
"""

from __future__ import annotations

import argparse
import ast
import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG_ROOT = ROOT / "travelogue"

PACKAGES = ("travelogue.curation", "travelogue.layout_engine")


@dataclass
class Edge:
    importer: str
    imported: str
    lines: list[int] = field(default_factory=list)

    @property
    def key(self) -> tuple[str, str]:
        return (self.importer, self.imported)


def module_from_path(path: Path) -> str:
    rel = path.relative_to(PKG_ROOT).with_suffix("")
    return "travelogue." + ".".join(rel.parts)


def package_of(module: str) -> str | None:
    for pkg in PACKAGES:
        if module == pkg or module.startswith(pkg + "."):
            return pkg
    return None


def target_module(node: ast.ImportFrom) -> str | None:
    if node.module is None:
        return None
    if node.level and node.level > 0:
        return None
    return node.module


def collect_imports(path: Path) -> list[tuple[str, int]]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    found: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            target = target_module(node)
            if target:
                found.append((target, node.lineno))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                found.append((alias.name, node.lineno))
    return [(target, line) for target, line in found if target.startswith("travelogue.")]


def scan_edges() -> dict[tuple[str, str], Edge]:
    edges: dict[tuple[str, str], Edge] = {}
    for py in PKG_ROOT.rglob("*.py"):
        if py.name == "__init__.py" and py.parent.name in {"curation", "layout_engine"}:
            continue
        importer = module_from_path(py)
        src_pkg = package_of(importer)
        if src_pkg not in PACKAGES:
            continue
        for imported, line in collect_imports(py):
            dst_pkg = package_of(imported)
            if dst_pkg is None or dst_pkg == src_pkg:
                continue
            key = (importer, imported)
            if key not in edges:
                edges[key] = Edge(importer=importer, imported=imported)
            edges[key].lines.append(line)
    return edges


def summarize(edges: dict[tuple[str, str], Edge]) -> dict[str, object]:
    le_to_cur = [e for e in edges.values() if e.importer.startswith("travelogue.layout_engine")]
    cur_to_le = [e for e in edges.values() if e.importer.startswith("travelogue.curation")]

    by_importer: dict[str, int] = defaultdict(int)
    by_imported: dict[str, int] = defaultdict(int)
    for edge in edges.values():
        by_importer[edge.importer] += 1
        by_imported[edge.imported] += 1

    return {
        "packages": list(PACKAGES),
        "totalCrossEdges": len(edges),
        "layoutEngineToCuration": len(le_to_cur),
        "curationToLayoutEngine": len(cur_to_le),
        "targetAfterMigration": {
            "maxCrossEdges": max(1, round(len(edges) * 0.2)),
            "reductionPercent": 80,
            "note": "M-B4b proceeds only if post-kernel (M-B4a) cross edges ≤ maxCrossEdges",
        },
        "topImporters": sorted(
            ((mod, count) for mod, count in by_importer.items()),
            key=lambda item: (-item[1], item[0]),
        )[:15],
        "topImported": sorted(
            ((mod, count) for mod, count in by_imported.items()),
            key=lambda item: (-item[1], item[0]),
        )[:15],
        "edges": [
            {
                "importer": edge.importer,
                "imported": edge.imported,
                "lines": sorted(set(edge.lines)),
            }
            for edge in sorted(edges.values(), key=lambda e: (e.importer, e.imported))
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LSE ↔ curation cross-import statistics")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable report")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "docs" / "acceptance-records" / "lse-cross-import-baseline.json",
        help="Write JSON report path",
    )
    args = parser.parse_args(argv)

    edges = scan_edges()
    report = summarize(edges)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"layout_engine → curation: {report['layoutEngineToCuration']}")
        print(f"curation → layout_engine: {report['curationToLayoutEngine']}")
        print(f"total cross edges: {report['totalCrossEdges']}")
        print(f"M-B4b target (≤20% of baseline): {report['targetAfterMigration']['maxCrossEdges']}")
        print(f"JSON: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
