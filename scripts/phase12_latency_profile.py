#!/usr/bin/env python3
"""Phase 12 CPU cull latency profile (P50/P95 on synthetic assets)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.config import CullConfig
from travelogue.curation.photo_cull import run_photo_cull


def _synthetic_assets(n: int) -> list[dict]:
    assets: list[dict] = []
    for i in range(n):
        face_ratio = 0.22 if i % 3 == 0 else 0.05 if i % 3 == 1 else 0.14
        assets.append(
            {
                "id": f"lat-{i:03d}",
                "type": "image",
                "mediaClass": "photo",
                "layoutEligible": True,
                "quality": {"sharpness": 40.0 + float(i % 35), "faceRatio": face_ratio},
            }
        )
    return assets


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, int(round((pct / 100.0) * (len(ordered) - 1)))))
    return ordered[idx]


def profile_cull(*, sizes: list[int], repeats: int) -> dict[str, Any]:
    cfg = CullConfig(mode="rules", min_keep=10, keep_ratio_floor=0.7)
    rows: list[dict[str, Any]] = []
    for n in sizes:
        samples_ms: list[float] = []
        reported_cpu: list[float] = []
        for _ in range(repeats):
            assets = _synthetic_assets(n)
            t0 = time.perf_counter()
            summary = run_photo_cull(assets, cfg=cfg)
            wall_ms = (time.perf_counter() - t0) * 1000.0
            samples_ms.append(wall_ms)
            reported_cpu.append(float(summary.get("cpuMs") or wall_ms))
        rows.append(
            {
                "assets": n,
                "repeats": repeats,
                "wallMs": {
                    "p50": round(_percentile(samples_ms, 50), 2),
                    "p95": round(_percentile(samples_ms, 95), 2),
                    "avg": round(mean(samples_ms), 2),
                },
                "reportedCpuMs": {
                    "p50": round(_percentile(reported_cpu, 50), 2),
                    "p95": round(_percentile(reported_cpu, 95), 2),
                    "avg": round(mean(reported_cpu), 2),
                },
            }
        )
    return {"sizes": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 12 cull latency profile")
    parser.add_argument("--sizes", type=str, default="30,60,120")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument(
        "--write",
        type=Path,
        default=ROOT / "docs" / "acceptance-records" / "phase12-latency.json",
    )
    args = parser.parse_args()
    sizes = [int(x.strip()) for x in args.sizes.split(",") if x.strip()]
    record = {
        "schemaVersion": "1",
        "phase": "P12-LatencyProfile",
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mode": "rules",
        "profile": profile_cull(sizes=sizes, repeats=max(1, args.repeats)),
    }
    args.write.parent.mkdir(parents=True, exist_ok=True)
    args.write.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"write": str(args.write.resolve())}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
