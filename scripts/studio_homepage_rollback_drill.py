#!/usr/bin/env python3
"""Studio 首页 v2 · 生产级回滚演练（M20-j · RUNBOOK §3）。

模拟「TRAVELOGUE_STUDIO_HOMEPAGE_V2=off」后用户态仍可用：
  1. gate off → GET / 仍 v3
  2. sessionStorage homepageVariant=v2 不破坏 v3
  3. v3 关键 pytest 子集
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
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]

# RUNBOOK §3.2 最小自动化子集
_ROLLBACK_TESTS = [
    "tests/test_studio_home_v2.py::test_studio_home_gate_off_serves_v3_at_root",
    "tests/test_studio_home_v2.py::test_studio_home_gate_auto_zero_percent_no_redirect",
    "tests/test_studio_home_v2_ac_playwright.py::test_ac_hp2_23_rollback_ignores_homepage_variant",
    "tests/test_studio_home_v2_ac_playwright.py::test_m20j_holdback_control_experiment_exposure",
    "tests/test_studio_p8_regression.py::test_p9_analytics_events",
]


def _run_pytest(tests: list[str]) -> tuple[bool, str]:
    env = os.environ.copy()
    env["TRAVELOGUE_STUDIO_HOMEPAGE_V2"] = "off"
    env.pop("TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT", None)
    cmd = [sys.executable, "-m", "pytest", *tests, "-q", "--tb=line"]
    proc = subprocess.run(
        cmd,
        cwd=_REPO,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    combined = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, combined.strip()


def run_drill(*, write_out: Path | None = None) -> tuple[dict, int]:
    passed, output = _run_pytest(_ROLLBACK_TESTS)
    report = {
        "schema": "studio-homepage-rollback-drill/v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gate_mode_simulated": "off",
        "tests": _ROLLBACK_TESTS,
        "passed": passed,
        "pytest_output_tail": output[-4000:] if output else "",
        "checklist": {
            "stop_redirect": passed,
            "v3_dom_regression": passed,
            "session_homepage_variant_ignored": passed,
            "v3_experiment_exposure": passed,
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
