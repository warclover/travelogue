"""PF-P3-03 · Studio pipeline end-to-end bench (ingest → preview · P3-Full).

Usage:
  python scripts/phase3_e2e_bench.py
  python scripts/phase3_e2e_bench.py --assets 150 --vision
  python scripts/phase3_e2e_bench.py --record-real trips/linzhi
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def build_album(album_dir: Path, count: int) -> None:
    from PIL import Image

    album_dir.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        path = album_dir / f"photo_{i:04d}.jpg"
        if path.is_file():
            continue
        color = (40 + (i * 17) % 180, 60 + (i * 11) % 120, 80 + (i * 7) % 100)
        Image.new("RGB", (1200, 900), color).save(path, quality=95)


def run_bench(*, assets: int, vision: bool, work_dir: Path) -> dict:
    from travelogue.config import AppConfig, ClusteringConfig, VisionConfig
    from travelogue.web.studio_pipeline import run_studio_pipeline

    album_dir = work_dir / "album"
    trips_dir = work_dir / "trips"
    build_album(album_dir, assets)

    cfg = AppConfig(
        clustering=ClusteringConfig(enabled="true", deterministic=True),
        vision=VisionConfig(enabled="true" if vision else "false"),
    )
    stages: list[dict] = []

    def progress(stage: str, index: int, hint: str) -> None:
        stages.append({"stage": stage, "stageIndex": index, "stageHint": hint})

    t0 = time.perf_counter()
    result = run_studio_pipeline(
        album_dir,
        trips_dir=trips_dir,
        title="E2E验收",
        place="测试",
        force=True,
        dedupe=False,
        app_config=cfg,
        progress=progress,
    )
    elapsed = time.perf_counter() - t0
    trip = json.loads(result.trip_json.read_text(encoding="utf-8"))
    clustering = (trip.get("curation") or {}).get("clustering") or {}
    budget_sec = 20 * 60
    return {
        "benchKind": "studio_pipeline_e2e",
        "photoCount": result.photo_count,
        "visionEnabled": vision,
        "elapsedSec": round(elapsed, 2),
        "budgetSec": budget_sec,
        "withinBudget": elapsed <= budget_sec,
        "tripId": result.trip_id,
        "previewArtifacts": {
            "indexHtml": (result.trip_dir / "index.html").is_file(),
            "previewJpg": (result.trip_dir / "preview.jpg").is_file(),
        },
        "clustering": {
            "segmentMode": clustering.get("segmentMode"),
            "clusterCount": len(clustering.get("clusters") or []),
            "visionSource": (clustering.get("vision") or {}).get("source"),
        },
        "clusterNotice": result.cluster_notice or "",
        "stageTrace": stages,
    }


def record_real_trip(trip_dir: Path) -> dict | None:
    trip_json = trip_dir / "trip.json"
    if not trip_json.is_file():
        return None
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    assets = trip.get("assets") or []
    gps = sum(1 for a in assets if (a.get("geo") or {}).get("lat") is not None)
    clustering = (trip.get("curation") or {}).get("clustering") or {}
    return {
        "tripId": trip.get("tripId") or trip_dir.name,
        "assetCount": len(assets),
        "gpsAssetCount": gps,
        "hasClustering": bool(clustering),
        "segmentMode": clustering.get("segmentMode"),
        "note": "Existing real trip reference · re-run pipeline separately for timed PF-P3-03",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 3 PF-P3-03 e2e pipeline bench")
    parser.add_argument("--assets", type=int, default=150)
    parser.add_argument("--vision", action="store_true", default=True)
    parser.add_argument("--no-vision", action="store_false", dest="vision")
    parser.add_argument("--work-dir", type=Path, default=ROOT / ".cache" / "e2e-bench")
    parser.add_argument(
        "--json-out",
        type=Path,
        default=ROOT / "docs" / "acceptance-records" / "phase3-pf-p3-03-e2e.json",
    )
    parser.add_argument(
        "--record-real",
        type=Path,
        action="append",
        default=[],
        help="Attach metadata for real trips (e.g. trips/linzhi)",
    )
    args = parser.parse_args()

    row = run_bench(assets=args.assets, vision=args.vision, work_dir=args.work_dir)
    real_refs = []
    for path in args.record_real:
        ref = record_real_trip(path.resolve())
        if ref:
            real_refs.append(ref)
    payload = {
        "recordId": "phase3-pf-p3-03-e2e",
        "phase": "M13",
        "date": "2026-05-28",
        "gate": "PF-P3-03",
        "syntheticRun": row,
        "realTripReferences": real_refs,
        "pass": row["withinBudget"] and row["previewArtifacts"]["indexHtml"],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {args.json_out}")
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
