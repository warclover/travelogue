"""Phase 4 · FirstSuccess featured feedback (AC-P4-02 e2e)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.e2e.test_studio_home_v2_ac_playwright import (
    _goto_v2,
    _success_dialog_text,
    _wait_visible,
)
from tests.integration.studio.test_studio_server import _free_port, _start_studio_server
from travelogue.web.studio_jobs import reset_job_store

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]


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
        yield {"base": base}
    finally:
        server.shutdown()
        server.server_close()


def _show_first_success(page, result: dict) -> None:
    page.wait_for_function("() => typeof showFirstSuccess === 'function' || true")
    page.evaluate(
        """
        async (payload) => {
          const mod = await import('/__studio/homepage-v2/first-success.js');
          mod.showFirstSuccess({ result: payload });
        }
        """,
        result,
    )
    _wait_visible(page, "v2-success-open")


def test_ac_p4_02_first_success_shows_featured_summary(studio_server) -> None:
    """AC-P4-02 · 双文件夹 trip 成功页第一行含「精选 N 张」。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"], "dev=1&studioFixture=multi")
        _show_first_success(
            page,
            {
                "tripId": "p4-feat-trip",
                "title": "雨后京都",
                "photoCount": 48,
                "featuredCount": 12,
                "segmentCount": 3,
                "cullUserLine": "经挑选 40 张进入排版（精选 12 张已为您保留）",
            },
        )
        msg = _success_dialog_text(page)
        assert "雨后京都" in msg
        assert "精选 12 张" in msg
        assert "行程 3 段" in msg
        assert "经挑选" in msg
        browser.close()


def test_ac_p4_02_first_success_without_featured_omits_featured_clause(studio_server) -> None:
    """AC-P4-02 负向 · 无精选时展示照片总数，不出现「精选 0 张」。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"], "dev=1&studioFixture=multi")
        _show_first_success(
            page,
            {
                "tripId": "p4-single-folder",
                "title": "周末散步",
                "photoCount": 18,
                "featuredCount": 0,
                "segmentCount": 0,
            },
        )
        msg = page.locator("#v2-success-msg").inner_text()
        assert "照片 18 张" in msg
        assert "精选" not in msg
        assert "0 段" not in msg
        browser.close()
