#!/usr/bin/env python3
"""LTN H8/E1 · active_set_gate: policy ↔ codegen ↔ LEGACY ↔ schema ↔ golden (+ contract).

Also enforces rollout.percent=0 lifecycle (zeroSince + 4-week review).
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

from travelogue.layout_contract.active_set import inventory_report


def check() -> dict:
    return inventory_report(root=ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description="LTN H8/E1 active_set_gate")
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    args = parser.parse_args()
    report = check()
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(
            f"LTN active_set_gate: policy={report['policyCount']} "
            f"codegen={report['codegenCount']} legacy={report['legacyCount']} "
            f"union={report['activeUnionCount']} "
            f"dogfood={report['contractDogfoodCount']}"
        )
        pc = report["policyVsCodegen"]
        if pc["only_in_policy"]:
            print("  only_in_policy:", ", ".join(pc["only_in_policy"]))
        if pc["only_in_codegen"]:
            print("  only_in_codegen:", ", ".join(pc["only_in_codegen"]))
        lv = report["legacyVsPolicy"]
        if lv["only_in_legacy"]:
            print("  only_in_legacy:", ", ".join(lv["only_in_legacy"]))
        if lv["only_in_policy"]:
            print("  legacy_missing:", ", ".join(lv["only_in_policy"]))
        if report["policyMissingInSchema"]:
            print("  policyMissingInSchema:", ", ".join(report["policyMissingInSchema"]))
        if report["goldenUnknownInSchema"]:
            print("  goldenUnknownInSchema:", ", ".join(report["goldenUnknownInSchema"]))
        if report["contractMissingInSchema"]:
            print(
                "  contractMissingInSchema:",
                ", ".join(report["contractMissingInSchema"]),
            )
        if report["policyMissingInGolden"]:
            print(
                "  policyMissingInGolden (info):",
                ", ".join(report["policyMissingInGolden"]),
            )
        if report["activeUnionCount"] > 12:
            print("  activeUnion>12:", report["activeUnionCount"], report["activeUnion"])
        life = report.get("rolloutZeroLifecycle") or {}
        if life.get("missingZeroSince"):
            print(
                "  rolloutZero missing zeroSince:",
                ", ".join(life["missingZeroSince"]),
            )
        if life.get("overdue"):
            print(
                "  rolloutZero overdue (>4w):",
                ", ".join(r["id"] for r in life["overdue"]),
            )
        print("  OK" if report["ok"] else "  FAIL")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
