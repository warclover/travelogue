"""Studio 首页 v2 holdback 合并报告（M20-i · TELEMETRY §3 / §17.2）。

合并 funnel jsonl 聚合（studio_telemetry_aggregate.py）与 LCP/FCP 报告
（studio_lcp_measure.py），输出 §17.2 全量回滚判据一览，供 nightly / CI 门禁。

纯函数 `build_holdback_report` import-safe，供单测；CLI 可选内联跑 LCP。

用法：
    # 仅 funnel（本机 jsonl）
    python scripts/studio_holdback_report.py --out holdback.json

    # funnel + 已有 LCP JSON
    python scripts/studio_holdback_report.py --lcp-json lcp.json --out holdback.json

    # funnel + 现场采 LCP（需 Studio 运行中）
    python scripts/studio_holdback_report.py --lcp-base http://127.0.0.1:8766 --lcp-runs 5
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_telemetry = _load_module("studio_telemetry_aggregate", _SCRIPTS / "studio_telemetry_aggregate.py")
_lcp = _load_module("studio_lcp_measure", _SCRIPTS / "studio_lcp_measure.py")


def _funnel_dict(summary: dict) -> dict[str, Any]:
    """VariantFunnel → JSON-serializable dict."""
    out: dict[str, Any] = {}
    for variant, funnel in summary.items():
        if is_dataclass(funnel):
            counts = funnel.counts
            out[variant] = {
                "counts": dict(counts),
                "homepage_view": funnel.homepage_view,
                "cta_click": funnel.cta_click,
                "import_start": funnel.import_start,
                "import_success": funnel.import_success,
                "import_conversion": round(funnel.import_conversion, 4),
                "cta_per_view": round(funnel.cta_per_view, 4),
                "js_error": funnel.js_error,
                "js_error_rate": round(funnel.js_error_rate, 6),
            }
        else:
            out[variant] = funnel
    return out


def classify_flags(flags: list[str]) -> dict[str, list[str]]:
    """按 ROLLBACK / WARN / INSUFFICIENT / OK 分组。"""
    buckets: dict[str, list[str]] = {
        "rollback": [],
        "warn": [],
        "insufficient": [],
        "ok": [],
        "other": [],
    }
    for flag in flags:
        if flag.startswith("ROLLBACK"):
            buckets["rollback"].append(flag)
        elif flag.startswith("WARN"):
            buckets["warn"].append(flag)
        elif flag.startswith("INSUFFICIENT"):
            buckets["insufficient"].append(flag)
        elif flag.startswith("OK"):
            buckets["ok"].append(flag)
        else:
            buckets["other"].append(flag)
    return buckets


def build_holdback_report(
    events: list[dict[str, Any]],
    lcp_summary: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """→ 合并报告 dict（funnel + LCP + flags + should_rollback）。"""
    funnel_raw = _telemetry.funnel_summary(events)
    funnel = _funnel_dict(funnel_raw)
    funnel_flags = _telemetry.rollback_flags(funnel_raw)

    lcp_flags: list[str] = []
    if lcp_summary:
        lcp_flags = _lcp.lcp_rollback_flags(lcp_summary)

    all_flags = funnel_flags + lcp_flags
    classified = classify_flags(all_flags)
    should_rollback = bool(classified["rollback"])

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "funnel": funnel,
        "lcp": lcp_summary,
        "flags": {
            "funnel": funnel_flags,
            "lcp": lcp_flags,
            "all": all_flags,
            "classified": classified,
        },
        "should_rollback": should_rollback,
    }


def _print_report(report: dict[str, Any]) -> None:
    print("=== Studio 首页 Holdback 报告（v2 vs v3 · §17.2）===")
    print(f"生成时间：{report['generated_at']}\n")

    funnel = report.get("funnel") or {}
    if funnel:
        print("--- 漏斗 ---")
        for variant in sorted(funnel):
            f = funnel[variant]
            print(
                f"[{variant}] PV={f.get('homepage_view', 0)} cta={f.get('cta_click', 0)}"
                f" import={f.get('import_success', 0)}/{f.get('import_start', 0)}"
                f" conv={f.get('import_conversion', 0):.3f}"
                f" cta/PV={f.get('cta_per_view', 0):.3f}"
                f" js_err={f.get('js_error_rate', 0):.4f}"
            )
        print()

    lcp = report.get("lcp")
    if lcp:
        print("--- 首屏耗时 ---")
        for variant in sorted(lcp):
            s = lcp[variant]
            print(
                f"[{variant}] metric={s.get('metric', 'lcp')} p95={s.get('p95', 0)}ms"
                f" p50={s.get('p50', 0)} n={s.get('n', 0)}"
            )
        print()

    print("--- 回滚判据 ---")
    flags = report.get("flags", {}).get("all") or []
    if not flags:
        print("  （无判据输出）")
    for flag in flags:
        print("  - " + flag)

    if report.get("should_rollback"):
        print("\n>>> 结论：触发 ROLLBACK（§17.2）")
    else:
        print("\n>>> 结论：未触发 ROLLBACK")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Studio holdback 合并报告")
    parser.add_argument("--telemetry", type=Path, default=None, help="jsonl 路径（默认 ~/.travelogue/...）")
    parser.add_argument("--lcp-json", type=Path, default=None, help="已有 LCP 报告 JSON（studio_lcp_measure 输出）")
    parser.add_argument("--lcp-base", default=None, help="现场采 LCP：Studio 基址，如 http://127.0.0.1:8766")
    parser.add_argument("--lcp-runs", type=int, default=5, help="现场 LCP 每 variant 采样次数")
    parser.add_argument("--out", type=Path, default=None, help="输出合并 JSON")
    args = parser.parse_args(argv)

    src = args.telemetry or _telemetry._events_path()
    if not src.exists():
        print(f"无 telemetry 文件：{src}", file=sys.stderr)
        return 1

    events = _telemetry.parse_events(src.read_text(encoding="utf-8-sig").splitlines())

    lcp_summary: dict[str, dict[str, Any]] | None = None
    if args.lcp_json:
        if not args.lcp_json.exists():
            print(f"LCP JSON 不存在：{args.lcp_json}", file=sys.stderr)
            return 1
        payload = json.loads(args.lcp_json.read_text(encoding="utf-8-sig"))
        lcp_summary = payload.get("summary") or payload
    elif args.lcp_base:
        try:
            import playwright  # noqa: F401
        except ImportError:
            print("现场 LCP 需要 playwright", file=sys.stderr)
            return 2
        lcp_summary = _lcp.run_measurements(
            args.lcp_base, ["v2", "v3"], args.lcp_runs, settle_ms=1200
        )

    report = build_holdback_report(events, lcp_summary)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已写 holdback 报告：{args.out}\n")

    _print_report(report)
    return 1 if report.get("should_rollback") else 0


if __name__ == "__main__":
    raise SystemExit(main())
