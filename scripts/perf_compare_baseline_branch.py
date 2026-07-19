# -*- coding: utf-8 -*-
"""Compare end-to-end trip generation: pre-PPF baseline worktree vs current branch.

Usage:
  python scripts/perf_compare_baseline_branch.py "D:/Photos/album" 48
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = Path(r"C:\Users\xiafe\Projects\travelogue-ppf-baseline")

_RUNNER = r'''
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import shutil
import sys
import time
from dataclasses import replace
from pathlib import Path


def main() -> None:
    repo = Path(sys.argv[1]).resolve()
    album = Path(sys.argv[2]).resolve()
    max_photos = int(sys.argv[3])
    slug = sys.argv[4]
    mode = sys.argv[5]  # baseline | candidate
    trips_root = Path(sys.argv[6]).resolve()
    report_path = Path(sys.argv[7]).resolve()
    config_path = Path(sys.argv[8]).resolve()

    sys.path.insert(0, str(repo))

    from travelogue.config import app_config_scope, load_config
    from travelogue.orchestrator.run import run_trip
    from travelogue.services.trip_factory import create_trip

    trip_dir = trips_root / slug
    if trip_dir.exists():
        shutil.rmtree(trip_dir, ignore_errors=True)
        if trip_dir.exists():
            shutil.rmtree(trip_dir)

    cfg = load_config(config_path)
    ingest_kw = dict(max_photos=max_photos, detect_faces=True)
    pipe_kw = dict(parallel_ingest=True, parallel_ingest_workers=0, parallel_embed=False)
    if mode == "baseline":
        ingest_kw.update(webp_method=4, face_detect_max_edge=0)
    else:
        ingest_kw.update(webp_method=2, face_detect_max_edge=1024)
        if hasattr(cfg.pipeline, "deferred_derivatives"):
            pipe_kw["deferred_derivatives"] = True
        if hasattr(cfg.ingest, "webp_ingest_widths"):
            ingest_kw["webp_ingest_widths"] = (800, 1600)
        if hasattr(cfg.ingest, "webp_pyramid"):
            ingest_kw["webp_pyramid"] = False

    cfg = replace(
        cfg,
        ingest=replace(cfg.ingest, **ingest_kw),
        pipeline=replace(cfg.pipeline, **pipe_kw),
        clustering=replace(cfg.clustering, enabled="false"),
    )

    with app_config_scope(cfg):
        trip_json = create_trip(slug, trips_root, title=slug, place="perf", cfg=cfg)
        t0 = time.perf_counter()
        result = run_trip(
            trip_json,
            from_stage="ingest",
            until="rendered",
            album_dir=album,
            skip_locked=False,
            validate=False,
            cfg=cfg,
            narrate_provider="stub",
        )
        elapsed = time.perf_counter() - t0

    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    timings = (trip.get("pipeline") or {}).get("timings") or {}
    report = {
        "mode": mode,
        "repo": str(repo),
        "slug": slug,
        "stages": list(result.stages),
        "elapsedSec": round(elapsed, 1),
        "assetCount": len(trip.get("assets") or []),
        "timings": {
            k: timings.get(k)
            for k in (
                "ingestMs",
                "ingestWorkers",
                "ingestWorkersDownscaled",
                "curateMs",
                "materializeMs",
                "narrateMs",
                "renderMs",
                "nimaWarmHits",
                "nimaWarmMisses",
                "derivativesOnDemandCount",
            )
        },
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("OK", mode, report["elapsedSec"], flush=True)


if __name__ == "__main__":
    main()
'''


def _minimal_config_yaml(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "vision:",
                "  enabled: false",
                "clustering:",
                "  enabled: false",
                "pipeline:",
                "  parallel_ingest: true",
                "  parallel_ingest_workers: 0",
                "  parallel_embed: false",
                "llm:",
                "  narrate_provider: stub",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _run_one(
    *,
    repo: Path,
    album: Path,
    max_photos: int,
    mode: str,
    trips_root: Path,
) -> dict:
    slug = f"perf-cmp-{mode}-{uuid.uuid4().hex[:8]}"
    runner = trips_root / f"_runner_{mode}.py"
    runner.write_text(_RUNNER, encoding="utf-8")
    report_path = trips_root / f"report_{mode}.json"
    config_path = trips_root / f"config_{mode}.yaml"
    _minimal_config_yaml(config_path)
    cmd = [
        sys.executable,
        str(runner),
        str(repo),
        str(album),
        str(max_photos),
        slug,
        mode,
        str(trips_root),
        str(report_path),
        str(config_path),
    ]
    print(f"\n=== RUN {mode} ===\nrepo={repo}\n", flush=True)
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, cwd=str(repo))
    wall = time.perf_counter() - t0
    if proc.returncode != 0 or not report_path.is_file():
        raise SystemExit(f"{mode} failed with code {proc.returncode}")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["wallClockSec"] = round(wall, 1)
    return report


def main() -> None:
    album = Path(sys.argv[1] if len(sys.argv) > 1 else r"D:\Photos\仙本那精选全集2")
    max_photos = int(sys.argv[2]) if len(sys.argv) > 2 else 48
    if not album.is_dir():
        raise SystemExit(f"album not found: {album}")
    if not BASELINE.is_dir():
        raise SystemExit(f"baseline worktree missing: {BASELINE}")

    trips_root = Path(tempfile.mkdtemp(prefix="ppf-compare-"))
    baseline = _run_one(
        repo=BASELINE,
        album=album,
        max_photos=max_photos,
        mode="baseline",
        trips_root=trips_root,
    )
    candidate = _run_one(
        repo=ROOT,
        album=album,
        max_photos=max_photos,
        mode="candidate",
        trips_root=trips_root,
    )

    b_sec = float(baseline["elapsedSec"])
    c_sec = float(candidate["elapsedSec"])
    speedup = (b_sec / c_sec) if c_sec > 0 else None
    summary = {
        "album": str(album),
        "maxPhotos": max_photos,
        "baselineCommit": "8f37a1f (pre Pipeline Perf V1)",
        "candidateBranch": "feat/pipeline-perf-v1",
        "baseline": baseline,
        "candidate": candidate,
        "deltaSec": round(b_sec - c_sec, 1),
        "speedupX": round(speedup, 2) if speedup else None,
        "fasterPct": round((1 - c_sec / b_sec) * 100, 1) if b_sec > 0 else None,
        "tripsRoot": str(trips_root),
    }
    out = ROOT / "docs" / "acceptance-records" / "pipeline-perf-v1-compare-latest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nWrote {out}", flush=True)


if __name__ == "__main__":
    main()
