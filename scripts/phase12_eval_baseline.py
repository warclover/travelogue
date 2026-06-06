#!/usr/bin/env python3
"""Phase 12 offline eval baseline (L1/L2/L3 cull telemetry + layout scoring smoke)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.config import CullConfig
from travelogue.curation.layout_scoring import score_category_coherence
from travelogue.curation.photo_cull import run_photo_cull
from travelogue.curation.subject_tagging import (
    refresh_semantic_tag_for_asset,
    semantic_category_for_asset,
)

DEFAULT_GOLDEN = ROOT / "docs" / "acceptance-records" / "phase9-golden-cull-signoff.json"


def _synthetic_assets(n: int) -> list[dict]:
    assets: list[dict] = []
    branches = (
        {"quality": {"faceRatio": 0.25, "sharpness": 72.0}, "subjectClass": "person"},
        {"quality": {"faceRatio": 0.02, "sharpness": 68.0}, "subjectClass": "landscape"},
        {"quality": {"faceRatio": 0.14, "sharpness": 55.0}, "subjectClass": "food"},
    )
    for i in range(n):
        base = dict(branches[i % len(branches)])
        asset = {
            "id": f"p12-{i:03d}",
            "type": "image",
            "mediaClass": "photo",
            "layoutEligible": True,
            **base,
        }
        refresh_semantic_tag_for_asset(asset)
        assets.append(asset)
    return assets


def _run_cull_smoke(n_assets: int = 60) -> dict[str, Any]:
    assets = _synthetic_assets(n_assets)
    cfg = CullConfig(mode="rules", min_keep=12, keep_ratio_floor=0.75)
    summary = run_photo_cull(assets, cfg=cfg)
    eligible = sum(1 for a in assets if a.get("layoutEligible", True))
    return {
        "assets": n_assets,
        "layoutEligible": eligible,
        "keepRatio": round(eligible / n_assets, 4) if n_assets else 0.0,
        "cullSummary": summary,
        "assetsMap": {a["id"]: a for a in assets},
    }


def _aggregate_golden(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    runs = data.get("runs") or []
    l1: list[float] = []
    l2: list[float] = []
    l3: list[float] = []
    cpu_ms: list[float] = []
    for run in runs:
        metrics = run.get("metrics") or {}
        l1.append(float(metrics.get("mlFallbackRateL1") or 0.0))
        l2.append(float(metrics.get("branchFallbackRateL2") or 0.0))
        l3.append(float(metrics.get("failOpenRateL3") or 0.0))
        cpu_ms.append(float(metrics.get("cpuMs") or metrics.get("ingestMs") or 0.0))
    if not runs:
        return None
    return {
        "tripCount": len(runs),
        "l1_ml_fallback_rate_avg": round(mean(l1), 4) if l1 else 0.0,
        "l2_branch_fallback_rate_avg": round(mean(l2), 4) if l2 else 0.0,
        "l3_fail_open_rate_avg": round(mean(l3), 4) if l3 else 0.0,
        "cpu_ms_avg": round(mean(cpu_ms), 2) if cpu_ms else 0.0,
    }


def build_phase12_eval_baseline(*, golden_path: Path, smoke_n: int) -> dict[str, Any]:
    smoke = _run_cull_smoke(smoke_n)
    summary = smoke.get("cullSummary") or {}
    assets_map = smoke["assetsMap"]
    same_ids = [f"p12-{i:03d}" for i in range(0, min(smoke_n, 9), 3)]
    mixed_ids = [f"p12-{i:03d}" for i in range(min(3, smoke_n))]
    coherence_same = score_category_coherence(same_ids, assets_map)
    coherence_mixed = score_category_coherence(mixed_ids, assets_map)

    record: dict[str, Any] = {
        "schemaVersion": "1",
        "phase": "P12-SilentCullEnhancement",
        "generatedAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "source": {
            "goldenSignoff": str(
                golden_path.relative_to(ROOT) if golden_path.is_relative_to(ROOT) else golden_path
            ),
        },
        "syntheticCullSmoke": {
            "assets": smoke["assets"],
            "layoutEligible": smoke["layoutEligible"],
            "keepRatio": smoke["keepRatio"],
            "mlFallbackRateL1": summary.get("mlFallbackRateL1"),
            "branchFallbackRateL2": summary.get("branchFallbackRateL2"),
            "failOpenRateL3": summary.get("failOpenRateL3"),
            "branchPortraitRatio": summary.get("branchPortraitRatio"),
            "branchLandscapeRatio": summary.get("branchLandscapeRatio"),
            "branchGrayRatio": summary.get("branchGrayRatio"),
            "cpuMs": summary.get("cpuMs"),
        },
        "categoryCoherence": {
            "sameCategoryScore": coherence_same,
            "mixedCategoryScore": coherence_mixed,
            "semanticCategoriesSample": sorted(
                {semantic_category_for_asset(assets_map[aid]) for aid in mixed_ids}
            ),
        },
        "gate": {
            "ac_p12_03_semantic_stable": coherence_same >= coherence_mixed,
            "ac_p12_04_coherence_observable": coherence_same >= 0.99,
        },
    }
    golden_agg = _aggregate_golden(golden_path)
    if golden_agg:
        record["goldenSignoffAggregate"] = golden_agg
    record["passed"] = bool(record["gate"]["ac_p12_03_semantic_stable"])
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 12 eval baseline JSON")
    parser.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN)
    parser.add_argument("--smoke-n", type=int, default=60)
    parser.add_argument(
        "--write",
        type=Path,
        default=ROOT / "docs" / "acceptance-records" / "phase12-eval-baseline.json",
    )
    args = parser.parse_args()
    record = build_phase12_eval_baseline(golden_path=args.golden, smoke_n=args.smoke_n)
    args.write.parent.mkdir(parents=True, exist_ok=True)
    args.write.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": record["passed"], "write": str(args.write.resolve())}))
    return 0 if record["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
