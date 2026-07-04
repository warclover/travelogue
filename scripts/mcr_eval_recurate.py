#!/usr/bin/env python3
"""MCR AC-MCR-05/06 · re-curate golden trips and record before/after layoutMetrics.

Writes JSON to .cache/mcr-eval/ (gitignored). Does not modify trips/*/trip.json.

Usage:
  python scripts/mcr_eval_recurate.py chuanzang-studio demo-80301df45c
  python scripts/mcr_eval_recurate.py chuanzang-studio --write .cache/mcr-eval/chuanzang-studio.json
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_HERO_MOSAIC = frozenset(
    {
        "screen-mosaic-5-main-hero-plus-4",
        "screen-mosaic-6-main-hero-plus-5",
    }
)


def _load_trip(target: str, *, trips_dir: Path) -> tuple[dict, str, Path]:
    path = Path(target)
    if path.is_file():
        trip = json.loads(path.read_text(encoding="utf-8"))
        return trip, str(trip.get("tripId") or path.parent.name), path
    trip_json = trips_dir / target / "trip.json"
    if not trip_json.is_file():
        raise FileNotFoundError(target)
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    return trip, str(trip.get("tripId") or target), trip_json


def _prepare_trip(trip: dict) -> dict:
    body = copy.deepcopy(trip)
    body.setdefault("pipeline", {})["status"] = "structure_draft"
    body.pop("chapters", None)
    curation = body.setdefault("curation", {})
    for key in ("layoutMetrics", "mosaicDecisionLog", "displayedAssetIds"):
        curation.pop(key, None)
    curation.pop("clustering", None)
    for asset in body.get("assets") or []:
        asset.pop("sceneClusterId", None)
        asset.pop("clusterSource", None)
    return body


def _snapshot(trip: dict) -> dict[str, Any]:
    chapters = trip.get("chapters") or []
    patterns: list[str] = []
    hero: list[str] = []
    mosaic: list[str] = []
    for ch in chapters:
        for screen in ch.get("screens") or []:
            pid = str(screen.get("patternId") or "")
            if pid:
                patterns.append(pid)
            if pid in _HERO_MOSAIC:
                hero.append(pid)
            if "mosaic" in pid:
                mosaic.append(pid)
    curation = trip.get("curation") or {}
    layout_metrics = curation.get("layoutMetrics") if isinstance(curation.get("layoutMetrics"), dict) else {}
    return {
        "chapterCount": len(chapters),
        "screenCount": len(patterns),
        "heroMosaicScreenCount": len(hero),
        "heroMosaicPatterns": sorted(set(hero)),
        "mosaicScreenCount": len(mosaic),
        "mosaicPatterns": sorted(set(mosaic)),
        "layoutMetrics": layout_metrics,
        "mosaicDecisionLogCount": len(curation.get("mosaicDecisionLog") or []),
    }


def _recurate(trip: dict, *, trip_id: str, work_dir: Path) -> dict[str, Any]:
    from travelogue.config import get_config
    from travelogue.curation.clustering import run_clustering_layer
    from travelogue.curation.curate import run_curate

    cfg = get_config()
    body = _prepare_trip(trip)
    work_dir.mkdir(parents=True, exist_ok=True)
    run_clustering_layer(body, trip_dir=work_dir / "cluster", cfg=cfg)
    run_curate(body, apply_layout=True, trip_dir=work_dir / "curate", cfg=cfg)
    return _snapshot(body)


def evaluate_trip(target: str, *, trips_dir: Path, work_dir: Path) -> dict[str, Any]:
    trip, trip_id, trip_json = _load_trip(target, trips_dir=trips_dir)
    before = _snapshot(trip)
    print(f"MCR eval {trip_id}: before hero_mosaic={before['heroMosaicScreenCount']} ...", flush=True)
    after = _recurate(trip, trip_id=trip_id, work_dir=work_dir / trip_id)
    print(
        f"  after hero_mosaic={after['heroMosaicScreenCount']} "
        f"patterns={after['heroMosaicPatterns']}",
        flush=True,
    )
    return {
        "recordId": "mcr-eval-recurate",
        "tripId": trip_id,
        "tripJson": str(trip_json),
        "evaluatedAt": datetime.now(timezone.utc).isoformat(),
        "before": before,
        "after": after,
        "passesHeroMosaic": after["heroMosaicScreenCount"] >= 1,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="MCR re-curate eval (layoutMetrics before/after)")
    parser.add_argument(
        "targets",
        nargs="*",
        default=["chuanzang-studio"],
        help="Trip id under trips/ or path to trip.json",
    )
    parser.add_argument("--trips-dir", type=Path, default=ROOT / "trips")
    parser.add_argument("--work-dir", type=Path, default=ROOT / ".cache" / "mcr-eval-work")
    parser.add_argument("--write", type=Path, default=None, help="Write combined JSON record")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / ".cache" / "mcr-eval",
        help="Per-trip output directory",
    )
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    for target in args.targets:
        try:
            row = evaluate_trip(target, trips_dir=args.trips_dir, work_dir=args.work_dir)
        except FileNotFoundError:
            print(f"SKIP {target} (not found)", file=sys.stderr)
            continue
        except Exception as exc:
            print(f"FAIL {target}: {exc}", file=sys.stderr)
            continue
        out_path = args.out_dir / f"{row['tripId']}.json"
        out_path.write_text(json.dumps(row, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"  wrote {out_path}", flush=True)
        results.append(row)

    if not results:
        return 1

    payload = {
        "recordId": "mcr-eval-recurate",
        "evaluatedAt": datetime.now(timezone.utc).isoformat(),
        "trips": results,
    }
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"combined record -> {args.write}", flush=True)

    chuanzang = next((r for r in results if r["tripId"] == "chuanzang-studio"), None)
    if chuanzang and not chuanzang["passesHeroMosaic"]:
        print("[warn] AC-MCR-05: chuanzang-studio has zero hero mosaic after re-curate", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
