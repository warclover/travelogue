"""Share-Face Purity · AC-SFP-06 分章面板与导出浮层互斥。"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.integration.studio.test_studio_server import _free_port, _start_studio_server
from tests.preview_arc14_fixtures import demo_assets_available, seed_arc14_preview_trip
from travelogue.web.studio_jobs import reset_job_store

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


@pytest.mark.skipif(not demo_assets_available(), reason="demo assets missing")
def test_ac_sfp_06_chapter_panel_close_not_blocked_by_export(tmp_path: Path) -> None:
    """开导出设置 → 开分章 → 点 × 一次关闭（不依赖 force click）。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = seed_arc14_preview_trip(trips_dir, "sfp-chapter-mutex")
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(f"{base}/{trip_id}/index.html", wait_until="networkidle")
            page.locator(".preview-toolbar__dock").wait_for(state="visible", timeout=15_000)

            # 打开导出设置浮层（▾ caret，非金色主按钮——主按钮会直接开导）
            caret = page.locator(".preview-toolbar__longshot-caret").first
            caret.wait_for(state="visible", timeout=10_000)
            caret.click()
            page.locator(".preview-toolbar__export-popover").wait_for(
                state="visible", timeout=10_000
            )

            # 打开分章（应关掉导出层）
            chap_btn = page.locator(".preview-toolbar__dock-btn--chapters").first
            chap_btn.click()
            panel = page.locator(".preview-chapter-panel")
            panel.wait_for(state="visible", timeout=10_000)
            assert page.locator(".preview-toolbar__export-popover:not([hidden])").count() == 0

            # 点 × 关闭 —— 不得被导出 caret 拦截
            close_btn = panel.locator(".preview-chapter-panel__close")
            close_btn.click(force=False, timeout=5_000)
            page.wait_for_function(
                """() => {
                  const el = document.querySelector('.preview-chapter-panel');
                  return !el || el.hidden === true;
                }""",
                timeout=5_000,
            )
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
