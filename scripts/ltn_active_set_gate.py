#!/usr/bin/env python3
"""LTN H8 · active_set_gate: policy ↔ codegen ↔ schema ↔ golden (+ contract union).

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

# Contract extras that may win under template_contract (E4) — counted in active union.
_CONTRACT_EXTRA_PREFIXES = (
    "screen-mosaic-4-1l3p-rail",
    "screen-mosaic-5-2p3l-rail",
    "screen-mosaic-4-2l2p-weighted",
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


def _schema_all_pattern_ids() -> set[str]:
    schema = json.loads((ROOT / "schemas" / "trip.schema.json").read_text(encoding="utf-8"))
    enum = (
        ((schema.get("$defs") or {}).get("layoutScreen") or {})
        .get("properties", {})
        .get("patternId", {})
        .get("enum")
        or []
    )
    return {str(pid) for pid in enum}


def _schema_mosaic_ids() -> set[str]:
    keys = (
        "mosaic",
        "portrait-grid",
        "portrait-3",
        "portrait-4",
        "portrait-6",
        "portrait-9",
        "landscape-3",
        "landscape-4",
        "landscape-6",
        "landscape-9",
        "portrait-1-landscape-2",
        "portrait-2-landscape-2",
    )
    out: set[str] = set()
    for s in _schema_all_pattern_ids():
        if any(k in s for k in keys):
            out.add(s)
    return out


def _golden_pattern_ids() -> set[str]:
    root = ROOT / "tests" / "_golden"
    out: set[str] = set()
    if not root.is_dir():
        return out
    for path in root.rglob("expected.layout.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        chapters = data.get("chapters") if isinstance(data, dict) else None
        if not isinstance(chapters, list):
            # Some goldens are bare chapter lists / screen lists
            if isinstance(data, list):
                chapters = data
            else:
                continue
        for ch in chapters:
            if not isinstance(ch, dict):
                continue
            for sc in ch.get("screens") or []:
                if isinstance(sc, dict) and sc.get("patternId"):
                    out.add(str(sc["patternId"]))
            # snapshot form: patternId at chapter or nested
            if ch.get("patternId") and str(ch["patternId"]).startswith("screen-"):
                out.add(str(ch["patternId"]))
    return out


def _contract_extra_ids() -> tuple[set[str], set[str]]:
    """Return (active_contract, dogfood_contract).

    Active = ga / rollout>0 (counts toward ≤12 union).
    Dogfood = experimental with rollout 0 (reported, not hard-capped).
    """
    import yaml

    tdir = ROOT / "travelogue" / "layout_templates" / "templates"
    active: set[str] = set()
    dogfood: set[str] = set()
    for path in tdir.glob("screen-*.yaml"):
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        tid = str(raw.get("id") or path.stem)
        if raw.get("status") == "deprecated":
            continue
        is_extra = any(tid.startswith(p) or tid == p for p in _CONTRACT_EXTRA_PREFIXES) or (
            "rail" in tid
        )
        if not is_extra:
            continue
        # hero-70 is already in policy; skip double-count
        if tid in _policy_ids():
            continue
        roll = raw.get("rollout") or {}
        pct = int(roll.get("percent") or 0) if isinstance(roll, dict) else 0
        if raw.get("status") == "ga" or pct > 0:
            active.add(tid)
        else:
            dogfood.add(tid)
    return active, dogfood


def check() -> dict:
    policy = _policy_ids()
    codegen = _codegen_ids()
    schema = _schema_mosaic_ids()
    schema_all = _schema_all_pattern_ids()
    golden = _golden_pattern_ids()
    contract_active, contract_dogfood = _contract_extra_ids()
    active_union = set(policy) | set(contract_active)
    contract_all = contract_active | contract_dogfood

    policy_vs_codegen = {
        "only_in_policy": sorted(policy - codegen),
        "only_in_codegen": sorted(codegen - policy),
    }
    missing_in_schema = sorted(policy - schema)
    # Golden 对账：成品 golden 不得引用 schema 未知 patternId（覆盖率另计）。
    golden_unknown = sorted(
        pid for pid in golden if pid.startswith("screen-") and pid not in schema_all
    )
    contract_missing_in_schema = sorted(contract_all - schema_all)
    policy_missing_in_golden = sorted(policy - golden)

    ok = (
        not policy_vs_codegen["only_in_policy"]
        and not policy_vs_codegen["only_in_codegen"]
        and not missing_in_schema
        and not golden_unknown
        and not contract_missing_in_schema
        and len(active_union) <= 12
    )
    return {
        "ok": ok,
        "policyCount": len(policy),
        "codegenCount": len(codegen),
        "schemaMosaicCount": len(schema),
        "goldenPatternCount": len(golden),
        "contractActiveCount": len(contract_active),
        "contractDogfoodCount": len(contract_dogfood),
        "activeUnionCount": len(active_union),
        "activeUnion": sorted(active_union),
        "contractDogfood": sorted(contract_dogfood),
        "policyVsCodegen": policy_vs_codegen,
        "policyMissingInSchema": missing_in_schema,
        "policyMissingInGolden": policy_missing_in_golden,
        "goldenUnknownInSchema": golden_unknown,
        "contractMissingInSchema": contract_missing_in_schema,
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
            f"codegen={report['codegenCount']} union={report['activeUnionCount']} "
            f"dogfood={report['contractDogfoodCount']}"
        )
        pc = report["policyVsCodegen"]
        if pc["only_in_policy"]:
            print("  only_in_policy:", ", ".join(pc["only_in_policy"]))
        if pc["only_in_codegen"]:
            print("  only_in_codegen:", ", ".join(pc["only_in_codegen"]))
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
        print("  OK" if report["ok"] else "  FAIL")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
