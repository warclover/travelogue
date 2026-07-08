"""M20-i 合并演练脚本集成测试（studio_homepage_m20i_drill.py）。"""



from __future__ import annotations
from tests._repo_root import repo_root

import importlib.util
import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("playwright")

_SCRIPT = repo_root(__file__) / "scripts" / "studio_homepage_m20i_drill.py"
_spec = importlib.util.spec_from_file_location("studio_homepage_m20i_drill", _SCRIPT)
drill_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
sys.modules["studio_homepage_m20i_drill"] = drill_mod
_spec.loader.exec_module(drill_mod)

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]


def test_run_drill_synthetic_skip_lcp(tmp_path: Path) -> None:
    out = tmp_path / "holdback.json"
    report, rc = drill_mod.run_drill(
        telemetry=None,
        synthetic=True,
        lcp_base=None,
        spawn=False,
        lcp_runs=2,
        settle_ms=800,
        skip_lcp=True,
        out=out,
    )
    assert rc == 0
    assert out.is_file()
    body = json.loads(out.read_text(encoding="utf-8"))
    assert body["should_rollback"] is False
    assert "v2" in body["funnel"]
    assert "v3" in body["funnel"]
    assert report["lcp"] is None


def test_main_spawn_lcp(tmp_path: Path) -> None:
    """spawn + 实量 LCP：验证报告结构（小样本 FCP 可能触发 ROLLBACK，属预期）。"""
    out = tmp_path / "drill.json"
    rc = drill_mod.main([
        "--spawn",
        "--synthetic",
        "--lcp-runs", "2",
        "--settle-ms", "1000",
        "--out", str(out),
    ])
    body = json.loads(out.read_text(encoding="utf-8"))
    assert body["lcp"] is not None
    assert body["lcp"]["v2"]["n"] == 2
    assert body["lcp"]["v3"]["n"] == 2
    assert body["lcp"]["v2"]["p95"] > 0
    assert body["lcp"]["v3"]["p95"] > 0
    assert body["flags"]["lcp"]
    assert body["funnel"]["v2"]["import_conversion"] == 1.0
    assert rc in (0, 1)
