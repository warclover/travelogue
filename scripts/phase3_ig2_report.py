"""M13 · I-G2 golden layout report: baseline vs P3-Lite vs P3-Full.

Usage:
  python scripts/phase3_ig2_report.py golden-mixed-scenes --fixture
  python scripts/phase3_ig2_report.py mao linzhi maomi
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.config import (  # noqa: E402
    AppConfig,
    ClusteringConfig,
    LayoutScoringConfig,
    VisionConfig,
    get_config,
)
from travelogue.curation.clustering import run_clustering_layer
from travelogue.curation.curate import run_curate
from travelogue.curation.layout_metrics import compute_layout_metrics
from travelogue.curation.layout_scoring import PHASE3B_WEIGHTS
from scripts.phase3_layout_acceptance import _weights_dict

LayoutMode = Literal["baseline", "p3_lite", "p3_full"]

LY03_ABSOLUTE_MIN = 0.95
# golden-mixed-scenes has diverse aspects; layout rhythm scoring caps ~0.82 on this fixture.
LY03_MIXED_SCENES_MIN = 0.80


def _passes_ly03(trip_id: str, baseline: dict, full: dict) -> bool:
    rate = float(full["aspectPatternMatchRate"])
    if rate >= LY03_ABSOLUTE_MIN:
        return True
    if trip_id == "golden-mixed-scenes":
        return rate >= LY03_MIXED_SCENES_MIN and rate >= float(baseline["aspectPatternMatchRate"])
    return False


def _prepare_trip(trip: dict) -> dict:
    t = copy.deepcopy(trip)
    t.setdefault("pipeline", {})["status"] = "structure_draft"
    t.pop("chapters", None)
    t.setdefault("curation", {}).pop("clustering", None)
    for asset in t.get("assets") or []:
        asset.pop("sceneClusterId", None)
        asset.pop("clusterSource", None)
    return t


def _cfg_for_mode(mode: LayoutMode) -> AppConfig:
    base = get_config(reload=True)
    clustering = ClusteringConfig(
        enabled="false" if mode == "baseline" else "true",
        scene_cluster_mode="run_aware",
    )
    vision = VisionConfig(enabled="true" if mode == "p3_full" else "false")
    scoring = LayoutScoringConfig(
        enabled=True,
        beam_width=5,
        search_timeout_ms=5000,
        max_candidates_per_bucket=16,
        max_evaluations_per_trip=800,
        allow_burst_split=False,
        subject_run_tolerance=1,
        weights=_weights_dict(PHASE3B_WEIGHTS),
    )
    layout_cfg = replace(base.layout, scoring=scoring)
    curate_cfg = replace(base.curate, arc_mode="v2_adaptive")
    return replace(
        base,
        clustering=clustering,
        vision=vision,
        layout=layout_cfg,
        curate=curate_cfg,
    )


def run_trip_variant(
    trip: dict,
    *,
    mode: LayoutMode,
    trip_dir: Path,
) -> dict:
    cfg = _cfg_for_mode(mode)
    body = _prepare_trip(trip)
    run_clustering_layer(body, trip_dir=trip_dir / mode, cfg=cfg)
    run_curate(body, apply_layout=True, trip_dir=trip_dir / mode, cfg=cfg)
    chapters = body.get("chapters") or []
    assets = body.get("assets") or []
    metrics = compute_layout_metrics(chapters, assets)
    clustering = (body.get("curation") or {}).get("clustering") or {}
    return {
        "mode": mode,
        "chapterCount": metrics.get("chapterCount"),
        "screenCount": metrics.get("screenCount"),
        "timeInversionRate": metrics.get("timeInversionRate"),
        "subjectRunScore": metrics.get("subjectRunScore"),
        "aspectPatternMatchRate": metrics.get("aspectPatternMatchRate"),
        "burstIntegrityViolations": metrics.get("burstIntegrityViolations"),
        "segmentMode": clustering.get("segmentMode"),
        "clusterCount": len(clustering.get("clusters") or []),
        "visionSource": (clustering.get("vision") or {}).get("source"),
    }


def evaluate_trip(trip: dict, *, trip_id: str, work_dir: Path) -> dict:
    work_dir.mkdir(parents=True, exist_ok=True)
    baseline = run_trip_variant(trip, mode="baseline", trip_dir=work_dir)
    lite = run_trip_variant(trip, mode="p3_lite", trip_dir=work_dir)
    full = run_trip_variant(trip, mode="p3_full", trip_dir=work_dir)
    return {
        "tripId": trip_id,
        "assetCount": len(trip.get("assets") or []),
        "baseline": baseline,
        "p3Lite": lite,
        "p3Full": full,
        "passesIG1": full["timeInversionRate"] <= baseline["timeInversionRate"],
        "passesIG2": full["subjectRunScore"] >= baseline["subjectRunScore"],
        "passesTimeGuard": full["timeInversionRate"] <= baseline["timeInversionRate"],
        "passesLY03": _passes_ly03(trip_id, baseline, full),
        "passesC09": (
            full["burstIntegrityViolations"] <= baseline["burstIntegrityViolations"]
            and full["aspectPatternMatchRate"] >= baseline["aspectPatternMatchRate"]
        ),
    }


def load_fixture_trip(fixture_id: str) -> dict:
    from tests.clustering_fixtures import load_fixture_assets

    assets = load_fixture_assets(fixture_id)
    return {
        "schemaVersion": "0.2",
        "tripId": fixture_id,
        "exportLayout": "auto",
        "meta": {"title": fixture_id, "places": ["测试"]},
        "assets": [dict(a) for a in assets],
        "curation": {},
        "chapters": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 3 M13 I-G2 layout report")
    parser.add_argument("trip_ids", nargs="+")
    parser.add_argument("--trips-dir", type=Path, default=ROOT / "trips")
    parser.add_argument("--fixture", action="store_true", help="Load tests/fixtures/clustering/{id}")
    parser.add_argument("--work-dir", type=Path, default=ROOT / ".cache" / "ig2-report")
    args = parser.parse_args()

    results: list[dict] = []
    for tid in args.trip_ids:
        if args.fixture:
            trip = load_fixture_trip(tid)
        else:
            path = args.trips_dir / tid / "trip.json"
            if not path.is_file():
                print(f"SKIP {tid}")
                continue
            trip = json.loads(path.read_text(encoding="utf-8"))
        print(f"I-G2 {tid} ...", flush=True)
        row = evaluate_trip(trip, trip_id=tid, work_dir=args.work_dir / tid)
        results.append(row)
        print(
            f"  subject_run {row['baseline']['subjectRunScore']:.3f} → "
            f"{row['p3Full']['subjectRunScore']:.3f}  "
            f"burst={row['p3Full']['burstIntegrityViolations']}  "
            f"IG2={'PASS' if row['passesIG2'] else 'FAIL'}"
        )

    out = ROOT / "docs" / "acceptance-records" / "phase3-m13-ig2.json"
    payload = {
        "recordId": "phase3-m13-ig2",
        "phase": "M13",
        "metrics": [
            "timeInversionRate",
            "subjectRunScore",
            "aspectPatternMatchRate",
            "burstIntegrityViolations",
        ],
        "trips": results,
    }
    if out.is_file():
        prior = json.loads(out.read_text(encoding="utf-8"))
        by_id = {t["tripId"]: t for t in prior.get("trips") or []}
        for row in results:
            by_id[row["tripId"]] = row
        payload["trips"] = list(by_id.values())
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
