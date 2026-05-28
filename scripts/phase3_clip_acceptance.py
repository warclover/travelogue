"""Real CLIP path acceptance (M13 · requires pip install -e '.[clip]')."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.config import AppConfig, ClusteringConfig, VisionConfig
from travelogue.curation.clustering import run_clustering_layer
from travelogue.vision.clip_encoder import ClipEncoder, clip_torch_available


def _write_sample_images(trip_dir: Path, n: int = 8) -> list[dict]:
    from PIL import Image

    assets: list[dict] = []
    img_dir = trip_dir / "assets" / "web"
    img_dir.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        aid = f"clip{i:02d}"
        path = img_dir / f"{aid}.jpg"
        color = ((40 + i * 25) % 255, (80 + i * 15) % 255, (120 + i * 10) % 255)
        Image.new("RGB", (224, 224), color).save(path, quality=90)
        assets.append(
            {
                "id": aid,
                "type": "image",
                "path": f"assets/web/{aid}.jpg",
                "width": 224,
                "height": 224,
                "sharpness": 0.6,
                "subjectBucket": "landscape" if i % 2 == 0 else "food",
            }
        )
    return assets


def main() -> int:
    if not clip_torch_available():
        print("SKIP: torch/open_clip not installed · pip install -e '.[clip]'")
        return 0

    trip_dir = ROOT / ".cache" / "clip-acceptance"
    trip_dir.mkdir(parents=True, exist_ok=True)
    assets = _write_sample_images(trip_dir, n=12)
    trip = {"schemaVersion": "0.2", "assets": assets, "curation": {}, "chapters": []}
    cfg = AppConfig(
        clustering=ClusteringConfig(enabled="true", force_recluster=True),
        vision=VisionConfig(enabled="true"),
    )

    enc = ClipEncoder()
    t0 = time.perf_counter()
    embed = enc.embed_assets(assets, trip_dir=trip_dir, deterministic=True)
    embed_sec = time.perf_counter() - t0

    t1 = time.perf_counter()
    result = run_clustering_layer(trip, trip_dir=trip_dir, cfg=cfg)
    cluster_sec = time.perf_counter() - t1

    clustering = (trip.get("curation") or {}).get("clustering") or {}
    row = {
        "clipAvailable": True,
        "embedSource": embed.source,
        "embedModel": embed.model,
        "vectorDim": int(embed.vectors.shape[1]) if embed.vectors.size else 0,
        "assetCount": len(assets),
        "embedSec": round(embed_sec, 3),
        "clusterSec": round(cluster_sec, 3),
        "segmentMode": result.segment_mode,
        "sceneClusterCount": result.scene_cluster_count,
        "clusterSource": (clustering.get("vision") or {}).get("source"),
        "pass": embed.source == "clip" and result.scene_cluster_count >= 0,
    }
    print(json.dumps(row, indent=2, ensure_ascii=False))

    out = ROOT / "docs" / "acceptance-records" / "phase3-m13-clip.json"
    out.write_text(json.dumps(row, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {out}")
    return 0 if row["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
