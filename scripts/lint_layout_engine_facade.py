#!/usr/bin/env python3
"""CSC W2a / QFX D-QFX-14b · ban *new* deep imports into layout_engine planner/mosaic.

Scan root: ``travelogue/**`` excluding ``layout_engine/**``.
Grandfather edges require owner + expiry in baseline JSON.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOT = ROOT / "travelogue"
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
    if _is_forbidden(mod):
        return False
    return True


def scan() -> list[dict[str, str | int]]:
    hits: list[dict[str, str | int]] = []
    if not SCAN_ROOT.is_dir():
        return hits
    for path in sorted(SCAN_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts or "layout_engine" in path.parts:
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
                    hits.append({"file": rel, "line": int(node.lineno), "module": mod})
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name
                    if mod.startswith("travelogue.layout_engine") and not _is_allowed(mod):
                        hits.append(
                            {"file": rel, "line": int(node.lineno), "module": mod}
                        )
    hits.sort(key=lambda h: (str(h["file"]), int(h["line"]), str(h["module"])))
    return hits


def _signature(hits: list[dict[str, str | int]]) -> list[str]:
    return sorted({f"{h['file']}::{h['module']}" for h in hits})


def _parse_expiry(raw: object) -> date | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def _grandfather_map(old: dict) -> dict[str, dict]:
    """Normalize baseline edges to {sig: {owner, expiry}}."""
    out: dict[str, dict] = {}
    edges = old.get("edges") or []
    meta = old.get("grandfather") or {}
    for item in edges:
        if isinstance(item, str):
            sig = item
            info = meta.get(sig) or {}
        elif isinstance(item, dict):
            sig = str(item.get("edge") or item.get("sig") or "")
            info = item
        else:
            continue
        if not sig:
            continue
        out[sig] = {
            "owner": str(info.get("owner") or "").strip(),
            "expiry": str(info.get("expiry") or "").strip(),
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Write/refresh baseline when deep-import set did not grow",
    )
    parser.add_argument(
        "--allow-growth",
        action="store_true",
        help="Permit baseline update when new edges appear (requires grandfather meta)",
    )
    args = parser.parse_args()

    hits = scan()
    sig = _signature(hits)
    report = {"count": len(sig), "edges": sig, "details": hits}

    if args.update_baseline:
        grandfather: dict[str, dict] = {}
        if BASELINE.is_file():
            old = json.loads(BASELINE.read_text(encoding="utf-8"))
            old_map = _grandfather_map(old)
            old_sig = set(old_map) or set(old.get("edges") or [])
            new_sig = set(sig)
            added = sorted(new_sig - old_sig)
            if added and not args.allow_growth:
                print("refusing baseline update; new deep imports:", file=sys.stderr)
                for a in added:
                    print(f"  + {a}", file=sys.stderr)
                return 1
            for edge in sig:
                prev = old_map.get(edge) or {}
                grandfather[edge] = {
                    "owner": prev.get("owner") or "architecture",
                    "expiry": prev.get("expiry") or "2026-12-31",
                }
        else:
            for edge in sig:
                grandfather[edge] = {
                    "owner": "architecture",
                    "expiry": "2026-12-31",
                }
        payload = {
            "count": len(sig),
            "edges": sig,
            "grandfather": grandfather,
            "details": hits,
        }
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"baseline updated: {len(sig)} deep-import edges")
        return 0

    if not BASELINE.is_file():
        print("missing baseline; run with --update-baseline", file=sys.stderr)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    old = json.loads(BASELINE.read_text(encoding="utf-8"))
    gf = _grandfather_map(old)
    old_sig = set(gf) or set(old.get("edges") or [])
    new_sig = set(sig)
    added = sorted(new_sig - old_sig)
    removed = sorted(old_sig - new_sig)
    print(f"layout_engine facade deep imports: {len(sig)} (baseline {len(old_sig)})")
    if removed:
        print(f"improved: removed {len(removed)} edge(s)")
    today = date.today()
    expired = []
    missing_meta = []
    for edge in sorted(new_sig & old_sig):
        info = gf.get(edge) or {}
        if not info.get("owner") or not info.get("expiry"):
            missing_meta.append(edge)
            continue
        exp = _parse_expiry(info.get("expiry"))
        if exp is None or exp < today:
            expired.append(edge)
    if missing_meta:
        print("REGRESSION: grandfather missing owner/expiry:", file=sys.stderr)
        for a in missing_meta:
            print(f"  ! {a}", file=sys.stderr)
        return 1
    if expired:
        print("REGRESSION: grandfather expiry passed:", file=sys.stderr)
        for a in expired:
            print(f"  ! {a} expiry={gf[a].get('expiry')}", file=sys.stderr)
        return 1
    if added:
        print("REGRESSION: new deep imports into planner/mosaic:", file=sys.stderr)
        for a in added:
            print(f"  + {a}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
