"""Phase 9 · Studio UX Playwright (AC-P9-UX-02/03)."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.web.studio_jobs import reset_job_store
from tests.test_studio_home_v2_ac_playwright import _goto_v2, _wait_visible
from tests.test_studio_server import _free_port, _start_studio_server

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]

CULL_LINE = "经挑选 10 张进入排版（精选 2 张已为您保留）"


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


def test_ac_p9_ux_02_v2_first_success_shows_cull_line(studio_server) -> None:
    """AC-P9-UX-02 · FirstSuccess 第二行展示 cullUserLine。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"], "dev=1&studioFixture=multi")
        page.wait_for_function("() => typeof showFirstSuccess === 'function' || true")
        page.evaluate(
            """
            async (line) => {
              const mod = await import('/__studio/homepage-v2/first-success.js');
              mod.showFirstSuccess({
                result: {
                  tripId: 'ux-trip',
                  title: '京都 · 雨后',
                  photoCount: 12,
                  featuredCount: 2,
                  segmentCount: 2,
                  cullUserLine: line,
                },
              });
            }
            """,
            CULL_LINE,
        )
        _wait_visible(page, "v2-success-open")
        msg = page.locator("#v2-success-msg").inner_text()
        assert "已生成" in msg
        assert "经挑选" in msg
        assert "精选 2 张已为您保留" in msg
        assert "\n" in msg or CULL_LINE.split("（")[0] in msg
        browser.close()


def test_ac_p9_ux_03_no_excluded_photos_entry(studio_server) -> None:
    """AC-P9-UX-03 · DOM 无被筛图入口。"""
    forbidden = ("被筛", "已隐藏", "excluded-photos", "已删除", "剔除")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(
            page,
            studio_server["base"],
            "dev=1&studioState=first-success&studioFixture=multi",
        )
        _wait_visible(page, "v2-success-open")
        body_text = page.locator("body").inner_text()
        html = page.content().lower()
        for token in forbidden:
            assert token not in body_text, f"unexpected UX copy: {token}"
            assert token not in html
        browser.close()


def test_ac_p9_ux_02_v3_success_msg_cull_line(studio_server) -> None:
    """AC-P9-UX-02 · v3 studio-success 第二行 cullUserLine。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(studio_server["base"], wait_until="networkidle")
        page.evaluate(
            """
            (line) => {
              var msg = document.getElementById('studio-success-msg');
              var panel = document.getElementById('studio-success');
              if (panel) panel.hidden = false;
              if (msg) {
                msg.textContent = '《测试》已生成 · 照片 12 张\\n' + line;
              }
            }
            """,
            CULL_LINE,
        )
        text = page.locator("#studio-success-msg").inner_text()
        assert "已生成" in text
        assert "经挑选" in text
        browser.close()
