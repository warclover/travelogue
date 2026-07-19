# -*- coding: utf-8 -*-
"""One-off perf probe: serial vs parallel ingest on a real album subset."""
from __future__ import annotations

import json
import shutil
import sys
import time
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from travelogue.config import get_config, app_config_scope
from travelogue.media.ingest import ingest_into_trip
from travelogue.services.trip_factory import create_trip
from travelogue.runtime import AppContext


def run_once(album: Path, trips_root: Path, tag: str, *, parallel: bool, workers: int, max_photos: int) -> dict:
    cfg = get_config(reload=True)
    cfg = replace(cfg, pipeline=replace(cfg.pipeline, parallel_ingest=parallel, parallel_ingest_workers=workers))
    slug = f"perf-{tag}"
    trip_dir = trips_root / slug
    if trip_dir.exists():
        shutil.rmtree(trip_dir)
    with app_config_scope(cfg):
        trip_json = create_trip(slug, trips_root, title="perf", place="perf", cfg=cfg)
        ctx = AppContext(cfg=cfg, trips_root=trips_root.resolve())
        svc = ctx.trip_service()
        trip = svc.load(trip_json)
        t0 = time.perf_counter()
        res = ingest_into_trip(
            trip, trip_json.parent,
            from_dir=album, max_photos=max_photos, app_cfg=cfg,
        )
        elapsed = time.perf_counter() - t0
    stats = res.stats or {}
    return {
        "tag": tag,
        "elapsedSec": round(elapsed, 1),
        "added": res.added,
        "perPhotoSec": round(elapsed / max(1, res.added), 2),
        "workers": stats.get("ingestWorkers"),
        "fallback": stats.get("ingestParallelFallback"),
        "elapsedMs": stats.get("elapsedMs"),
    }


def main() -> None:
    album = Path(sys.argv[1])
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    trips_root = Path("trips")
    for tag, par, w in [("serial", False, 1), ("par4", True, 4), ("par8", True, 8)]:
        r = run_once(album, trips_root, tag, parallel=par, workers=w, max_photos=n)
        print(json.dumps(r, ensure_ascii=False))


if __name__ == "__main__":
    main()
