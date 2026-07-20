#!/usr/bin/env python3
"""LTN H8 · active_set_gate: policy ↔ codegen ↔ schema mosaic ID parity.

Exit 1 on drift. Intended for PR CI (test-pr).

Usage:
  python scripts/ltn_active_set_gate.py
  python scripts/ltn_active_set_gate.py --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_POLICY_GROUPS = (
    "MOSAIC_3_PATTERN_IDS",
    "MOSAIC_4_PATTERN_IDS",
    "MOSAIC_5_PATTERN_IDS",
    "MOSAIC_6_PATTERN_IDS",
    "MOSAIC_8_PATTERN_IDS",
    "MOSAIC_9_PATTERN_IDS",
)


def _policy_ids() -> set[str]:
    import yaml

    raw = yaml.safe_load(
        (ROOT / "travelogue" / "layout_templates" / "lte_policy.yaml").read_text(
            encoding="utf-8"
        )
    )
    groups = (raw or {}).get("mosaic_unified_groups") or {}
    out: set[str] = set()
    for name in _POLICY_GROUPS:
        for pid in groups.get(name) or []:
            out.add(str(pid))
    return out


def _codegen_ids() -> set[str]:
    from travelogue.layout_engine.mosaic import _legacy_generated as gen

    out: set[str] = set()
    for name in _POLICY_GROUPS:
        out.update(getattr(gen, name))
    return out


def _schema_mosaic_ids() -> set[str]:
    schema = json.loads((ROOT / "schemas" / "trip.schema.json").read_text(encoding="utf-8"))
    enum = (
        ((schema.get("$defs") or {}).get("layoutScreen") or {})
        .get("properties", {})
        .get("patternId", {})
        .get("enum")
        or []
    )
    # Mosaic / dense collage family only (name heuristic + known grid ids).
    keys = ("mosaic", "portrait-grid", "portrait-3", "portrait-4", "portrait-6",
            "portrait-9", "landscape-3", "landscape-4", "landscape-6", "landscape-9",
            "portrait-1-landscape-2", "portrait-2-landscape-2")
    out: set[str] = set()
    for pid in enum:
        s = str(pid)
        if any(k in s for k in keys):
            out.add(s)
    return out


def check() -> dict:
    policy = _policy_ids()
    codegen = _codegen_ids()
    schema = _schema_mosaic_ids()

    policy_vs_codegen = {
        "only_in_policy": sorted(policy - codegen),
        "only_in_codegen": sorted(codegen - policy),
    }
    # Policy IDs must appear in schema enum (schema may be a superset).
    missing_in_schema = sorted(policy - schema)

    ok = (
        not policy_vs_codegen["only_in_policy"]
        and not policy_vs_codegen["only_in_codegen"]
        and not missing_in_schema
    )
    return {
        "ok": ok,
        "policyCount": len(policy),
        "codegenCount": len(codegen),
        "schemaMosaicCount": len(schema),
        "policyVsCodegen": policy_vs_codegen,
        "policyMissingInSchema": missing_in_schema,
        "policyIds": sorted(policy),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="LTN H8 active_set_gate")
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    args = parser.parse_args()
    report = check()
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(
            f"LTN active_set_gate: policy={report['policyCount']} "
            f"codegen={report['codegenCount']} schema∩mosaic≈{report['schemaMosaicCount']}"
        )
        pc = report["policyVsCodegen"]
        if pc["only_in_policy"]:
            print("  only_in_policy:", ", ".join(pc["only_in_policy"]))
        if pc["only_in_codegen"]:
            print("  only_in_codegen:", ", ".join(pc["only_in_codegen"]))
        if report["policyMissingInSchema"]:
            print("  policyMissingInSchema:", ", ".join(report["policyMissingInSchema"]))
        print("  OK" if report["ok"] else "  FAIL")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
