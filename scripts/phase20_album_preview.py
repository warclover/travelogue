#!/usr/bin/env python3
"""Ingest album → Phase20 curate → render preview (one-off dogfood)."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import travelogue.curation.screen_planner  # noqa: F401
from travelogue.config import AppConfig, get_config
from travelogue.config.layout import LayoutAssetAspectConfig, LayoutStrategyEngineConfig
from travelogue.curation.clustering import run_clustering_layer
from travelogue.curation.curate import run_curate
from travelogue.media.ingest import ingest_into_trip
from travelogue.render.engine import render_trip
from travelogue.curation.screen_planner import LAYOUT_ENGINE_SCREENS
from travelogue.services.trip import TripService
from travelogue.services.trip_factory import create_trip


def _trip_id_for_album(album: Path) -> str:
    digest = hashlib.sha256(str(album.resolve()).encode("utf-8")).hexdigest()[:10]
    return f"demo-{digest}"


def _phase20_cfg(base: AppConfig) -> AppConfig:
    se = replace(base.layout.strategy_engine, enabled=False)
    scoring = replace(base.layout.scoring, enabled=False)
    layout = replace(
        base.layout,
        strategy_engine=se,
        scoring=scoring,
        asset_aspect=LayoutAssetAspectConfig(use_case_scoring_enabled=True),
    )
    return replace(base, layout=layout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase20 album ingest + preview")
    parser.add_argument("album", type=Path, help="Photo folder")
    parser.add_argument("--out", type=Path, default=ROOT / ".cache" / "phase20-album-preview")
    args = parser.parse_args()

    album = args.album.resolve()
    if not album.is_dir():
        print(f"album not found: {album}", file=sys.stderr)
        return 1

    trip_id = _trip_id_for_album(album)
    trips_root = ROOT / "trips"
    work = trips_root / trip_id
    trip_json = work / "trip.json"

    base_cfg = get_config()
    cfg = _phase20_cfg(base_cfg)

    if not trip_json.is_file():
        create_trip(
            trip_id,
            trips_root,
            title=(album.name[:20] or "相册"),
            place="东澳岛",
            export_layout="web",
            cfg=cfg,
        )

    svc = TripService(root=ROOT)
    trip = svc.load(trip_json)

    print(f"ingest {album} → {trip_id} ...", flush=True)
    ingest_into_trip(trip, work, from_dir=album, generate_crops=False, dedupe=True)
    svc.save(trip, trip_json)

    print("cluster + curate ...", flush=True)
    run_clustering_layer(trip, trip_dir=work / "cluster", cfg=cfg)
    run_curate(trip, export_layout="web", apply_layout=True, trip_dir=work, cfg=cfg)
    svc.save(trip, trip_json)

    print("render ...", flush=True)
    render_trip(
        trip_json,
        work,
        trip=trip,
        validate=False,
        copy_css=True,
        index_name="index.html",
        layout_engine=LAYOUT_ENGINE_SCREENS,
        export_layout_override="web",
        update_pipeline=False,
    )

    index = work / "index.html"
    file_url = index.resolve().as_uri()
    studio_url = f"http://127.0.0.1:8766/{trip_id}/index.html"

    from collections import Counter

    pids = []
    for ch in trip.get("chapters") or []:
        for s in ch.get("screens") or []:
            if s.get("patternId"):
                pids.append(s["patternId"])

    new_patterns = {
        "screen-mosaic-5-top-hero-4",
        "screen-mosaic-5-left3-right2",
        "screen-mosaic-6-grid-hero-br",
        "screen-landscape-3-wide-top-2",
        "screen-landscape-3-square-left-2",
    }
    hits = {p: c for p, c in Counter(pids).items() if p in new_patterns}

    report = {
        "tripId": trip_id,
        "album": str(album),
        "photoCount": len(trip.get("assets") or []),
        "screenCount": len(pids),
        "newPatternHits": hits,
        "patternTop": dict(Counter(pids).most_common(15)),
        "fileUrl": file_url,
        "studioUrl": studio_url,
        "tripDir": str(work.resolve()),
    }
    (work / "phase20_preview_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\n=== Phase20 preview ===")
    print("tripId:", trip_id)
    print("screens:", len(pids), "photos:", len(trip.get("assets") or []))
    print("new patterns:", hits or "none")
    print("FILE:", file_url)
    print("STUDIO (需 travelogue studio):", studio_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
