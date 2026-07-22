#!/usr/bin/env python3
"""CSC W2a · ban *new* deep imports into layout_engine planner/mosaic internals.

Allowed for curation/services/web:
  - travelogue.layout_engine / .api / .adapter
  - LSE admin/support modules (capabilities, registry, rollout, …)

Forbidden unless grandfathered in baseline JSON:
  - travelogue.layout_engine.planner.*
  - travelogue.layout_engine.mosaic.*
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = (
    ROOT / "travelogue" / "curation",
    ROOT / "travelogue" / "services",
    ROOT / "travelogue" / "web",
)
BASELINE = ROOT / "docs" / "acceptance-records" / "csc-w2a-facade-deep-import-baseline.json"

ALLOWED_EXACT = frozenset(
    {
        "travelogue.layout_engine",
        "travelogue.layout_engine.api",
        "travelogue.layout_engine.adapter",
        "travelogue.layout_engine.capabilities",
        "travelogue.layout_engine.decision_log",
        "travelogue.layout_engine.governance",
        "travelogue.layout_engine.pattern_policy",
        "travelogue.layout_engine.policy",
        "travelogue.layout_engine.query",
        "travelogue.layout_engine.registry",
        "travelogue.layout_engine.rollout",
        "travelogue.layout_engine.runtime_store",
        "travelogue.layout_engine.sandbox",
        "travelogue.layout_engine.shadow",
        "travelogue.layout_engine.studio_feedback",
    }
)

FORBIDDEN_PREFIXES = (
    "travelogue.layout_engine.planner",
    "travelogue.layout_engine.mosaic",
)


def _is_forbidden(mod: str) -> bool:
    return any(mod == p or mod.startswith(p + ".") for p in FORBIDDEN_PREFIXES)


def _is_allowed(mod: str) -> bool:
    if mod in ALLOWED_EXACT:
        return True
    if not mod.startswith("travelogue.layout_engine"):
        return True
    # Other layout_engine submodules (beam, editorial, …): treat as deep for now
    # only if under planner/mosaic; else allow (admin/algo helpers).
    if _is_forbidden(mod):
        return False
    return True


def scan() -> list[dict[str, str | int]]:
    hits: list[dict[str, str | int]] = []
    for root in SCAN_ROOTS:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError:
                continue
            rel = path.relative_to(ROOT).as_posix()
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    mod = node.module
                    if mod.startswith("travelogue.layout_engine") and not _is_allowed(mod):
                        hits.append(
                            {
                                "file": rel,
                                "line": int(node.lineno),
                                "module": mod,
                            }
                        )
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        mod = alias.name
                        if mod.startswith("travelogue.layout_engine") and not _is_allowed(mod):
                            hits.append(
                                {
                                    "file": rel,
                                    "line": int(node.lineno),
                                    "module": mod,
                                }
                            )
    hits.sort(key=lambda h: (str(h["file"]), int(h["line"]), str(h["module"])))
    return hits


def _signature(hits: list[dict[str, str | int]]) -> list[str]:
    """Stable identity without line numbers (refactors that only move lines OK)."""
    return sorted({f"{h['file']}::{h['module']}" for h in hits})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Write/refresh baseline when deep-import set did not grow",
    )
    args = parser.parse_args()

    hits = scan()
    sig = _signature(hits)
    report = {"count": len(sig), "edges": sig, "details": hits}

    if args.update_baseline:
        if BASELINE.is_file():
            old = json.loads(BASELINE.read_text(encoding="utf-8"))
            old_sig = set(old.get("edges") or [])
            new_sig = set(sig)
            added = sorted(new_sig - old_sig)
            if added:
                print("refusing baseline update; new deep imports:", file=sys.stderr)
                for a in added:
                    print(f"  + {a}", file=sys.stderr)
                return 1
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"baseline updated: {len(sig)} deep-import edges")
        return 0

    if not BASELINE.is_file():
        print("missing baseline; run with --update-baseline", file=sys.stderr)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    old = json.loads(BASELINE.read_text(encoding="utf-8"))
    old_sig = set(old.get("edges") or [])
    new_sig = set(sig)
    added = sorted(new_sig - old_sig)
    removed = sorted(old_sig - new_sig)
    print(f"layout_engine facade deep imports: {len(sig)} (baseline {len(old_sig)})")
    if removed:
        print(f"improved: removed {len(removed)} edge(s)")
    if added:
        print("REGRESSION: new deep imports into planner/mosaic:", file=sys.stderr)
        for a in added:
            print(f"  + {a}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
