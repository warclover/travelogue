"""Phase 17 golden layout metrics · AC-P17-16～19.

Usage:
  python scripts/phase17_golden_metrics.py --fixture golden-mixed-scenes
  python scripts/phase17_golden_metrics.py --fixture golden-mixed-scenes --strict --write
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.phase3_ig2_report import _cfg_for_mode, load_fixture_trip
from travelogue.config import AppConfig
from travelogue.layout_engine.golden_probe import merge_gates, run_ac_probe
from tests.p17_golden_fixtures import P17_MIXED_FIXTURES

from travelogue.layout_engine.metrics import (
    assets_map_from_trip,
    compute_layout_golden_metrics,
    curate_trip_chapters,
    evaluate_ac_delta,
)

DEFAULT_BASELINE = ROOT / "docs" / "acceptance-records" / "p17-golden-metrics-baseline.json"
DEFAULT_FIXTURES = (
    "golden-mixed-scenes",
    "golden-p17-mixed-person",
    "golden-portrait-family",
    "golden-portrait-travel",
    "golden-landscape-coast",
    "golden-landscape-mountain",
)

AC_FIXTURE_SCOPE: dict[str, tuple[str, ...] | None] = {
    "AC-P17-16": P17_MIXED_FIXTURES,
    "AC-P17-19": P17_MIXED_FIXTURES,
}

AC_SPECS: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {
    "AC-P17-16": (
        {"saliency_scoring": False},
        {"saliency_scoring": True},
    ),
    "AC-P17-17": (
        {"beat_profile": "flat"},
        {"beat_profile": "classic_magazine"},
    ),
    "AC-P17-18": (
        {"tone_harmony": False},
        {"tone_harmony": True},
    ),
    "AC-P17-19": (
        {"hungarian_assignment": False, "quality_unified": False},
        {"hungarian_assignment": True, "quality_unified": True},
    ),
    "AC-P17-20": (
        {"segment_order_optimizer": False},
        {"segment_order_optimizer": True},
    ),
    "AC-P17-26": (
        {"highlight_windows": False},
        {"highlight_windows": True},
    ),
}


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _git_commit() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip() or None
    except Exception:
        return None


def _cfg_lse_enabled(base: AppConfig) -> AppConfig:
    se = replace(base.layout.strategy_engine, enabled=True)
    layout = replace(base.layout, strategy_engine=se, scoring=replace(base.layout.scoring, enabled=False))
    return replace(base, layout=layout)


def _cfg_with_capabilities(base: AppConfig, **caps: Any) -> AppConfig:
    merged = replace(base.layout.strategy_engine.capabilities, **caps)
    se = replace(base.layout.strategy_engine, capabilities=merged)
    layout = replace(base.layout, strategy_engine=se)
    return replace(base, layout=layout)


def _run_capability_pair(
    trip: dict,
    *,
    fixture_id: str,
    ac_id: str,
    baseline_caps: dict[str, Any],
    candidate_caps: dict[str, Any],
    work_dir: Path,
) -> dict[str, Any]:
    base_cfg = _cfg_lse_enabled(_cfg_for_mode("p3_full"))
    baseline_cfg = _cfg_with_capabilities(base_cfg, **baseline_caps)
    candidate_cfg = _cfg_with_capabilities(base_cfg, **candidate_caps)
    assets = assets_map_from_trip(trip)

    base_chapters = curate_trip_chapters(
        trip,
        work_dir=work_dir / ac_id / "baseline",
        cfg=baseline_cfg,
    )
    cand_chapters = curate_trip_chapters(
        trip,
        work_dir=work_dir / ac_id / "candidate",
        cfg=candidate_cfg,
    )
    base_metrics = compute_layout_golden_metrics(base_chapters, assets)
    cand_metrics = compute_layout_golden_metrics(cand_chapters, assets)
    ac_eval = evaluate_ac_delta(base_metrics, cand_metrics)
    curate_gate = ac_eval.get(ac_id) or {}
    probe = run_ac_probe(
        trip,
        ac_id,
        baseline_cfg=baseline_cfg,
        candidate_cfg=candidate_cfg,
    )
    supplemental = None
    if ac_id == "AC-P17-17":
        supplemental = run_ac_probe(
            trip,
            "AC-P17-17b",
            baseline_cfg=baseline_cfg,
            candidate_cfg=candidate_cfg,
        )
    gate = merge_gates(curate_gate, probe, supplemental_probe=supplemental)
    if ac_id == "AC-P17-17":
        gate["AC-P17-17b"] = ac_eval.get("AC-P17-17b")
        if (gate.get("AC-P17-17b") or {}).get("passed") is False:
            gate["passed"] = False
    return {
        "acId": ac_id,
        "fixtureId": fixture_id,
        "baselineCaps": baseline_caps,
        "candidateCaps": candidate_caps,
        "baselineMetrics": base_metrics,
        "candidateMetrics": cand_metrics,
        "gate": gate,
        "passed": gate.get("passed"),
        "measurable": gate.get("measurable"),
    }


def evaluate_fixture(fixture_id: str, *, work_dir: Path) -> dict[str, Any]:
    trip = load_fixture_trip(fixture_id)
    pairs: list[dict[str, Any]] = []
    for ac_id, (base_caps, cand_caps) in AC_SPECS.items():
        pairs.append(
            _run_capability_pair(
                trip,
                fixture_id=fixture_id,
                ac_id=ac_id,
                baseline_caps=base_caps,
                candidate_caps=cand_caps,
                work_dir=work_dir / fixture_id,
            )
        )
    return {
        "fixtureId": fixture_id,
        "pairs": pairs,
        "passed": not any(p.get("passed") is False for p in pairs),
    }


def _ac_applies_to_fixture(ac_id: str, fixture_id: str) -> bool:
    scope = AC_FIXTURE_SCOPE.get(ac_id)
    if scope is None:
        return True
    return fixture_id in scope


def build_record(fixture_results: list[dict[str, Any]]) -> dict[str, Any]:
    ac_summary: dict[str, bool] = {}
    for fr in fixture_results:
        fixture_id = str(fr.get("fixtureId") or "")
        for pair in fr.get("pairs") or []:
            ac_id = str(pair.get("acId") or "")
            if not ac_id or not _ac_applies_to_fixture(ac_id, fixture_id):
                continue
            prev = ac_summary.get(ac_id)
            cur = pair.get("passed")
            if cur is False:
                ac_summary[ac_id] = False
            elif prev is None and cur is not False:
                ac_summary[ac_id] = cur
            elif prev not in (False, None) and cur is not False:
                ac_summary[ac_id] = prev and cur
            if ac_id == "AC-P17-17":
                g17b = (pair.get("gate") or {}).get("AC-P17-17b") or {}
                b_prev = ac_summary.get("AC-P17-17b")
                b_cur = g17b.get("passed")
                if b_cur is False:
                    ac_summary["AC-P17-17b"] = False
                elif b_prev is None and b_cur is not False:
                    ac_summary["AC-P17-17b"] = b_cur
                elif b_prev not in (False, None) and b_cur is not False:
                    ac_summary["AC-P17-17b"] = b_prev and b_cur
    return {
        "schemaVersion": "1",
        "benchmarkId": "p17-golden-metrics-v1",
        "emittedAt": _now(),
        "commit": _git_commit(),
        "ac_p17": ac_summary,
        "fixtures": fixture_results,
        "passed": not any(v is False for v in ac_summary.values()) if ac_summary else True,
        "notes": "LSE enabled · per-AC baseline vs capability-on candidate on golden fixtures",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 17 golden layout metrics (AC-P17-16～19)")
    parser.add_argument("--fixture", action="append", help="Fixture trip id")
    parser.add_argument("--work-dir", type=Path, default=ROOT / ".cache" / "p17-golden-metrics")
    parser.add_argument("--out", type=Path, default=ROOT / ".cache" / "p17-golden-metrics.json")
    parser.add_argument("--write", action="store_true", help="Write acceptance baseline record")
    parser.add_argument("--strict", action="store_true", help="Exit 1 when any AC gate fails")
    args = parser.parse_args()

    fixtures = args.fixture or list(DEFAULT_FIXTURES)
    args.work_dir.mkdir(parents=True, exist_ok=True)
    results = [evaluate_fixture(fid, work_dir=args.work_dir) for fid in fixtures]
    record = build_record(results)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))

    if args.write:
        DEFAULT_BASELINE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_BASELINE.write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    if args.strict and any(v is False for v in record.get("ac_p17", {}).values()):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
