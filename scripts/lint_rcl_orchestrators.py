#!/usr/bin/env python3
"""RCL W0 · three orchestrator AST-length ratchet + comment-budget allowlist.

W0 records current sizes and forbids growth. W1 switches on ``cap_after_w1``.
Comment budget only scans stage modules + ``trip_hot.py``; missing files skip.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "docs" / "acceptance-records" / "rcl-orchestrator-baseline.json"

# (baseline_key, repo-relative file, function name, owner)
ORCHESTRATORS: tuple[tuple[str, str, str, str], ...] = (
    (
        "travelogue.render.assemble:build_render_context",
        "travelogue/render/assemble.py",
        "build_render_context",
        "shared",
    ),
    (
        "travelogue.render.journal_chapters:build_journal_chapters",
        "travelogue/render/journal_chapters.py",
        "build_journal_chapters",
        "journal",
    ),
    (
        "travelogue.curation.curate:_stage_build_chapters_compose",
        "travelogue/curation/curate.py",
        "_stage_build_chapters_compose",
        "shared",
    ),
)

COMMENT_ALLOWLIST: tuple[str, ...] = (
    "travelogue/curation/compose_stages.py",
    "travelogue/render/assemble_cover.py",
    "travelogue/render/assemble_copy.py",
    "travelogue/render/journal_folio.py",
    "travelogue/render/journal_screens.py",
    "travelogue/types/trip_hot.py",
)
DOCSTRING_LINE_CAP = 15


def _module_function(tree: ast.AST, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def measure_orchestrators(root: Path = ROOT) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for key, rel, name, owner in ORCHESTRATORS:
        path = root / rel
        if not path.is_file():
            raise FileNotFoundError(rel)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        fn = _module_function(tree, name)
        if fn is None or fn.end_lineno is None:
            raise SystemExit(f"missing function {name} in {rel}")
        out[key] = {
            "file": rel,
            "name": name,
            "owner": owner,
            "lines": fn.end_lineno - fn.lineno + 1,
        }
    return out


def _module_docstring_lines(path: Path) -> int:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
    if not tree.body:
        return 0
    first = tree.body[0]
    if not isinstance(first, ast.Expr):
        return 0
    value = first.value
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return len(value.value.splitlines()) or 1
    return 0


def check_comment_budget(
    root: Path = ROOT,
    allowlist: tuple[str, ...] = COMMENT_ALLOWLIST,
) -> list[str]:
    """Return violations. Missing allowlisted files are skipped (W0)."""
    violations: list[str] = []
    for rel in allowlist:
        path = root / rel
        if not path.is_file():
            continue
        n = _module_docstring_lines(path)
        if n > DOCSTRING_LINE_CAP:
            violations.append(f"{rel}: module docstring {n} > {DOCSTRING_LINE_CAP}")
    return violations


def load_baseline(path: Path = BASELINE) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def compare_to_baseline(
    current: dict[str, dict[str, Any]],
    baseline: dict[str, Any],
    *,
    enforce_w1_caps: bool = False,
) -> list[str]:
    functions = baseline.get("functions") or {}
    violations: list[str] = []
    for key, meta in current.items():
        rec = functions.get(key)
        if not isinstance(rec, dict):
            violations.append(f"{key}: missing from baseline")
            continue
        if not rec.get("owner"):
            violations.append(f"{key}: baseline missing owner")
        ceiling = int(rec["lines"])
        n = int(meta["lines"])
        if n > ceiling:
            violations.append(f"{key}: {n} > baseline {ceiling}")
        if enforce_w1_caps:
            cap = int(rec["cap_after_w1"])
            if n > cap:
                violations.append(f"{key}: {n} > W1 cap {cap}")
    return violations


def write_baseline(
    current: dict[str, dict[str, Any]],
    path: Path = BASELINE,
    *,
    measured_at: str,
) -> None:
    functions: dict[str, dict[str, Any]] = {}
    caps = {row[0]: None for row in ORCHESTRATORS}
    old: dict[str, Any] = {}
    if path.is_file():
        old = json.loads(path.read_text(encoding="utf-8")).get("functions") or {}
    for key, meta in current.items():
        prev = old.get(key) if isinstance(old.get(key), dict) else {}
        cap = int(prev.get("cap_after_w1") or _default_cap(key))
        caps[key] = cap
        functions[key] = {
            "lines": meta["lines"],
            "cap_after_w1": cap,
            "owner": meta["owner"],
            "file": meta["file"],
        }
    report = {
        "version": 1,
        "measured_at": measured_at,
        "functions": functions,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _default_cap(key: str) -> int:
    return {
        "travelogue.render.assemble:build_render_context": 160,
        "travelogue.render.journal_chapters:build_journal_chapters": 140,
        "travelogue.curation.curate:_stage_build_chapters_compose": 160,
    }[key]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update-baseline", action="store_true")
    parser.add_argument(
        "--allow-growth",
        action="store_true",
        help="Permit baseline update even when a function grew",
    )
    parser.add_argument(
        "--enforce-w1-caps",
        action="store_true",
        help="Fail when a function exceeds cap_after_w1 (W1+)",
    )
    parser.add_argument("--measured-at", default="2026-08-29")
    args = parser.parse_args(argv)

    current = measure_orchestrators()
    if args.update_baseline:
        if BASELINE.is_file() and not args.allow_growth:
            old = json.loads(BASELINE.read_text(encoding="utf-8")).get("functions") or {}
            grew = []
            for key, meta in current.items():
                prev = old.get(key) if isinstance(old.get(key), dict) else {}
                if int(meta["lines"]) > int(prev.get("lines") or 0) and prev.get("lines") is not None:
                    grew.append(f"{key}: {prev.get('lines')} -> {meta['lines']}")
            if grew:
                print("refusing baseline update; growth without --allow-growth:", file=sys.stderr)
                for row in grew:
                    print(f"  {row}", file=sys.stderr)
                return 1
        write_baseline(current, measured_at=args.measured_at)
        print("baseline updated:", json.dumps({k: v["lines"] for k, v in current.items()}))
        return 0

    if not BASELINE.is_file():
        print("missing baseline; run with --update-baseline", file=sys.stderr)
        return 1

    baseline = load_baseline()
    violations = compare_to_baseline(
        current, baseline, enforce_w1_caps=args.enforce_w1_caps
    )
    violations.extend(check_comment_budget())
    for key, meta in current.items():
        rec = (baseline.get("functions") or {}).get(key) or {}
        print(f"{key}: {meta['lines']} lines (ceiling {rec.get('lines')}, owner {meta['owner']})")
    if violations:
        print("REGRESSION: RCL orchestrator / comment-budget gate", file=sys.stderr)
        for row in violations:
            print(f"  {row}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
