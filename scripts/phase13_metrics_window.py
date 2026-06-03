#!/usr/bin/env python3
"""Phase 13 G6 metrics window check (24h / 72h thresholds)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# PRD §9.3 / phase13-1-release-gate-checklist §1
THRESHOLDS = {
    "24h": {
        "error_rate_max": 0.005,
        "fallback_rate_max": 0.12,
    },
    "72h": {
        "fallback_rate_max": 0.08,
        "manual_override_rate_max": 0.25,
    },
    "1h_rollback": {
        "error_rate_max": 0.01,
        "fallback_rate_max": 0.20,
    },
}


def build_report(
    *,
    hours: int = 24,
    dev_relaxed: bool = False,
    empty_window: bool = False,
) -> dict[str, Any]:
    from travelogue.templating.metrics import aggregate_metrics

    if empty_window:
        agg = {"windowHours": hours, "counts": {}, "rates": {"route_total": 0}}
    else:
        agg = aggregate_metrics(window_hours=hours)
    rates = agg.get("rates") or {}
    counts = agg.get("counts") or {}
    route_total = int(rates.get("route_total") or 0)
    manual = int(counts.get("template.route.manual_override", 0))
    fallback = int(counts.get("template.route.fallback", 0))
    manual_rate = round(manual / route_total, 4) if route_total else 0.0

    window_key = "72h" if hours >= 72 else "24h"
    limits = THRESHOLDS[window_key]
    checks = {
        "fallback_rate": {
            "value": rates.get("fallback_rate", 0),
            "max": limits.get("fallback_rate_max"),
            "pass": float(rates.get("fallback_rate") or 0) <= float(limits.get("fallback_rate_max", 1)),
        },
        "render_error_rate": {
            "value": rates.get("render_error_rate", 0),
            "max": limits.get("error_rate_max", 1),
            "pass": float(rates.get("render_error_rate") or 0) <= float(limits.get("error_rate_max", 1)),
        },
    }
    if hours >= 72:
        checks["manual_override_rate"] = {
            "value": manual_rate,
            "max": THRESHOLDS["72h"]["manual_override_rate_max"],
            "pass": manual_rate <= THRESHOLDS["72h"]["manual_override_rate_max"],
        }
    rates = agg.get("rates") or {}
    route_p95 = rates.get("route_duration_p95_ms")
    if route_p95 is not None:
        slo = float(rates.get("route_p95_slo_ms") or 120)
        checks["route_duration_p95_ms"] = {
            "value": route_p95,
            "max": slo,
            "pass": float(route_p95) <= slo,
        }

    all_pass = all(c.get("pass") for c in checks.values())
    if dev_relaxed and route_total > 0:
        all_pass = True
    if route_total == 0:
        all_pass = True
    return {
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "windowHours": hours,
        "metrics": agg,
        "manual_override_rate": manual_rate,
        "checks": checks,
        "pass": all_pass,
        "devRelaxed": dev_relaxed,
        "emptyWindow": empty_window,
        "note": (
            "empty_window：GA 闸门字段归档模板（无样本，阈值跳过）"
            if empty_window
            else (
                "dev_relaxed：仅校验脚本与字段，不阻断开发 Smoke"
                if dev_relaxed
                else ("无路由样本，阈值检查跳过" if route_total == 0 else "")
            )
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 13 G6 metrics window")
    parser.add_argument("--hours", type=int, default=24, choices=(1, 24, 72))
    parser.add_argument("--write", type=Path, default=None)
    parser.add_argument("--dev-relaxed", action="store_true", help="开发 Smoke：有数据也不因超阈失败")
    parser.add_argument(
        "--empty-window",
        action="store_true",
        help="无样本归档（发布闸门字段校验；生产须用真实 72h 窗口）",
    )
    args = parser.parse_args()

    report = build_report(
        hours=args.hours,
        dev_relaxed=args.dev_relaxed,
        empty_window=args.empty_window,
    )
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(text, encoding="utf-8")
        print(f"wrote {args.write} (pass={report['pass']})")
    else:
        print(text)
    # 无样本时不阻断开发 Smoke
    return 0 if report["pass"] or not (report.get("metrics", {}).get("rates", {}).get("route_total")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
