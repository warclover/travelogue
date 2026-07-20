#!/usr/bin/env python3
"""LTN H7 · geometry audit: eligibility.targetDisplayAspect vs rendered cell AR.

Fails (exit 1) when an active (non-deprecated) template with main eligibility
declares targetDisplayAspect farther than arLadderTol (default 0.08) from the
computed slot cell aspect.

Usage:
  python scripts/ltn_geometry_audit.py
  python scripts/ltn_geometry_audit.py --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_TOL = 0.08


def audit() -> dict:
    from travelogue.layout_templates.geometry import slot_aspect_table
    from travelogue.layout_templates.registry import get_engine

    engine = get_engine()
    rows: list[dict] = []
    failures: list[dict] = []
    for tid in sorted(engine._templates):
        tpl = engine._templates[tid]
        if tpl.status in ("deprecated", "disabled"):
            continue
        elig = (tpl.constraints or {}).get("eligibility") or {}
        target = elig.get("targetDisplayAspect")
        if target is None:
            continue
        try:
            target_f = float(target)
        except (TypeError, ValueError):
            failures.append({"id": tid, "error": "non-numeric targetDisplayAspect"})
            continue
        tol = float(elig.get("arLadderTol") or DEFAULT_TOL)
        table = {r.index: r.display_aspect for r in slot_aspect_table(tpl)}
        slot_idx = int(elig.get("slotIndex") or 0)
        cell = table.get(slot_idx)
        if cell is None:
            failures.append({"id": tid, "error": f"missing slot {slot_idx}"})
            continue
        delta = abs(target_f - cell)
        row = {
            "id": tid,
            "status": tpl.status,
            "slotIndex": slot_idx,
            "targetDisplayAspect": round(target_f, 4),
            "cellAspect": round(cell, 4),
            "delta": round(delta, 4),
            "tol": tol,
            "ok": delta <= tol,
        }
        rows.append(row)
        if not row["ok"]:
            failures.append(row)
    return {
        "ok": not failures,
        "checked": len(rows),
        "failures": failures,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="LTN H7 geometry audit")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = audit()
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"LTN geometry audit: checked={report['checked']} ok={report['ok']}")
        for f in report["failures"]:
            print(f"  FAIL {f}")
        if report["ok"]:
            for r in report["rows"]:
                print(
                    f"  ok {r['id']}: target={r['targetDisplayAspect']} "
                    f"cell={r['cellAspect']} Δ={r['delta']}"
                )
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
