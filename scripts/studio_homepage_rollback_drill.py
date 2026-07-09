#!/usr/bin/env python3
"""Studio 首页 v2 · 生产级回滚演练（M20-j · RUNBOOK §3）。

模拟「TRAVELOGUE_STUDIO_HOMEPAGE_V2=off」后用户态仍可用：
  1. gate off → GET / 仍 classic 冻结页
  2. sessionStorage homepageVariant=v2 不破坏 classic
  3. classic 关键 pytest 子集
  4. 可选写 rollout log 片段

退出码：全部通过 → 0；任一失败 → 1。

用法：
    python scripts/studio_homepage_rollback_drill.py
    python scripts/studio_homepage_rollback_drill.py --json --out docs/acceptance-records/studio-homepage-v2-rollback-drill.json
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]

# RUNBOOK §3.2 最小自动化子集
_ROLLBACK_TESTS = [
    "tests/unit/web/test_studio_home_v2.py::test_studio_home_gate_off_serves_classic_at_root",
    "tests/unit/web/test_studio_home_v2.py::test_studio_home_gate_auto_zero_percent_no_redirect",
    "tests/unit/web/test_studio_home_v2.py::test_studio_classic_contract_smoke_config_capabilities",
    "tests/e2e/test_studio_home_v2_ac_playwright.py::test_ac_hp2_23_rollback_ignores_homepage_variant",
]


def _run_pytest(tests: list[str]) -> tuple[bool, str]:
    """Run rollback subset in-process (nested subprocess breaks on Windows under pytest)."""
    import io
    from contextlib import redirect_stderr, redirect_stdout

    import pytest

    out = io.StringIO()
    err = io.StringIO()
    prev_mode = os.environ.get("TRAVELOGUE_STUDIO_HOMEPAGE_V2")
    prev_pct = os.environ.get("TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT")
    os.environ["TRAVELOGUE_STUDIO_HOMEPAGE_V2"] = "off"
    os.environ.pop("TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT", None)
    try:
        os.chdir(_REPO)
        with redirect_stdout(out), redirect_stderr(err):
            code = pytest.main(["-q", "--tb=line", *tests])
    finally:
        if prev_mode is None:
            os.environ.pop("TRAVELOGUE_STUDIO_HOMEPAGE_V2", None)
        else:
            os.environ["TRAVELOGUE_STUDIO_HOMEPAGE_V2"] = prev_mode
        if prev_pct is None:
            os.environ.pop("TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT", None)
        else:
            os.environ["TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT"] = prev_pct
    combined = (out.getvalue() or "") + (err.getvalue() or "")
    return code == 0, combined.strip()


def run_drill(*, write_out: Path | None = None) -> tuple[dict, int]:
    passed, output = _run_pytest(_ROLLBACK_TESTS)
    report = {
        "schema": "studio-homepage-rollback-drill/v1",
        "timestamp": datetime.now(UTC).isoformat(),
        "gate_mode_simulated": "off",
        "tests": _ROLLBACK_TESTS,
        "passed": passed,
        "pytest_output_tail": output[-4000:] if output else "",
        "checklist": {
            "stop_redirect": passed,
            "v3_dom_regression": passed,
            "session_homepage_variant_ignored": passed,
        },
        "next_steps_manual": [
            "验证 staging GET / 无 302",
            "Import 续 poll 手测（harness importing-resume）",
            "24h 漏斗监控 v3 恢复",
        ],
    }
    if write_out:
        write_out.parent.mkdir(parents=True, exist_ok=True)
        write_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report, 0 if passed else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Studio 首页 v2 回滚演练")
    parser.add_argument("--json", action="store_true", help="JSON 摘要输出 stdout")
    parser.add_argument("--out", type=Path, default=None, help="写入 JSON 报告路径")
    args = parser.parse_args(argv)

    report, code = run_drill(write_out=args.out)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        status = "PASS" if report["passed"] else "FAIL"
        print(f"=== Studio 首页 v2 回滚演练 [{status}] ===")
        print(f"  gate: {report['gate_mode_simulated']}")
        print(f"  tests: {len(report['tests'])}")
        if not report["passed"]:
            print("\n--- pytest tail ---")
            print(report["pytest_output_tail"])
    return code


if __name__ == "__main__":
    raise SystemExit(main())
