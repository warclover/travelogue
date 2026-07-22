#!/usr/bin/env python3
"""CSC W3a · structured dual-path / shim debt ratchet (not raw ``legacy`` rg).

Detects debt modules by:
  - filename markers (legacy*, *_legacy*)
  - module docstring containing ``shim →`` / ``Shim re-export``

Baseline edges may only shrink (or stay). Growth requires ``--allow-growth``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "travelogue"
BASELINE = ROOT / "docs" / "acceptance-records" / "csc-w3-debt-table-baseline.json"
TABLE = ROOT / "docs" / "acceptance-records" / "csc-w3-debt-table.md"

_SHIM_DOC = re.compile(r"(shim\s*→|Shim re-export)", re.I)
_LEGACY_NAME = re.compile(r"(^legacy)|(_legacy)|(legacy_)", re.I)


def _first_doc_chunk(text: str) -> str:
    text = text.lstrip()
    if text.startswith('"""') or text.startswith("'''"):
        q = text[:3]
        end = text.find(q, 3)
        if end != -1:
            return text[: end + 3]
    return text[:400]


def classify(path: Path, text: str) -> str | None:
    name = path.name
    if _LEGACY_NAME.search(name):
        return "legacy_filename"
    if _SHIM_DOC.search(_first_doc_chunk(text)):
        return "shim_docstring"
    return None


def scan() -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for path in sorted(PKG.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        kind = classify(path, text)
        if not kind:
            continue
        hits.append(
            {
                "file": path.relative_to(ROOT).as_posix(),
                "kind": kind,
            }
        )
    return hits


def _write_table_md(hits: list[dict[str, str]]) -> None:
    lines = [
        "# CSC W3 · 结构化债务表（shim / legacy 双路径）",
        "",
        "| 属性 | 内容 |",
        "|------|------|",
        "| **计量** | 文件名 legacy* / docstring `shim →`（非全文 rg） |",
        f"| **条目数** | **{len(hits)}** |",
        "| **棘轮** | `python scripts/lint_csc_debt_table.py`（只降不升） |",
        "",
        "| 文件 | 类型 |",
        "|------|------|",
    ]
    for h in hits:
        lines.append(f"| `{h['file']}` | {h['kind']} |")
    lines.append("")
    lines.append(
        "> 删除无调用 shim 或退役 legacy 模块后重跑 `--update-baseline`；"
        "新增债务须 `--allow-growth` 并附理由。"
    )
    lines.append("")
    TABLE.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update-baseline", action="store_true")
    parser.add_argument("--allow-growth", action="store_true")
    args = parser.parse_args()

    hits = scan()
    edges = sorted(h["file"] for h in hits)
    report = {"count": len(edges), "edges": edges, "details": hits}

    if args.update_baseline:
        if BASELINE.is_file() and not args.allow_growth:
            old = set(json.loads(BASELINE.read_text(encoding="utf-8")).get("edges") or [])
            added = sorted(set(edges) - old)
            if added:
                print("refusing baseline update; new debt modules:", file=sys.stderr)
                for a in added:
                    print(f"  + {a}", file=sys.stderr)
                return 1
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        _write_table_md(hits)
        print(f"baseline updated: {len(edges)} debt modules")
        return 0

    if not BASELINE.is_file():
        print("missing baseline; run with --update-baseline", file=sys.stderr)
        return 1

    old_edges = set(json.loads(BASELINE.read_text(encoding="utf-8")).get("edges") or [])
    new_edges = set(edges)
    added = sorted(new_edges - old_edges)
    removed = sorted(old_edges - new_edges)
    print(f"CSC debt modules: {len(new_edges)} (baseline {len(old_edges)})")
    if removed:
        print(f"improved: removed {len(removed)}")
    if added:
        print("REGRESSION: new shim/legacy debt modules:", file=sys.stderr)
        for a in added:
            print(f"  + {a}", file=sys.stderr)
        return 1
    # Keep human table in sync when count unchanged but details refreshed
    if not TABLE.is_file() or args.update_baseline:
        _write_table_md(hits)
    return 0


if __name__ == "__main__":
    sys.exit(main())
