"""Wait Tips V1 · W0 e2e 烟测（AC-WT-01 / 05 · QA-WT-04）。

对照 docs/ACCEPTANCE-WAIT-TIPS-V1.md · dogfood F1/F4。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.e2e.test_import_wizard_v3_playwright import (
    _goto_v2,
    _route_harness_import_mocks,
    _wait_visible,
    _wizard_quick_folder_to_confirm,
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
def wizard_server(tmp_path: Path):
    trips_dir = tmp_path / "trips-wait-tips"
    trips_dir.mkdir(parents=True, exist_ok=True)
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"
    try:
        yield {"base": base}
    finally:
        server.shutdown()
        server.server_close()


def test_ac_wt_01_tips_appear_under_stage_after_2s(wizard_server) -> None:
    """Harness Importing：≥2s 后 Tips 可见，且在取消按钮之前。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(
            page,
            wizard_server["base"],
            "dev=1&studioState=importing&studioJob=running",
        )
        page.evaluate(
            """() => {
              try {
                localStorage.removeItem('travelogue.waitTips.dismissed');
                localStorage.removeItem('travelogue.waitTips.version');
              } catch (e) {}
            }"""
        )
        # harness 在首屏后注入；清 dismiss 后重进 Importing
        _goto_v2(
            page,
            wizard_server["base"],
            "dev=1&studioState=importing&studioJob=running",
        )
        _wait_visible(page, "v2-import-cancel")
        page.wait_for_selector("#v2-wait-tips:not([hidden])", timeout=5_000)
        tips = page.locator("#v2-wait-tips")
        assert tips.is_visible()
        assert "可翻的卷轴" in tips.locator(".v2-wait-tips__title").inner_text()
        order_ok = page.evaluate(
            """() => {
              const panel = document.querySelector('.v2-import-panel');
              if (!panel) return false;
              const tips = document.getElementById('v2-wait-tips');
              const cancel = document.getElementById('v2-import-cancel');
              const stage = document.getElementById('v2-import-stage');
              if (!tips || !cancel || !stage) return false;
              const kids = Array.from(panel.children);
              return kids.indexOf(stage) < kids.indexOf(tips)
                && kids.indexOf(tips) < kids.indexOf(cancel);
            }"""
        )
        assert order_ok, "Tips must sit between stage and cancel"
        browser.close()


def test_ac_wt_05_tips_gone_after_first_success(wizard_server) -> None:
    """真实导入 succeeded → FirstSuccess；Tips 节点卸载。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _route_harness_import_mocks(
            page,
            photo_count=6,
            layout_eligible=6,
            import_mode="quick_share",
        )
        _goto_v2(page, wizard_server["base"])
        page.evaluate(
            """() => {
              try {
                localStorage.removeItem('travelogue.waitTips.dismissed');
                localStorage.removeItem('travelogue.waitTips.version');
              } catch (e) {}
            }"""
        )
        _wait_visible(page, "v2-frame")
        _wizard_quick_folder_to_confirm(page)
        page.locator("#v2-wizard-start").click()
        page.wait_for_selector("#v2-import-cancel", state="visible", timeout=15_000)
        # Tips 可能尚未到 2s；等到可见或成功面出现
        page.wait_for_function(
            """() => {
              const tips = document.getElementById('v2-wait-tips');
              const ok = document.getElementById('v2-success-open');
              return (tips && !tips.hidden) || (ok && !ok.hidden && ok.offsetParent);
            }""",
            timeout=30_000,
        )
        page.wait_for_selector("#v2-success-open", state="visible", timeout=30_000)
        tips_gone = page.evaluate(
            """() => {
              const tips = document.getElementById('v2-wait-tips');
              return !tips || tips.hidden || !tips.isConnected;
            }"""
        )
        assert tips_gone, "Wait Tips must unmount before/with FirstSuccess"
        browser.close()
