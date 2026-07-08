#!/usr/bin/env python3
"""Studio 首页 v2 · M20-i 合并演练（funnel + LCP + §17.2 holdback 判据）。

串联：
  1. 读 telemetry jsonl（或 --synthetic 生成最小 v2/v3 对照样本）
  2. 可选：Playwright 实量 LCP/FCP（--lcp-base 或 --spawn 临时起 Studio）
  3. 输出 holdback 合并报告 JSON + 人类可读摘要

退出码：触发 ROLLBACK → 1；否则 0（便于 nightly CI 门禁）。

用法：
    # 本机 Studio 已运行
    python scripts/studio_homepage_m20i_drill.py --lcp-base http://127.0.0.1:8766 --out holdback.json

    # 自动起 loopback Studio（无需手动 serve）
    python scripts/studio_homepage_m20i_drill.py --spawn --lcp-runs 3 --out holdback.json

    # 仅 funnel（无 LCP）
    python scripts/studio_homepage_m20i_drill.py --telemetry ~/.travelogue/telemetry/studio-homepage-events.jsonl --skip-lcp
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_REPO = _SCRIPTS.parent


def _load(name: str, path: Path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_hb = _load("studio_holdback_report", _SCRIPTS / "studio_holdback_report.py")
_lcp = _load("studio_lcp_measure", _SCRIPTS / "studio_lcp_measure.py")
_telemetry = _load("studio_telemetry_aggregate", _SCRIPTS / "studio_telemetry_aggregate.py")


def _synthetic_events() -> list[dict]:
    """最小 v2/v3 同期样本（漏斗不触发 ROLLBACK，仅供演练结构）。"""

    def ev(variant: str, name: str) -> dict:
        return {
            "ts": "2026-06-01T12:00:00.000+00:00",
            "event": name,
            "meta": {"variant": variant},
        }

    return (
        [ev("classic", "homepage_view") for _ in range(20)]
        + [ev("classic", "cta_click") for _ in range(8)]
        + [ev("classic", "import_start") for _ in range(5)]
        + [ev("classic", "import_success") for _ in range(5)]
        + [ev("v2", "homepage_view") for _ in range(20)]
        + [ev("v2", "cta_click") for _ in range(7)]
        + [ev("v2", "import_start") for _ in range(5)]
        + [ev("v2", "import_success") for _ in range(5)]
    )


def _spawn_studio() -> tuple[object, str, Path]:
    """起临时 loopback Studio；返回 (server, base_url, trips_dir)。"""
    sys.path.insert(0, str(_REPO))
    from tests.integration.studio.test_studio_server import _free_port, _start_studio_server

    trips_dir = Path(tempfile.mkdtemp(prefix="m20i-drill-")) / "trips"
    trips_dir.mkdir(parents=True)
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    return server, f"http://127.0.0.1:{port}", trips_dir


def run_drill(
    *,
    telemetry: Path | None,
    synthetic: bool,
    lcp_base: str | None,
    spawn: bool,
    lcp_runs: int,
    settle_ms: int,
    skip_lcp: bool,
    out: Path | None,
    min_lcp_runs: int = 10,
) -> tuple[dict, int]:
    """执行演练；返回 (report, exit_code)。"""
    if not skip_lcp and lcp_runs < min_lcp_runs:
        print(
            f"WARN: --lcp-runs={lcp_runs} < {min_lcp_runs}，"
            "小样本易误报 ROLLBACK；nightly 建议 --lcp-runs 10",
            file=sys.stderr,
        )
    events: list[dict] = []
    if synthetic:
        events = _synthetic_events()
    elif telemetry and telemetry.exists():
        events = _telemetry.parse_events(
            telemetry.read_text(encoding="utf-8-sig").splitlines()
        )
    else:
        default = _telemetry._events_path()
        if default.exists():
            events = _telemetry.parse_events(
                default.read_text(encoding="utf-8-sig").splitlines()
            )
        else:
            print(
                "WARN: 无 telemetry 文件，漏斗判据将 INSUFFICIENT_DATA"
                "（可用 --synthetic 生成演练样本）",
                file=sys.stderr,
            )

    server = None
    lcp_summary = None
    try:
        if not skip_lcp:
            base = lcp_base
            if spawn:
                server, base, _ = _spawn_studio()
                print(f"已启动临时 Studio：{base}", file=sys.stderr)
            if not base:
                print("跳过 LCP：未指定 --lcp-base / --spawn", file=sys.stderr)
            else:
                try:
                    import playwright  # noqa: F401
                except ImportError:
                    print("LCP 需要 playwright", file=sys.stderr)
                    return {"error": "playwright missing"}, 2
                lcp_summary = _lcp.run_measurements(
                    base, ["v2", "classic"], lcp_runs, settle_ms
                )
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()

    report = _hb.build_holdback_report(events, lcp_summary)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已写 holdback 报告：{out}\n")

    _hb._print_report(report)
    exit_code = 1 if report.get("should_rollback") else 0
    return report, exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Studio 首页 M20-i holdback 演练")
    parser.add_argument("--telemetry", type=Path, default=None, help="jsonl 路径")
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="使用内置 v2/v3 最小对照样本（无本机 jsonl 时）",
    )
    parser.add_argument("--lcp-base", default=None, help="Studio 基址，如 http://127.0.0.1:8766")
    parser.add_argument(
        "--spawn",
        action="store_true",
        help="自动起临时 loopback Studio 并采 LCP",
    )
    parser.add_argument("--lcp-runs", type=int, default=5, help="每 variant LCP 采样次数")
    parser.add_argument(
        "--min-lcp-runs",
        type=int,
        default=10,
        help="低于此值时 stderr 警告（nightly 建议 ≥10）",
    )
    parser.add_argument("--settle-ms", type=int, default=1200, help="LCP 收尾等待 ms")
    parser.add_argument("--skip-lcp", action="store_true", help="跳过 LCP 采集")
    parser.add_argument("--out", type=Path, default=None, help="输出 holdback JSON")
    args = parser.parse_args(argv)

    if args.spawn and args.lcp_base:
        print("WARN: --spawn 与 --lcp-base 同时指定，使用 --spawn", file=sys.stderr)

    _, exit_code = run_drill(
        telemetry=args.telemetry,
        synthetic=args.synthetic,
        lcp_base=None if args.spawn else args.lcp_base,
        spawn=args.spawn,
        lcp_runs=args.lcp_runs,
        settle_ms=args.settle_ms,
        skip_lcp=args.skip_lcp,
        out=args.out,
        min_lcp_runs=args.min_lcp_runs,
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
