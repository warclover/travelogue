#!/usr/bin/env python3
"""Build Phase 9 offline evaluation baseline from acceptance records."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GOLDEN = ROOT / "docs/acceptance-records/phase9-golden-cull-signoff.json"
DEFAULT_QUALITY = ROOT / "docs/acceptance-records/phase9-quality-gate.json"

_CULL_COUNT_RE = re.compile(r"经挑选\s*(\d+)")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_cull_count(user_line: str) -> int | None:
    match = _CULL_COUNT_RE.search(user_line)
    if not match:
        return None
    return _safe_int(match.group(1), default=0)


def _build_phase92_recommendations(
    *,
    cull_ratios: list[float],
    final_ratios: list[float],
    excluded_by_reason: dict[str, int],
    fail_open_rate: float,
    quality_status: dict[str, Any] | None,
) -> dict[str, Any]:
    total_excluded = sum(int(v) for v in excluded_by_reason.values())
    quota_ratio = (
        (excluded_by_reason.get("cull_quota", 0) / total_excluded)
        if total_excluded > 0
        else 0.0
    )
    blur_ratio = (
        (excluded_by_reason.get("blur", 0) / total_excluded) if total_excluded > 0 else 0.0
    )
    avg_cull = mean(cull_ratios) if cull_ratios else 0.0
    avg_final = mean(final_ratios) if final_ratios else 0.0
    low_res_drop = max(0.0, avg_cull - avg_final)
    w2_status = str((quality_status or {}).get("w2Status") or "").lower()
    ml_pending = w2_status in {"partial", "pending", "todo"}

    m4_enable = blur_ratio >= 0.15
    m4_samples = 4 if m4_enable else 3
    if low_res_drop >= 0.02:
        m4_samples = max(m4_samples, 4)

    if quota_ratio >= 0.75:
        m5_penalty = 0.08
    elif quota_ratio >= 0.50:
        m5_penalty = 0.06
    else:
        m5_penalty = 0.04
    if low_res_drop >= 0.03:
        m5_penalty = max(0.04, m5_penalty - 0.02)

    recommendations: dict[str, Any] = {
        "recommendedConfig": {
            "cull": {
                "bucketed_blur_thresholds": m4_enable,
                "bucketed_blur_min_samples": m4_samples,
                "enable_cull_explain": True,
                "score": {
                    "duplicate_group_penalty": round(m5_penalty, 3),
                },
            }
        },
        "m4_bucketed_blur_thresholds": {
            "enabled": m4_enable,
            "bucketed_blur_min_samples": m4_samples,
            "reason": (
                "blur 占比较高，建议开启按桶阈值"
                if m4_enable
                else "blur 占比低，先保持关闭，待样本规模增大后再灰度"
            ),
        },
        "m5_duplicate_group_penalty": {
            "value": round(m5_penalty, 3),
            "reason": (
                "cull_quota 占比较高，建议启用轻度重复惩罚提升多样性"
                if quota_ratio >= 0.5
                else "当前配额淘汰占比中等，建议保守惩罚"
            ),
        },
        "m6_cull_explain": {
            "enabled": True,
            "reason": "建议默认开启 explain，便于验收复盘与线上定位",
        },
        "m7_ml_cache": {
            "enabled": True,
            "warmupRecommended": ml_pending,
            "reason": (
                "ML 验收仍部分 pending，建议保留缓存并在回归集预热"
                if ml_pending
                else "ML 路径稳定，建议保持缓存开启以降低重复推理耗时"
            ),
        },
        "signals": {
            "excludedTotal": total_excluded,
            "cullQuotaRatio": round(quota_ratio, 4),
            "blurRatio": round(blur_ratio, 4),
            "avgCullRatio": round(avg_cull, 4),
            "avgFinalRatio": round(avg_final, 4),
            "lowResDrop": round(low_res_drop, 4),
            "failOpenRate": round(fail_open_rate, 4),
        },
    }
    return recommendations


def build_phase9_eval_baseline(
    *,
    golden_path: Path,
    quality_path: Path | None = None,
) -> dict[str, Any]:
    golden = _read_json(golden_path)
    runs = golden.get("runs") or []
    per_trip: list[dict[str, Any]] = []
    cull_ratios: list[float] = []
    final_ratios: list[float] = []
    ingest_ms: list[float] = []
    excluded_by_reason: dict[str, int] = {}
    branch_fallback_by_reason_l2: dict[str, int] = {}
    fail_open_count = 0
    l1_fallback_rates: list[float] = []
    l2_fallback_rates: list[float] = []
    l3_fail_open_rates: list[float] = []

    for run in runs:
        metrics = run.get("metrics") or {}
        scanned = _safe_int(metrics.get("scanned"), 0)
        user_line = str(metrics.get("cullUserLine") or "")
        cull_eligible = _parse_cull_count(user_line)
        if cull_eligible is None:
            cull_eligible = _safe_int(metrics.get("layoutEligibleCount"), 0)
        cull_ratio = (cull_eligible / scanned) if scanned > 0 else 0.0
        final_ratio = _safe_float(metrics.get("nonFeaturedKeepRatio"), 0.0)
        cull_ratios.append(cull_ratio)
        final_ratios.append(final_ratio)
        ingest_ms.append(_safe_float(metrics.get("ingestMs"), 0.0))

        by_reason = metrics.get("excludedByReason") or {}
        if isinstance(by_reason, dict):
            for reason, count in by_reason.items():
                excluded_by_reason[str(reason)] = (
                    excluded_by_reason.get(str(reason), 0) + _safe_int(count, 0)
                )
        l2_by_reason = metrics.get("branchFallbackByReasonL2") or {}
        if isinstance(l2_by_reason, dict):
            for reason, count in l2_by_reason.items():
                branch_fallback_by_reason_l2[str(reason)] = (
                    branch_fallback_by_reason_l2.get(str(reason), 0) + _safe_int(count, 0)
                )

        l1_fallback_rates.append(_safe_float(metrics.get("mlFallbackRateL1"), 0.0))
        l2_fallback_rates.append(_safe_float(metrics.get("branchFallbackRateL2"), 0.0))
        l3_fail_open_rates.append(_safe_float(metrics.get("failOpenRateL3"), 0.0))

        fail_open = (
            bool(metrics.get("failOpen"))
            or bool(metrics.get("error"))
            or bool(metrics.get("cullError"))
        )
        if fail_open:
            fail_open_count += 1

        per_trip.append(
            {
                "tripId": str(run.get("tripId") or ""),
                "scanned": scanned,
                "cull_keep_ratio_non_featured": round(cull_ratio, 4),
                "final_keep_ratio_non_featured": round(final_ratio, 4),
                "ingest_elapsed_ms": round(_safe_float(metrics.get("ingestMs"), 0.0), 2),
                "fail_open": fail_open,
            }
        )

    out: dict[str, Any] = {
        "schemaVersion": "1",
        "phase": "P9.2-offline-baseline",
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": {
            "goldenSignoff": str(golden_path.relative_to(ROOT) if golden_path.is_relative_to(ROOT) else golden_path),
            "qualityGate": str(quality_path.relative_to(ROOT) if quality_path and quality_path.is_relative_to(ROOT) else quality_path) if quality_path else None,
        },
        "tripCount": len(per_trip),
        "cull_keep_ratio_non_featured": {
            "avg": round(mean(cull_ratios), 4) if cull_ratios else 0.0,
            "min": round(min(cull_ratios), 4) if cull_ratios else 0.0,
            "max": round(max(cull_ratios), 4) if cull_ratios else 0.0,
        },
        "final_keep_ratio_non_featured": {
            "avg": round(mean(final_ratios), 4) if final_ratios else 0.0,
            "min": round(min(final_ratios), 4) if final_ratios else 0.0,
            "max": round(max(final_ratios), 4) if final_ratios else 0.0,
        },
        "excluded_by_reason": dict(sorted(excluded_by_reason.items())),
        "l1_ml_fallback_rate": {
            "avg": round(mean(l1_fallback_rates), 4) if l1_fallback_rates else 0.0,
            "max": round(max(l1_fallback_rates), 4) if l1_fallback_rates else 0.0,
        },
        "l2_branch_fallback_rate": {
            "avg": round(mean(l2_fallback_rates), 4) if l2_fallback_rates else 0.0,
            "max": round(max(l2_fallback_rates), 4) if l2_fallback_rates else 0.0,
        },
        "l2_branch_fallback_by_reason": dict(sorted(branch_fallback_by_reason_l2.items())),
        "l3_fail_open_rate": {
            "avg": round(mean(l3_fail_open_rates), 4) if l3_fail_open_rates else 0.0,
            "max": round(max(l3_fail_open_rates), 4) if l3_fail_open_rates else 0.0,
        },
        "fail_open_rate": round((fail_open_count / len(per_trip)), 4) if per_trip else 0.0,
        "ingest_elapsed_ms": {
            "avg": round(mean(ingest_ms), 2) if ingest_ms else 0.0,
            "min": round(min(ingest_ms), 2) if ingest_ms else 0.0,
            "max": round(max(ingest_ms), 2) if ingest_ms else 0.0,
        },
        "perTrip": per_trip,
    }

    quality_status: dict[str, Any] | None = None
    if quality_path and quality_path.is_file():
        quality = _read_json(quality_path)
        quality_status = {
            "w1Status": quality.get("w1Status"),
            "w2Status": quality.get("w2Status"),
            "w3Status": quality.get("w3Status"),
        }
        out["qualityGateStatus"] = quality_status
    out["phase92Recommendations"] = _build_phase92_recommendations(
        cull_ratios=cull_ratios,
        final_ratios=final_ratios,
        excluded_by_reason=excluded_by_reason,
        fail_open_rate=out["fail_open_rate"],
        quality_status=quality_status,
    )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Build phase9 evaluation baseline")
    parser.add_argument(
        "--golden",
        type=Path,
        default=DEFAULT_GOLDEN,
        help="Path to phase9 golden signoff JSON",
    )
    parser.add_argument(
        "--quality",
        type=Path,
        default=DEFAULT_QUALITY,
        help="Path to phase9 quality gate JSON (optional)",
    )
    parser.add_argument(
        "--write",
        type=Path,
        default=ROOT / "docs/acceptance-records/phase9-eval-baseline.json",
        help="Write output JSON to file",
    )
    args = parser.parse_args()

    result = build_phase9_eval_baseline(
        golden_path=args.golden,
        quality_path=args.quality if args.quality and args.quality.is_file() else None,
    )
    out = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(out + "\n", encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

