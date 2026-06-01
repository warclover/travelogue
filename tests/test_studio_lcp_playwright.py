"""Studio 首页 LCP 采集 e2e（M20-i）。

用 scripts/studio_lcp_measure.py 的 measure_lcp / run_measurements 对真实
loopback 服务器实量 v2(/v2) 与 v3(/)，校验能采到 >0 的 LCP 并产出可比 P95。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from travelogue.web.studio_jobs import reset_job_store
from tests.test_studio_server import _free_port, _start_studio_server

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "studio_lcp_measure.py"
_spec = importlib.util.spec_from_file_location("studio_lcp_measure", _SCRIPT)
lcp_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
sys.modules["studio_lcp_measure"] = lcp_mod
_spec.loader.exec_module(lcp_mod)


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


@pytest.fixture
def studio_server(tmp_path: Path):
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"
    try:
        yield base
    finally:
        server.shutdown()
        server.server_close()


def test_measure_lcp_v2_positive(studio_server) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        lcp = lcp_mod.measure_lcp(page, studio_server + "/v2", settle_ms=1500)
        context.close()
        browser.close()
    assert lcp > 0, "未采到 v2 LCP"


def test_run_measurements_both_variants(studio_server) -> None:
    summary = lcp_mod.run_measurements(
        studio_server, ["v2", "v3"], runs=2, settle_ms=1200
    )
    assert summary["v2"]["n"] == 2
    assert summary["v3"]["n"] == 2
    assert summary["v2"]["p95"] > 0
    assert summary["v3"]["p95"] > 0
    flags = lcp_mod.lcp_rollback_flags(summary)
    assert flags  # OK 或 ROLLBACK，均为有效对照
    assert "INSUFFICIENT_DATA" not in flags[0]
