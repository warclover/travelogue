"""M13 · P3-Full clustering bench (PF-P3-01/02 · AC-P3-C05).

Usage:
  python scripts/phase3_cluster_bench.py
  python scripts/phase3_cluster_bench.py --assets 400 --vision
  python scripts/phase3_cluster_bench.py --assets 400 --geo-only
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.config import AppConfig, ClusteringConfig, VisionConfig
from travelogue.curation.clustering import run_clustering_layer
from travelogue.vision.clip_encoder import clip_torch_available


def synthetic_assets(count: int) -> list[dict]:
    assets: list[dict] = []
    cities = [
        (35.681, 139.767, "东京"),
        (35.011, 135.768, "京都"),
        (34.693, 135.502, "大阪"),
    ]
    buckets = ["landscape", "food", "street", "temple"]
    for i in range(count):
        day = 1 + (i // max(1, count // 9))
        city_idx = (i // max(1, count // 3)) % 3
        lat, lon, city = cities[city_idx]
        bucket = buckets[i % len(buckets)]
        rel = f"assets/web/b{i:04d}.jpg"
        assets.append(
            {
                "id": f"b{i:04d}",
                "type": "image",
                "sourceFile": rel,
                "displayFile": rel,
                "path": rel,
                "takenAt": f"2025-06-{day:02d}T{(8 + i % 12):02d}:00:00Z",
                "geo": {"lat": lat + (i % 5) * 0.001, "lon": lon + (i % 5) * 0.001},
                "place": {"city": city},
                "width": 1200 if i % 2 == 0 else 800,
                "height": 800 if i % 2 == 0 else 1200,
                "sharpness": 0.5 + (i % 20) * 0.01,
                "subjectBucket": bucket,
                "meanLuma": 0.4 + (i % 10) * 0.05,
            }
        )
    return assets


def prepare_synthetic_images(trip_dir: Path, assets: list[dict]) -> None:
    from PIL import Image

    for asset in assets:
        rel = asset.get("path") or asset.get("displayFile")
        if not isinstance(rel, str):
            continue
        out = trip_dir / rel.replace("/", "\\").lstrip("\\/")
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.is_file():
            continue
        seed = sum(ord(c) for c in asset["id"])
        color = (40 + seed % 180, 60 + (seed // 3) % 120, 80 + (seed // 7) % 100)
        Image.new("RGB", (224, 224), color).save(out, quality=85)


def bench(*, asset_count: int, vision: bool, geo_only: bool, work_dir: Path) -> dict:
    work_dir.mkdir(parents=True, exist_ok=True)
    warmup_dir = work_dir / "warmup"
    timed_dir = work_dir / "timed"
    assets = synthetic_assets(asset_count)
    prepare_synthetic_images(warmup_dir, assets)
    prepare_synthetic_images(timed_dir, [dict(a) for a in assets])

    vision_on = vision and not geo_only
    cfg = AppConfig(
        clustering=ClusteringConfig(enabled="true", deterministic=True),
        vision=VisionConfig(enabled="true" if vision_on else "false"),
    )
    budget_sec = 60 if geo_only else 480

    warmup_trip = {
        "schemaVersion": "0.2",
        "assets": [dict(a) for a in assets],
        "curation": {},
        "chapters": [],
    }
    run_clustering_layer(warmup_trip, trip_dir=warmup_dir, cfg=cfg)

    timed_trip = {
        "schemaVersion": "0.2",
        "assets": [dict(a) for a in assets],
        "curation": {},
        "chapters": [],
    }
    t0 = time.perf_counter()
    result = run_clustering_layer(timed_trip, trip_dir=timed_dir, cfg=cfg)
    elapsed = time.perf_counter() - t0
    clustering = (timed_trip.get("curation") or {}).get("clustering") or {}
    vision_meta = clustering.get("vision") or {}
    return {
        "benchKind": "geo_only" if geo_only else "p3_full",
        "assetCount": asset_count,
        "visionEnabled": vision_on,
        "clipAvailable": clip_torch_available(),
        "elapsedSec": round(elapsed, 2),
        "budgetSec": budget_sec,
        "withinBudget": elapsed <= budget_sec,
        "segmentMode": result.segment_mode,
        "geoEventCount": result.geo_event_count,
        "sceneClusterCount": result.scene_cluster_count,
        "embeddingSource": vision_meta.get("source"),
        "embeddingModel": vision_meta.get("model") or clustering.get("visionModel"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 3 P3-Full cluster bench")
    parser.add_argument("--assets", type=int, default=400)
    parser.add_argument("--vision", action="store_true", default=True, help="vision.enabled=true (default)")
    parser.add_argument("--no-vision", action="store_false", dest="vision")
    parser.add_argument("--geo-only", action="store_true", help="PF-P3-01 geo_events only (vision off)")
    parser.add_argument("--work-dir", type=Path, default=ROOT / ".cache" / "cluster-bench")
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Output JSON path (default: phase3-m13-bench.json or phase3-m13-bench-geo.json)",
    )
    args = parser.parse_args()

    json_out = args.json_out
    if json_out is None:
        json_out = (
            ROOT / "docs" / "acceptance-records" / "phase3-m13-bench-geo.json"
            if args.geo_only
            else ROOT / "docs" / "acceptance-records" / "phase3-m13-bench.json"
        )

    row = bench(
        asset_count=args.assets,
        vision=args.vision,
        geo_only=args.geo_only,
        work_dir=args.work_dir / ("geo" if args.geo_only else "full"),
    )
    print(json.dumps(row, indent=2))
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {json_out}")
    return 0 if row["withinBudget"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
