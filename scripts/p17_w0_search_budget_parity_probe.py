#!/usr/bin/env python3
"""W0 临时探针 · 审计 B：search_budget 挂钟是否改变 screens[] 产出。

标注：W0 一次性验证脚本，W1 parity CI 落地后删除或迁入 layout_engine/cli.py audit。

Usage:
  python scripts/p17_w0_search_budget_parity_probe.py trips/demo-2025
  python scripts/p17_w0_search_budget_parity_probe.py --fixture golden-mixed-scenes
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.phase3_layout_acceptance import _weights_dict
from travelogue.config import AppConfig, LayoutScoringConfig, get_config
from travelogue.curation.clustering import run_clustering_layer
from travelogue.curation.curate import run_curate
from travelogue.curation.layout_scoring import PHASE3B_WEIGHTS


def _prepare_trip(trip: dict) -> dict:
    t = copy.deepcopy(trip)
    t.setdefault("pipeline", {})["status"] = "structure_draft"
    t.pop("chapters", None)
    t.setdefault("curation", {}).pop("clustering", None)
    for asset in t.get("assets") or []:
        asset.pop("sceneClusterId", None)
        asset.pop("clusterSource", None)
    return t


def _screens_fingerprint(chapters: list[dict]) -> list[dict]:
    """Pattern + slot asset ids per screen (parity compare)."""
    out: list[dict] = []
    for ch in chapters:
        for sc in ch.get("screens") or []:
            slots = [
                {"slot": s.get("slot"), "assetId": s.get("assetId")}
                for s in (sc.get("slots") or [])
            ]
            out.append({"patternId": sc.get("patternId"), "slots": slots})
    return out


def _run_once(
    trip: dict,
    *,
    work_dir: Path,
    scoring_enabled: bool,
    search_timeout_ms: int,
    max_evaluations_per_trip: int = 500,
) -> dict:
    base = get_config(reload=True)
    scoring = LayoutScoringConfig(
        enabled=scoring_enabled,
        beam_width=3,
        search_timeout_ms=search_timeout_ms,
        max_candidates_per_bucket=12,
        max_evaluations_per_trip=max_evaluations_per_trip,
        allow_burst_split=False,
        subject_run_tolerance=1,
        weights=_weights_dict(PHASE3B_WEIGHTS) if scoring_enabled else LayoutScoringConfig().weights,
    )
    cfg = replace(base.layout, scoring=scoring)
    app_cfg = replace(base, layout=cfg)

    body = _prepare_trip(trip)
    tag = f"scoring-{scoring_enabled}_timeout-{search_timeout_ms}"
    run_dir = work_dir / tag
    run_clustering_layer(body, trip_dir=run_dir / "cluster", cfg=app_cfg)
    run_curate(body, apply_layout=True, trip_dir=run_dir, cfg=app_cfg)

    curation = body.get("curation") or {}
    budget = curation.get("layoutSearchBudget") or {}
    return {
        "tag": tag,
        "scoringEnabled": scoring_enabled,
        "searchTimeoutMs": search_timeout_ms,
        "screens": _screens_fingerprint(body.get("chapters") or []),
        "screenCount": sum(len(ch.get("screens") or []) for ch in (body.get("chapters") or [])),
        "layoutSearchBudget": budget,
        "skipReason": curation.get("degradationReason"),
        "replanApplied": bool(budget.get("evaluations", 0) > 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="P17 W0 search_budget parity probe")
    parser.add_argument("trip_path", nargs="?", help="Path to trip dir or trip.json")
    parser.add_argument("--fixture", default="", help="Golden fixture name")
    args = parser.parse_args()

    if args.fixture:
        from scripts.phase3_ig2_report import load_fixture_trip

        trip = load_fixture_trip(args.fixture)
        trip_id = args.fixture
    elif args.trip_path:
        p = Path(args.trip_path)
        trip_file = p / "trip.json" if p.is_dir() else p
        trip = json.loads(trip_file.read_text(encoding="utf-8"))
        trip_id = trip.get("tripId") or p.stem
    else:
        parser.error("Provide trip_path or --fixture")

    asset_count = len(trip.get("assets") or [])
    print(f"trip={trip_id} assets={asset_count}")

    with tempfile.TemporaryDirectory(prefix="p17-w0-budget-") as tmp:
        work = Path(tmp)
        # A: 默认路径 scoring.enabled=false（现网默认）
        off_inf = _run_once(trip, work_dir=work, scoring_enabled=False, search_timeout_ms=2_147_483_647)
        off_tight = _run_once(trip, work_dir=work, scoring_enabled=False, search_timeout_ms=1)

        # B: beam 开闸 scoring.enabled=true（Studio 实验路径）
        on_inf = _run_once(trip, work_dir=work, scoring_enabled=True, search_timeout_ms=2_147_483_647)
        on_tight = _run_once(trip, work_dir=work, scoring_enabled=True, search_timeout_ms=1)

    default_same = off_inf["screens"] == off_tight["screens"]
    beam_same = on_inf["screens"] == on_tight["screens"]

    report = {
        "tripId": trip_id,
        "assetCount": asset_count,
        "defaultPath": {
            "scoringEnabled": False,
            "timeoutInfVs1msScreensEqual": default_same,
            "screenCount": off_inf["screenCount"],
            "layoutSearchBudget": off_inf["layoutSearchBudget"],
        },
        "beamPath": {
            "scoringEnabled": True,
            "timeoutInfVs1msScreensEqual": beam_same,
            "screenCountInf": on_inf["screenCount"],
            "screenCountTight": on_tight["screenCount"],
            "budgetInf": on_inf["layoutSearchBudget"],
            "budgetTight": on_tight["layoutSearchBudget"],
        },
        "conclusion": {
            "defaultPathAffectedByWallClock": not default_same,
            "beamPathAffectedByWallClock": not beam_same,
        },
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
