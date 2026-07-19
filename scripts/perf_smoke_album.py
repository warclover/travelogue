# -*- coding: utf-8 -*-
"""Real-album smoke for Pipeline Perf V1 (ingest → curate → materialize → render)."""
from __future__ import annotations

import json
import shutil
import sys
import time
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from travelogue.config import get_config, app_config_scope
from travelogue.orchestrator.run import run_trip
from travelogue.services.trip_factory import create_trip
from travelogue.runtime import AppContext


def main() -> None:
    album = Path(sys.argv[1])
    max_photos = int(sys.argv[2]) if len(sys.argv) > 2 else 48
    trips_root = Path("trips")
    slug = "perf-smoke"
    trip_dir = trips_root / slug
    if trip_dir.exists():
        shutil.rmtree(trip_dir)

    cfg = get_config(reload=True)
    cfg = replace(
        cfg,
        ingest=replace(cfg.ingest, max_photos=max_photos, detect_faces=True),
        pipeline=replace(
            cfg.pipeline,
            parallel_ingest=True,
            parallel_ingest_workers=0,
            deferred_derivatives=True,
        ),
        clustering=replace(cfg.clustering, enabled="false"),
    )

    with app_config_scope(cfg):
        trip_json = create_trip(slug, trips_root, title="perf-smoke", place="smoke", cfg=cfg)
        t0 = time.perf_counter()
        result = run_trip(
            trip_json,
            from_stage="ingest",
            until="rendered",
            album_dir=album,
            skip_locked=False,
            validate=False,
            cfg=cfg,
        )
        elapsed = time.perf_counter() - t0

    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    assets = trip.get("assets") or []
    timings = (trip.get("pipeline") or {}).get("timings") or {}
    selected = set()
    for ch in trip.get("chapters") or []:
        for item in ch.get("items") or []:
            if item.get("assetId"):
                selected.add(item["assetId"])
            for aid in item.get("assetIds") or []:
                selected.add(aid)
    if trip.get("coverAssetId"):
        selected.add(trip["coverAssetId"])

    preview_only = 0
    full_srcset = 0
    missing_hi = []
    for a in assets:
        widths = [e.get("width") for e in (a.get("srcset") or [])]
        plan = a.get("derivedPlan") or {}
        aid = a.get("id")
        if aid in selected:
            if 2400 in widths or 3200 in widths:
                full_srcset += 1
            else:
                missing_hi.append(aid)
        else:
            if max(widths or [0]) <= 1600:
                preview_only += 1

    report = {
        "slug": slug,
        "stages": result.stages,
        "elapsedSec": round(elapsed, 1),
        "assetCount": len(assets),
        "selectedCount": len(selected),
        "timings": {k: timings.get(k) for k in (
            "ingestMs", "ingestWorkers", "ingestWorkersDownscaled",
            "curateMs", "materializeMs", "narrateMs", "renderMs", "totalMs",
        )},
        "previewOnlyUnselected": preview_only,
        "selectedWithHiRes": full_srcset,
        "selectedMissingHiRes": missing_hi[:10],
        "ok": (
            float(timings.get("ingestWorkers") or 0) >= 2
            and len(missing_hi) == 0
            and "ingest" in result.stages
            and "render" in result.stages
        ),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
