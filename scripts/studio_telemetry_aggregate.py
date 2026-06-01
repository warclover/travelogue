"""Studio homepage v2 telemetry aggregation (M20-i · TELEMETRY §3).

Reads the local funnel jsonl (`~/.travelogue/telemetry/studio-homepage-events.jsonl`)
and produces a `variant × event × day` summary plus a holdback funnel comparison
(v2 vs v3) for the §17.2 rollback criteria.

Pure helpers (`parse_events`, `aggregate`, `funnel_summary`, `rollback_flags`) are
import-safe for tests; CLI writes a CSV and prints a human summary.

Usage:
    python scripts/studio_telemetry_aggregate.py [--input PATH] [--out CSV]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

# §17.2 回滚阈值（同期 v2 vs v3）
ROLLBACK_THRESHOLDS = {
    "import_conversion_drop_pct": 15.0,  # import_success/import_start ↓>15%
    "cta_click_drop_pct": 20.0,  # cta_click（按 PV 归一）↓>20%
    "js_error_rate_ratio": 2.0,  # JS error rate ↑>2×
}


def _events_path() -> Path:
    # 延迟导入，避免脚本对包结构的硬依赖（仅 CLI 默认路径需要）。
    try:
        from travelogue.web.studio_homepage_telemetry import (
            studio_homepage_events_path,
        )

        return studio_homepage_events_path()
    except Exception:
        return Path.home() / ".travelogue" / "telemetry" / "studio-homepage-events.jsonl"


def parse_events(lines: Iterable[str]) -> list[dict[str, Any]]:
    """Parse jsonl lines → event dicts. Bad lines are skipped (robust to partial writes)."""
    out: list[dict[str, Any]] = []
    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            rec = json.loads(raw)
        except (ValueError, TypeError):
            continue
        if isinstance(rec, dict) and rec.get("event"):
            out.append(rec)
    return out


def _variant_of(rec: dict[str, Any]) -> str:
    meta = rec.get("meta")
    if isinstance(meta, dict):
        v = meta.get("variant")
        if v:
            return str(v)
    return "unknown"


def _day_of(rec: dict[str, Any]) -> str:
    ts = str(rec.get("ts") or "")
    return ts[:10] if len(ts) >= 10 else "unknown"


def aggregate(events: list[dict[str, Any]]) -> dict[tuple[str, str, str], int]:
    """→ {(day, variant, event): count}."""
    counts: dict[tuple[str, str, str], int] = defaultdict(int)
    for rec in events:
        counts[(_day_of(rec), _variant_of(rec), str(rec["event"]))] += 1
    return dict(counts)


@dataclass
class VariantFunnel:
    variant: str
    counts: dict[str, int] = field(default_factory=dict)

    @property
    def import_start(self) -> int:
        return self.counts.get("import_start", 0)

    @property
    def import_success(self) -> int:
        return self.counts.get("import_success", 0)

    @property
    def cta_click(self) -> int:
        return self.counts.get("cta_click", 0)

    @property
    def homepage_view(self) -> int:
        return self.counts.get("homepage_view", 0)

    @property
    def js_error(self) -> int:
        return self.counts.get("js_error", 0)

    @property
    def import_conversion(self) -> float:
        return self.import_success / self.import_start if self.import_start else 0.0

    @property
    def cta_per_view(self) -> float:
        return self.cta_click / self.homepage_view if self.homepage_view else 0.0

    @property
    def js_error_rate(self) -> float:
        return self.js_error / self.homepage_view if self.homepage_view else 0.0


def funnel_summary(events: list[dict[str, Any]]) -> dict[str, VariantFunnel]:
    """→ {variant: VariantFunnel}."""
    per: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for rec in events:
        per[_variant_of(rec)][str(rec["event"])] += 1
    return {v: VariantFunnel(v, dict(c)) for v, c in per.items()}


def rollback_flags(summary: dict[str, VariantFunnel]) -> list[str]:
    """对照 §17.2：v2 相对 v3 是否触发回滚判据。无 v2/v3 同期数据则返回提示。"""
    flags: list[str] = []
    v2 = summary.get("v2")
    v3 = summary.get("v3")
    if not v2 or not v3:
        flags.append("INSUFFICIENT_DATA: 缺少 v2/v3 同期对照，禁止仅用历史 baseline 自动回滚")
        return flags

    if v3.import_conversion > 0:
        drop = (1 - v2.import_conversion / v3.import_conversion) * 100
        if drop > ROLLBACK_THRESHOLDS["import_conversion_drop_pct"]:
            flags.append(
                f"ROLLBACK: import 转化率下降 {drop:.1f}% "
                f"(v2={v2.import_conversion:.3f} v3={v3.import_conversion:.3f})"
            )

    if v3.cta_per_view > 0:
        drop = (1 - v2.cta_per_view / v3.cta_per_view) * 100
        if drop > ROLLBACK_THRESHOLDS["cta_click_drop_pct"]:
            flags.append(
                f"ROLLBACK: cta_click/PV 下降 {drop:.1f}% "
                f"(v2={v2.cta_per_view:.3f} v3={v3.cta_per_view:.3f})"
            )

    if v3.js_error_rate > 0:
        ratio = v2.js_error_rate / v3.js_error_rate
        if ratio > ROLLBACK_THRESHOLDS["js_error_rate_ratio"]:
            flags.append(
                f"ROLLBACK: JS error rate ↑{ratio:.1f}× "
                f"(v2={v2.js_error_rate:.4f} v3={v3.js_error_rate:.4f})"
            )
    elif v2.js_error_rate > 0:
        flags.append(
            f"WARN: v3 无 JS error 基线，v2 error rate={v2.js_error_rate:.4f}"
        )

    return flags


def write_csv(agg: dict[tuple[str, str, str], int], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["date", "variant", "event", "count"])
        for (day, variant, event), count in sorted(agg.items()):
            writer.writerow([day, variant, event, count])


def _print_summary(summary: dict[str, VariantFunnel], flags: list[str]) -> None:
    print("=== Studio 首页漏斗（按 variant 汇总）===")
    for variant in sorted(summary):
        f = summary[variant]
        print(
            f"[{variant}] PV={f.homepage_view} cta={f.cta_click}"
            f" import_start={f.import_start} import_success={f.import_success}"
            f" | conv={f.import_conversion:.3f} cta/PV={f.cta_per_view:.3f}"
            f" js_err_rate={f.js_error_rate:.4f}"
        )
    print("\n=== §17.2 回滚判据 ===")
    if flags:
        for flag in flags:
            print("  - " + flag)
    else:
        print("  无触发（v2 未劣于 v3 阈值）")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Studio homepage telemetry aggregation")
    parser.add_argument("--input", type=Path, default=None, help="jsonl 路径（默认本机 telemetry）")
    parser.add_argument("--out", type=Path, default=None, help="输出聚合 CSV 路径")
    args = parser.parse_args(argv)

    src = args.input or _events_path()
    if not src.exists():
        print(f"无 telemetry 文件：{src}", file=sys.stderr)
        return 1

    events = parse_events(src.read_text(encoding="utf-8").splitlines())
    agg = aggregate(events)
    summary = funnel_summary(events)
    flags = rollback_flags(summary)

    if args.out:
        write_csv(agg, args.out)
        print(f"已写聚合 CSV：{args.out}（{len(agg)} 行）\n")

    _print_summary(summary, flags)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
