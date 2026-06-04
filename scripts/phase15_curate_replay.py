#!/usr/bin/env python3
"""Phase 15 full curate replay: baseline (mosaic off) vs MCS (mosaic on).

Usage:
  python scripts/phase15_curate_replay.py golden-mixed-scenes --fixture
  python scripts/phase15_curate_replay.py mao maomi linzhi
  python scripts/phase15_curate_replay.py --write docs/acceptance-records/phase15-curate-replay.json
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.config import AppConfig
from travelogue.curation.chapter_items import summarize_screen_patterns
from travelogue.curation.clustering import run_clustering_layer
from travelogue.curation.curate import run_curate
from travelogue.curation.mosaic.metrics import (
    compute_mosaic_metrics,
    mcs_unified_exposure_rate,
    mosaic5_exposure_rate,
)
from scripts.phase3_ig2_report import _cfg_for_mode, load_fixture_trip


def _prepare_trip(trip: dict) -> dict:
    t = copy.deepcopy(trip)
    t.setdefault("pipeline", {})["status"] = "structure_draft"
    t.pop("chapters", None)
    t.setdefault("curation", {}).pop("clustering", None)
    for asset in t.get("assets") or []:
        asset.pop("sceneClusterId", None)
        asset.pop("clusterSource", None)
    return t


def _cfg_p3_full_mosaic(*, enabled: bool) -> AppConfig:
    base = _cfg_for_mode("p3_full")
    mosaic = replace(
        base.mosaic,
        enabled=enabled,
        enabled_window_sizes=(3, 4, 5, 6, 8, 9),
        unified_mode=True,
        scorer_version="p15-s2",
        min_candidate_score=0.35 if enabled else base.mosaic.min_candidate_score,
    )
    return replace(base, mosaic=mosaic)


def _run_curate_variant(
    trip: dict,
    *,
    trip_id: str,
    work_dir: Path,
    mosaic_enabled: bool,
) -> dict[str, Any]:
    cfg = _cfg_p3_full_mosaic(enabled=mosaic_enabled)
    body = _prepare_trip(trip)
    tag = "mosaicOn" if mosaic_enabled else "mosaicOff"
    run_clustering_layer(body, trip_dir=work_dir / tag / "cluster", cfg=cfg)
    run_curate(body, apply_layout=True, trip_dir=work_dir / tag, cfg=cfg)
    chapters = body.get("chapters") or []
    curation = body.get("curation") or {}
    logs = curation.get("mosaicDecisionLog") or []
    layout_metrics = (curation.get("layoutMetrics") or {}) if isinstance(curation.get("layoutMetrics"), dict) else {}
    patterns = summarize_screen_patterns(chapters)
    mosaic_metrics = compute_mosaic_metrics(chapters, mosaic_logs=logs if mosaic_enabled else None)
    return {
        "mosaicEnabled": mosaic_enabled,
        "chapterCount": len(chapters),
        "screenPatterns": patterns,
        "mosaic5ExposureRate": mosaic5_exposure_rate(chapters),
        "mcsUnifiedExposureRate": mcs_unified_exposure_rate(chapters),
        "mosaicMetrics": mosaic_metrics if mosaic_enabled else None,
        "mosaicDecisionCount": len(logs),
        "displayedAssetCount": len(curation.get("displayedAssetIds") or []),
        "layoutMetrics": layout_metrics or None,
    }


def evaluate_trip_curate(
    trip: dict,
    *,
    trip_id: str,
    work_dir: Path,
) -> dict[str, Any]:
    off = _run_curate_variant(
        trip, trip_id=trip_id, work_dir=work_dir, mosaic_enabled=False
    )
    on = _run_curate_variant(
        trip, trip_id=trip_id, work_dir=work_dir, mosaic_enabled=True
    )
    off_m5 = float(off["mosaic5ExposureRate"])
    on_m5 = float(on["mosaic5ExposureRate"])
    off_u = float(off["mcsUnifiedExposureRate"])
    on_u = float(on["mcsUnifiedExposureRate"])
    on_metrics = on.get("layoutMetrics") or on.get("mosaicMetrics") or {}
    fallback = (on.get("mosaicMetrics") or {}).get("mosaicFallbackRate")
    coverage = float(
        on_metrics.get("eligible_to_screen_coverage")
        or on_metrics.get("layout.eligible_to_screen_coverage")
        or 0.0
    )
    lift_m5 = on_m5 - off_m5
    lift_ratio = round(on_m5 / off_m5, 4) if off_m5 > 0 else None
    return {
        "tripId": trip_id,
        "assetCount": len(trip.get("assets") or []),
        "mosaicOff": off,
        "mosaicOn": on,
        "lift": {
            "mosaic5ExposureRate": round(lift_m5, 6),
            "mcsUnifiedExposureRate": round(on_u - off_u, 6),
            "mosaic5LiftRatio": lift_ratio,
        },
        "passesExposureLift": on_m5 >= off_m5,
        "passesUnifiedLift": on_u >= off_u,
        "passesCoverage": (
            coverage >= (0.85 if trip_id == "golden-mixed-scenes" else 0.99)
            if on_metrics
            else True
        ),
        "passesMosaic5LiftWhenBaseline": lift_m5 > 0 if off_m5 > 0 else True,
        "mosaicFallbackRateOn": fallback,
        "eligibleToScreenCoverageOn": coverage or None,
    }


def _load_trip(target: str, *, fixture: bool, trips_dir: Path) -> tuple[dict, str]:
    if fixture:
        return load_fixture_trip(target), target
    path = Path(target)
    if path.is_file():
        trip = json.loads(path.read_text(encoding="utf-8"))
        return trip, trip.get("tripId") or path.parent.name
    trip_json = trips_dir / target / "trip.json"
    if not trip_json.is_file():
        raise FileNotFoundError(target)
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    return trip, trip.get("tripId") or target


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 15 curate replay (mosaic off vs on)")
    ap.add_argument(
        "targets",
        nargs="*",
        default=["golden-mixed-scenes"],
        help="fixture id, trip id under trips/, or path to trip.json",
    )
    ap.add_argument("--fixture", action="store_true", help="Treat targets as clustering fixture ids")
    ap.add_argument("--trips-dir", type=Path, default=ROOT / "trips")
    ap.add_argument("--work-dir", type=Path, default=ROOT / ".cache" / "phase15-curate-replay")
    ap.add_argument("--write", type=Path, default=None)
    args = ap.parse_args()

    results: list[dict] = []
    for target in args.targets:
        try:
            trip, trip_id = _load_trip(
                target, fixture=args.fixture, trips_dir=args.trips_dir
            )
        except FileNotFoundError:
            print(f"SKIP {target} (not found)", file=sys.stderr)
            continue
        if len(trip.get("assets") or []) < 4:
            print(f"SKIP {trip_id} (too few assets)", file=sys.stderr)
            continue
        print(f"curate replay {trip_id} ...", flush=True)
        row = evaluate_trip_curate(
            trip, trip_id=trip_id, work_dir=args.work_dir / trip_id
        )
        results.append(row)
        print(
            f"  mosaic5 {row['mosaicOff']['mosaic5ExposureRate']:.3f} → "
            f"{row['mosaicOn']['mosaic5ExposureRate']:.3f}  "
            f"MCS {row['mosaicOff']['mcsUnifiedExposureRate']:.3f} → "
            f"{row['mosaicOn']['mcsUnifiedExposureRate']:.3f}",
            flush=True,
        )

    if not results:
        return 1

    payload = {
        "recordId": "phase15-curate-replay",
        "phase": "P15",
        "config": {
            "mode": "p3_full",
            "mosaic.enabled": True,
            "mosaic.unifiedMode": True,
            "mosaic.scorerVersion": "p15-s2",
        },
        "trips": results,
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    print(text)
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote {args.write}", flush=True)
    ok = all(
        r["passesExposureLift"]
        and r["passesUnifiedLift"]
        and r.get("passesCoverage", True)
        for r in results
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
