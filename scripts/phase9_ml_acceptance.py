#!/usr/bin/env python3
"""AC-P9-ML-02～04 · optional GPU/pyiqa acceptance (W2).

Usage:
  pip install -e ".[cull-ml]"
  python scripts/phase9_ml_acceptance.py --write docs/acceptance-records/phase9-ml-acceptance.json

Skips gracefully when pyiqa or CUDA is unavailable (records status=skipped).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.config import CullConfig
from travelogue.curation.photo_cull import run_photo_cull
from travelogue.curation.photo_cull_ml import pyiqa_available, resolve_effective_mode


def _synthetic_assets(n: int) -> list[dict]:
    assets: list[dict] = []
    for i in range(n):
        assets.append(
            {
                "id": f"a{i:04d}",
                "type": "image",
                "mediaClass": "photo",
                "quality": {"sharpness": 50.0 + float(i % 40)},
                "layoutEligible": True,
            }
        )
    return assets


def _keep_ratio(assets: list[dict]) -> float:
    eligible = sum(1 for a in assets if a.get("layoutEligible", True))
    return eligible / len(assets) if assets else 1.0


def run_ml_acceptance(*, n_assets: int = 100, bench_n: int = 250) -> dict:
    out: dict = {
        "schemaVersion": "1",
        "phase": "P9-QualityGate-W2",
        "recordedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
            "+00:00", "Z"
        ),
        "pyiqaAvailable": pyiqa_available(),
    }
    if not pyiqa_available():
        out["status"] = "skipped"
        out["reason"] = "pyiqa not installed; pip install -e '.[cull-ml]'"
        return out

    try:
        import torch

        out["cudaAvailable"] = bool(torch.cuda.is_available())
    except ImportError:
        out["cudaAvailable"] = False

    ml_cfg = CullConfig(mode="ml", min_keep=15, keep_ratio_floor=0.90)
    rules_cfg = CullConfig(mode="rules", min_keep=15, keep_ratio_floor=0.90)
    effective = resolve_effective_mode(ml_cfg)
    out["effectiveMode"] = effective

    if effective != "ml":
        out["status"] = "skipped"
        out["reason"] = "resolve_effective_mode != ml (no GPU or allow_cpu_ml=false)"
        return out

    base = _synthetic_assets(n_assets)
    rules_assets = [dict(a) for a in base]
    ml_assets = [dict(a) for a in base]

    rules_summary = run_photo_cull(rules_assets, cfg=rules_cfg)
    ml_summary = run_photo_cull(ml_assets, cfg=ml_cfg)

    rules_ratio = _keep_ratio(rules_assets)
    ml_ratio = _keep_ratio(ml_assets)
    out["compare"] = {
        "nAssets": n_assets,
        "rulesKeepRatio": round(rules_ratio, 4),
        "mlKeepRatio": round(ml_ratio, 4),
        "floorDelta": round(ml_ratio - rules_ratio, 4),
        "acP9Ml02Pass": ml_ratio >= rules_ratio - 0.02,
        "rulesSummary": {
            "mode": rules_summary.get("mode"),
            "layoutEligibleCount": rules_summary.get("layoutEligibleCount"),
        },
        "mlSummary": {
            "mode": ml_summary.get("mode"),
            "layoutEligibleCount": ml_summary.get("layoutEligibleCount"),
        },
    }

    bench_assets = _synthetic_assets(bench_n)
    t0 = time.monotonic()
    run_photo_cull(bench_assets, cfg=ml_cfg)
    elapsed_s = time.monotonic() - t0
    out["benchmark"] = {
        "nAssets": bench_n,
        "elapsedSeconds": round(elapsed_s, 2),
        "acP9Ml04Pass": elapsed_s <= 90.0,
    }
    out["status"] = "passed" if out["compare"]["acP9Ml02Pass"] and out["benchmark"]["acP9Ml04Pass"] else "failed"
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 9 W2 ML acceptance")
    parser.add_argument("--write", type=Path, help="Write JSON record")
    parser.add_argument("--n", type=int, default=100, help="Compare fixture size")
    parser.add_argument("--bench", type=int, default=250, help="Benchmark asset count")
    args = parser.parse_args()

    record = run_ml_acceptance(n_assets=args.n, bench_n=args.bench)
    text = json.dumps(record, ensure_ascii=False, indent=2)
    print(text)

    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote {args.write}", file=sys.stderr)

    if record.get("status") == "skipped":
        return 0
    return 0 if record.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
