"""LTN E1 · active mosaic set inventory + six-write map.

Write points (converge toward fewer):
1. YAML ``status`` on template files
2. YAML ``rollout.percent`` (+ ``zeroSince`` lifecycle)
3. ``lte_policy.yaml`` ``mosaic_unified_groups``
4. Codegen ``_legacy_generated.py`` (``--sync-python``)
5. ``schemas/trip.schema.json`` ``patternId`` enum
6. Config ``layout.template_engine.overrides_disable``

H8 gate: policy ↔ codegen ↔ schema ↔ golden ∪ contract.
E1 step: LEGACY registry derived from codegen groups (no hand list);
``rollout.percent=0`` requires ``zeroSince`` and 4-week review.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

POLICY_GROUPS = (
    "MOSAIC_3_PATTERN_IDS",
    "MOSAIC_4_PATTERN_IDS",
    "MOSAIC_5_PATTERN_IDS",
    "MOSAIC_6_PATTERN_IDS",
    "MOSAIC_8_PATTERN_IDS",
    "MOSAIC_9_PATTERN_IDS",
)

CONTRACT_EXTRA_PREFIXES = (
    "screen-mosaic-4-1l3p-rail",
    "screen-mosaic-5-2p3l-rail",
    "screen-mosaic-4-2l2p-weighted",
)

# PRD R-E1 · rollout=0 older than this must be reviewed (promote / archive / bump).
ROLLOUT_ZERO_REVIEW_DAYS = 28

SIX_WRITE_SOURCES: tuple[dict[str, str], ...] = (
    {
        "id": "yaml_status",
        "path": "travelogue/layout_templates/templates/*.yaml#status",
        "role": "lifecycle (ga/experimental/deprecated)",
    },
    {
        "id": "yaml_rollout",
        "path": "travelogue/layout_templates/templates/*.yaml#rollout",
        "role": "percent + zeroSince review clock",
    },
    {
        "id": "lte_policy",
        "path": "travelogue/layout_templates/lte_policy.yaml#mosaic_unified_groups",
        "role": "MCS active groups SSOT",
    },
    {
        "id": "codegen",
        "path": "travelogue/layout_engine/mosaic/_legacy_generated.py",
        "role": "sync from policy (--sync-python)",
    },
    {
        "id": "schema_enum",
        "path": "schemas/trip.schema.json#layoutScreen.patternId",
        "role": "persistable patternId allowlist",
    },
    {
        "id": "config_override",
        "path": "config.yaml#layout.template_engine.overrides_disable",
        "role": "runtime kill-switch (fail-loud)",
    },
)


def policy_mosaic_ids(*, root: Path | None = None) -> set[str]:
    import yaml

    base = root or ROOT
    raw = yaml.safe_load(
        (base / "travelogue/layout_templates/lte_policy.yaml").read_text(encoding="utf-8")
    )
    groups = (raw or {}).get("mosaic_unified_groups") or {}
    out: set[str] = set()
    for name in POLICY_GROUPS:
        for pid in groups.get(name) or []:
            out.add(str(pid))
    return out


def codegen_mosaic_ids() -> set[str]:
    import importlib

    gen = importlib.import_module("travelogue.layout_engine.mosaic._legacy_generated")
    out: set[str] = set()
    for name in POLICY_GROUPS:
        out.update(getattr(gen, name))
    return out


def legacy_registry_ids() -> frozenset[str]:
    """E1 · LEGACY = codegen unified groups (no hand-maintained fourth list)."""
    import importlib

    constants = importlib.import_module("travelogue.layout_engine.mosaic.constants")
    return frozenset(constants.MOSAIC_UNIFIED_PATTERN_IDS)


def _string_enum_values(node: object) -> list[str]:
    """Collect ``enum`` members from a schema node, including anyOf/oneOf/allOf."""
    if not isinstance(node, dict):
        return []
    out: list[str] = []
    raw = node.get("enum")
    if isinstance(raw, list):
        out.extend(str(x) for x in raw)
    for key in ("anyOf", "oneOf", "allOf"):
        alts = node.get(key)
        if isinstance(alts, list):
            for alt in alts:
                out.extend(_string_enum_values(alt))
    return out


def schema_all_pattern_ids(*, root: Path | None = None) -> set[str]:
    base = root or ROOT
    schema = json.loads((base / "schemas/trip.schema.json").read_text(encoding="utf-8"))
    pid_schema = (
        ((schema.get("$defs") or {}).get("layoutScreen") or {})
        .get("properties", {})
        .get("patternId", {})
    )
    return set(_string_enum_values(pid_schema))


def schema_mosaic_ids(*, root: Path | None = None) -> set[str]:
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
    return {s for s in schema_all_pattern_ids(root=root) if any(k in s for k in keys)}


def golden_pattern_ids(*, root: Path | None = None) -> set[str]:
    base = root or ROOT
    groot = base / "tests/_golden"
    out: set[str] = set()
    if not groot.is_dir():
        return out
    for path in groot.rglob("expected.layout.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        chapters = data.get("chapters") if isinstance(data, dict) else None
        if not isinstance(chapters, list):
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
            if ch.get("patternId") and str(ch["patternId"]).startswith("screen-"):
                out.add(str(ch["patternId"]))
    return out


def contract_extra_ids(*, root: Path | None = None) -> tuple[set[str], set[str]]:
    import yaml

    base = root or ROOT
    tdir = base / "travelogue/layout_templates/templates"
    policy = policy_mosaic_ids(root=base)
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
        is_extra = any(tid.startswith(p) or tid == p for p in CONTRACT_EXTRA_PREFIXES) or (
            tid.endswith("-rail")
        )
        if not is_extra or tid in policy:
            continue
        roll = raw.get("rollout") if isinstance(raw.get("rollout"), dict) else {}
        pct = int(roll.get("percent") or 0)
        if raw.get("status") == "ga" or pct > 0:
            active.add(tid)
        else:
            dogfood.add(tid)
    return active, dogfood


def _parse_iso_date(raw: object) -> date | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def scan_rollout_zero_lifecycle(
    *,
    root: Path | None = None,
    today: date | None = None,
    review_days: int = ROLLOUT_ZERO_REVIEW_DAYS,
) -> dict[str, Any]:
    """List rollout=0 templates and flag missing/overdue zeroSince (E1 lifecycle)."""
    import yaml

    base = root or ROOT
    today = today or datetime.now().date()
    tdir = base / "travelogue/layout_templates/templates"
    missing_zero_since: list[str] = []
    overdue: list[dict[str, str]] = []
    ok_rows: list[dict[str, str]] = []
    for path in sorted(tdir.glob("screen-*.yaml")):
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        tid = str(raw.get("id") or path.stem)
        status = str(raw.get("status") or "")
        if status in ("deprecated", "disabled"):
            continue
        roll = raw.get("rollout") if isinstance(raw.get("rollout"), dict) else {}
        pct = int(roll.get("percent") or 0) if roll else 0
        # Missing rollout block ⇒ treat as not in zero-lifecycle (ga default path).
        if not roll or pct > 0:
            continue
        if roll.get("reviewExempt"):
            ok_rows.append({"id": tid, "zeroSince": str(roll.get("zeroSince") or ""), "exempt": "true"})
            continue
        zero = _parse_iso_date(roll.get("zeroSince"))
        if zero is None:
            missing_zero_since.append(tid)
            continue
        age = (today - zero).days
        row = {"id": tid, "zeroSince": zero.isoformat(), "ageDays": str(age)}
        if age > review_days:
            overdue.append(row)
        else:
            ok_rows.append(row)
    return {
        "reviewDays": review_days,
        "asOf": today.isoformat(),
        "missingZeroSince": missing_zero_since,
        "overdue": overdue,
        "withinWindow": ok_rows,
        "ok": not missing_zero_since and not overdue,
    }


def inventory_report(*, root: Path | None = None, today: date | None = None) -> dict[str, Any]:
    """Full E1/H8 inventory (used by scripts/ltn_active_set_gate.py)."""
    base = root or ROOT
    policy = policy_mosaic_ids(root=base)
    codegen = codegen_mosaic_ids()
    legacy = set(legacy_registry_ids())
    schema = schema_mosaic_ids(root=base)
    schema_all = schema_all_pattern_ids(root=base)
    golden = golden_pattern_ids(root=base)
    contract_active, contract_dogfood = contract_extra_ids(root=base)
    active_union = set(policy) | set(contract_active)
    contract_all = contract_active | contract_dogfood
    lifecycle = scan_rollout_zero_lifecycle(root=base, today=today)

    policy_vs_codegen = {
        "only_in_policy": sorted(policy - codegen),
        "only_in_codegen": sorted(codegen - policy),
    }
    legacy_vs_policy = {
        "only_in_legacy": sorted(legacy - policy),
        "only_in_policy": sorted(policy - legacy),
    }
    missing_in_schema = sorted(policy - schema)
    golden_unknown = sorted(
        pid for pid in golden if pid.startswith("screen-") and pid not in schema_all
    )
    contract_missing_in_schema = sorted(contract_all - schema_all)
    policy_missing_in_golden = sorted(policy - golden)
    # Audit-only: mosaic ids in schema that are neither policy nor contract extras
    # (legacy/deprecated render paths). Does not fail the gate.
    schema_mosaic_not_in_active = sorted(
        schema - policy - contract_active - contract_dogfood
    )

    ok = (
        not policy_vs_codegen["only_in_policy"]
        and not policy_vs_codegen["only_in_codegen"]
        and not legacy_vs_policy["only_in_legacy"]
        and not legacy_vs_policy["only_in_policy"]
        and not missing_in_schema
        and not golden_unknown
        and not contract_missing_in_schema
        and len(active_union) <= 12
        and bool(lifecycle["ok"])
    )
    return {
        "ok": ok,
        "sixWriteSources": list(SIX_WRITE_SOURCES),
        "policyCount": len(policy),
        "codegenCount": len(codegen),
        "legacyCount": len(legacy),
        "schemaMosaicCount": len(schema),
        "goldenPatternCount": len(golden),
        "contractActiveCount": len(contract_active),
        "contractDogfoodCount": len(contract_dogfood),
        "activeUnionCount": len(active_union),
        "activeUnion": sorted(active_union),
        "contractDogfood": sorted(contract_dogfood),
        "policyVsCodegen": policy_vs_codegen,
        "legacyVsPolicy": legacy_vs_policy,
        "policyMissingInSchema": missing_in_schema,
        "policyMissingInGolden": policy_missing_in_golden,
        "goldenUnknownInSchema": golden_unknown,
        "contractMissingInSchema": contract_missing_in_schema,
        "schemaMosaicNotInActive": schema_mosaic_not_in_active,
        "policyIds": sorted(policy),
        "rolloutZeroLifecycle": lifecycle,
    }


def days_until_rollout_review(zero_since: date, *, today: date | None = None) -> int:
    today = today or datetime.now().date()
    due = zero_since + timedelta(days=ROLLOUT_ZERO_REVIEW_DAYS)
    return (due - today).days
