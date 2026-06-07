#!/usr/bin/env python3
"""Phase 16 dogfood template metrics (AC-P16-08/15)."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from travelogue.config import get_config
from travelogue.curation.layout_metrics import pattern_diversity, pattern_diversity_p50
from travelogue.curation.mosaic.lte_adapter import mosaic_registry, read_templates_from_lte
from travelogue.curation.mosaic.metrics import (
    mcs_unified_exposure_rate,
    mixed_layout_exposure_rate,
    mosaic5_exposure_rate,
)
from travelogue.layout_templates.registry import LayoutTemplateEngine, reset_engine_cache_for_tests

DEFAULT_BASELINE = Path("docs/acceptance-records/phase16-template-eval-baseline.json")
DEFAULT_DOGFOOD_DIR = Path("tests/fixtures/phase16-dogfood")
LTE_POLICY = Path("travelogue/layout_templates/lte_policy.yaml")


def _load_trip_chapters(trip_json: Path) -> list[dict] | None:
    try:
        data = json.loads(trip_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    chapters = data.get("chapters") or []
    return chapters if chapters else None


def _pattern_exposure_from_trips(trips_root: Path) -> dict[str, int]:
    counts: Counter[str] = Counter()
    if not trips_root.is_dir():
        return {}
    for trip_json in trips_root.glob("*/trip.json"):
        chapters = _load_trip_chapters(trip_json)
        if not chapters:
            continue
        for ch in chapters:
            for screen in ch.get("screens") or []:
                pid = str(screen.get("patternId") or "").strip()
                if pid:
                    counts[pid] += 1
    return dict(sorted(counts.items()))


def evaluate_dogfood_trips(trips_root: Path) -> dict[str, Any]:
    per_trip: list[dict[str, Any]] = []
    p50_values: list[float] = []
    mosaic5_rates: list[float] = []
    unified_rates: list[float] = []
    mixed_rates: list[float] = []
    diversity_values: list[float] = []

    if trips_root.is_dir():
        for trip_json in sorted(trips_root.glob("*/trip.json")):
            chapters = _load_trip_chapters(trip_json)
            if not chapters:
                continue
            p50 = pattern_diversity_p50(chapters)
            div = pattern_diversity(chapters)
            m5 = mosaic5_exposure_rate(chapters)
            unified = mcs_unified_exposure_rate(chapters)
            mixed = mixed_layout_exposure_rate(chapters)
            per_trip.append(
                {
                    "tripId": trip_json.parent.name,
                    "layout.chapter.pattern_diversity_p50": round(p50, 4),
                    "layout.chapter.pattern_diversity": round(div, 4),
                    "layout.mosaic5.exposure_rate": m5,
                    "layout.mosaic_v2.unified_exposure_rate": unified,
                    "layout.mosaic.mixed_layout_exposure_rate": mixed,
                }
            )
            p50_values.append(p50)
            mosaic5_rates.append(m5)
            unified_rates.append(unified)
            mixed_rates.append(mixed)
            diversity_values.append(div)

    def _median(vals: list[float]) -> float | None:
        return round(statistics.median(vals), 4) if vals else None

    def _mean(vals: list[float]) -> float | None:
        return round(statistics.mean(vals), 4) if vals else None

    return {
        "tripCount": len(per_trip),
        "perTrip": per_trip,
        "aggregate": {
            "layout.chapter.pattern_diversity_p50": _median(p50_values),
            "layout.chapter.pattern_diversity_mean": _mean(diversity_values),
            "layout.mosaic5.exposure_rate_mean": _mean(mosaic5_rates),
            "layout.mosaic_v2.unified_exposure_rate_mean": _mean(unified_rates),
            "layout.mosaic.mixed_layout_exposure_rate_mean": _mean(mixed_rates),
        },
    }


def _load_exposure_control() -> dict[str, float]:
    defaults = {"damping": 0.5, "min_weight": 0.5, "max_weight": 2.0}
    if not LTE_POLICY.is_file():
        return defaults
    try:
        import yaml

        doc = yaml.safe_load(LTE_POLICY.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return defaults
    ctrl = doc.get("exposure_control") or {}
    out = dict(defaults)
    for key in defaults:
        val = ctrl.get(key)
        if val is not None:
            out[key] = float(val)
    return out


def compute_exposure_debt_proposals(
    exposure_share: dict[str, float],
    engine: LayoutTemplateEngine,
    *,
    damping: float = 0.5,
    min_weight: float = 0.5,
    max_weight: float = 2.0,
) -> list[dict[str, Any]]:
    """§9.4 proportional controller — proposals only, not auto-applied."""
    active = engine.list_active()
    if not active:
        return []
    target = 1.0 / len(active)
    proposals: list[dict[str, Any]] = []
    for tpl in sorted(active, key=lambda t: t.id):
        actual = float(exposure_share.get(tpl.id, 0.0))
        debt = target - actual
        current = float((tpl.scoring or {}).get("base_weight") or 1.0)
        if target <= 0:
            continue
        factor = 1.0 + damping * (debt / target)
        suggested = max(min_weight, min(max_weight, round(current * factor, 4)))
        if abs(suggested - current) < 0.01:
            continue
        proposals.append(
            {
                "templateId": tpl.id,
                "templateVersion": tpl.version,
                "currentBaseWeight": current,
                "suggestedBaseWeight": suggested,
                "targetExposureShare": round(target, 4),
                "actualExposureShare": round(actual, 4),
                "exposureDebt": round(debt, 4),
                "approvalRequired": True,
            }
        )
    return proposals


def evaluate_registry(*, trip_id: str | None = None, trips_dir: Path | None = None) -> dict:
    cfg = get_config()
    lte_on = read_templates_from_lte(cfg)
    reg = mosaic_registry(cfg)
    engine = LayoutTemplateEngine.load(rebuild_cache=True)

    active = engine.list_active()
    by_size: dict[int, list[str]] = {}
    for t in active:
        for n in range(t.photo_count_min, t.photo_count_max + 1):
            by_size.setdefault(n, []).append(t.id)

    root = trips_dir or get_config().trips_dir
    exposure = _pattern_exposure_from_trips(root)
    total_screens = sum(exposure.values())
    exposure_share = {
        pid: round(n / total_screens, 4) if total_screens else 0.0
        for pid, n in exposure.items()
    }

    dogfood = evaluate_dogfood_trips(root)
    ctrl = _load_exposure_control()
    proposals = compute_exposure_debt_proposals(
        exposure_share,
        engine,
        damping=ctrl["damping"],
        min_weight=ctrl["min_weight"],
        max_weight=ctrl["max_weight"],
    )

    return {
        "tripId": trip_id,
        "readTemplatesFromLte": lte_on,
        "registrySize": len(reg),
        "activeTemplateCount": len(active),
        "activeByPhotoCount": {str(k): sorted(v) for k, v in sorted(by_size.items())},
        "flagshipPresent": "screen-mosaic-5-2p3l-equal" in reg,
        "heroPresent": "screen-mosaic-5-hero-3-2-plus-4" in reg,
        "deprecatedExcluded": "screen-mosaic-5-3portrait-2land-balanced" not in reg,
        "templateExposureCount": exposure,
        "templateExposureShare": exposure_share,
        "screenSampleTotal": total_screens,
        "dogfood": dogfood,
        "exposureDebtProposals": proposals,
        "templateRegistryVersion": engine._content_hash,
    }


def submit_exposure_proposals(
    report: dict[str, Any],
    *,
    operator: str = "phase16-eval",
    reason: str = "exposure debt rebalance (§9.4)",
) -> dict[str, Any]:
    """Propose runtime base_weight patch from evaluate_registry exposureDebtProposals."""
    from travelogue.templating.config_governance import propose_layout_weight_changes

    proposals = report.get("exposureDebtProposals") or []
    return propose_layout_weight_changes(
        proposals,
        operator=operator,
        reason=reason,
        template_registry_version=str(report.get("templateRegistryVersion") or "").strip() or None,
    )


def approve_exposure_proposal(change_id: str, *, approver: str) -> dict[str, Any]:
    """Single approval step for a pending exposure rebalance (needs two distinct approvers)."""
    from travelogue.templating.config_governance import approve_router_change

    return approve_router_change(change_id, approver=approver)


def compare_baseline(report: dict, baseline_path: Path) -> dict[str, Any]:
    if not baseline_path.is_file():
        return {"ok": True, "skipped": True, "reason": "baseline missing"}
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    agg = (report.get("dogfood") or {}).get("aggregate") or {}
    base_agg = (baseline.get("dogfood") or {}).get("aggregate") or {}
    warnings: list[str] = []
    for key in (
        "layout.chapter.pattern_diversity_p50",
        "layout.mosaic5.exposure_rate_mean",
        "layout.mosaic.mixed_layout_exposure_rate_mean",
    ):
        cur = agg.get(key)
        ref = base_agg.get(key)
        if cur is None or ref is None:
            continue
        if abs(float(cur) - float(ref)) > 0.15:
            warnings.append(f"{key}: {cur} vs baseline {ref}")
    return {"ok": not warnings, "warnings": warnings, "baselinePath": str(baseline_path)}


def compare_ac15_thresholds(report: dict) -> dict[str, Any]:
    """AC-P16-15 hard gates on North Star metrics (dogfood aggregate)."""
    dogfood = report.get("dogfood") or {}
    agg = dogfood.get("aggregate") or {}
    failures: list[str] = []
    trip_count = int(dogfood.get("tripCount") or 0)
    if trip_count < 3:
        failures.append(f"dogfood tripCount {trip_count} < 3")
    p50 = agg.get("layout.chapter.pattern_diversity_p50")
    if p50 is None:
        failures.append("pattern_diversity_p50 missing")
    elif float(p50) < 2.0:
        failures.append(f"pattern_diversity_p50 {p50} < 2.0")
    m5 = agg.get("layout.mosaic5.exposure_rate_mean")
    if m5 is None:
        failures.append("mosaic5 exposure missing")
    elif float(m5) <= 0.0:
        failures.append(f"mosaic5 exposure {m5} <= 0")
    unified = agg.get("layout.mosaic_v2.unified_exposure_rate_mean")
    if unified is None:
        failures.append("unified mosaic exposure missing")
    elif float(unified) < 0.3:
        failures.append(f"unified mosaic exposure {unified} < 0.3")
    mixed = agg.get("layout.mosaic.mixed_layout_exposure_rate_mean")
    if mixed is not None and float(mixed) < 0.0:
        failures.append(f"mixed_layout exposure {mixed} < 0")
    return {"ok": not failures, "failures": failures}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 16 LTE template eval report")
    parser.add_argument("--trip", dest="trip_id", default=None)
    parser.add_argument("--trips-dir", type=Path, default=None, help="Trip root for exposure + dogfood (CI: phase16-dogfood fixtures)")
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--write-baseline", action="store_true")
    parser.add_argument(
        "--propose",
        action="store_true",
        help="Submit exposureDebtProposals for dual-approval (§9.4); prints pending change id",
    )
    parser.add_argument("--operator", default="phase16-eval", help="Operator id for --propose")
    parser.add_argument(
        "--approve",
        metavar="CHANGE_ID",
        default=None,
        help="Approve pending change once; repeat with a second approver to apply",
    )
    parser.add_argument("--approver", default="phase16-approver", help="Approver id for --approve")
    parser.add_argument(
        "--strict-ac15",
        action="store_true",
        help="Exit 1 when baseline drift or AC-P16-15 North Star thresholds fail",
    )
    args = parser.parse_args(argv)

    reset_engine_cache_for_tests()

    if args.approve:
        try:
            result = approve_exposure_proposal(args.approve, approver=args.approver)
        except ValueError as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
            return 1
        print(json.dumps({"ok": True, "change": result}, indent=2, ensure_ascii=False))
        return 0 if result.get("status") == "approved" else 0

    report = evaluate_registry(trip_id=args.trip_id, trips_dir=args.trips_dir)

    if args.propose:
        try:
            pending = submit_exposure_proposals(report, operator=args.operator)
        except ValueError as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
            return 1
        out = {
            "ok": True,
            "proposalCount": len(report.get("exposureDebtProposals") or []),
            "pendingChangeId": pending.get("id"),
            "status": pending.get("status"),
            "nextStep": f"python scripts/phase16_template_eval.py --approve {pending.get('id')} --approver <name>",
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    if args.write_baseline:
        out = args.json_out or args.baseline
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"baseline written → {out}")
        return 0

    drift = compare_baseline(report, args.baseline)
    ac15 = compare_ac15_thresholds(report)
    report["baselineCheck"] = drift
    report["ac15Check"] = ac15
    text = json.dumps(report, indent=2, ensure_ascii=False)
    print(text)
    if args.json_out:
        args.json_out.write_text(text + "\n", encoding="utf-8")
    if drift.get("warnings"):
        print("::warning::Phase16 dogfood drift: " + " | ".join(drift["warnings"]))
    if args.strict_ac15:
        if not drift.get("ok") and not drift.get("skipped"):
            return 1
        if not ac15.get("ok"):
            print("::error::AC-P16-15 thresholds: " + " | ".join(ac15.get("failures") or []))
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
