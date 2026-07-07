"""Import Wizard v3 · AC 自动验收 e2e（Playwright）。

对照 docs/PRD-IMPORT-SHEET-v3-WIZARD.md §12：
  AC-IW-01/02 一屏无滚轮 · AC-IW-04 默认无 checkbox · AC-IW-05 摘要行随开关同步
  AC-IW-09b 首次访问强制快速分享 · AC-IW-11 flag 关回落旧 Sheet
  AC-IW-DS-01 下游 import_start/Importing 衔接 · AC-IW-DS-05 上传失败重试回 Step 1

flag：studio.importWizardV3Enabled（默认 false，仅本文件测试显式开启）。
"""

from __future__ import annotations

import yaml
from pathlib import Path

import pytest

from tests.test_studio_server import _free_port, _start_studio_server
from travelogue.web.studio_jobs import reset_job_store

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


@pytest.fixture
def wizard_server(tmp_path: Path):
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump({"studio": {"import_wizard_v3_enabled": True}}),
        encoding="utf-8",
    )
    port = _free_port()
    server = _start_studio_server(trips_dir, port, config_path=config_path)
    base = f"http://127.0.0.1:{port}"
    try:
        yield {"base": base}
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture
def legacy_server(tmp_path: Path):
    """flag 关闭（默认）· AC-IW-11 回归基线。"""
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


def _goto_v2(page, base: str, query: str = "") -> None:
    url = base + "/" + (("?" + query) if query else "")
    page.goto(url, wait_until="networkidle")


def _wait_visible(page, el_id: str, timeout: int = 20_000) -> None:
    page.wait_for_function(
        """
        (id) => {
          const el = document.getElementById(id);
          if (!el || el.hidden) return false;
          const cs = getComputedStyle(el);
          return cs.display !== 'none' && cs.visibility !== 'hidden'
            && el.getClientRects().length > 0;
        }
        """,
        arg=el_id,
        timeout=timeout,
    )


def _open_wizard(page) -> None:
    page.locator("#v2-cta").click()
    _wait_visible(page, "v2-wizard-root")


def _no_internal_scroll(page, selector: str) -> bool:
    return page.evaluate(
        """
        (sel) => {
          const el = document.querySelector(sel);
          if (!el) return false;
          return el.scrollHeight <= el.clientHeight + 1;
        }
        """,
        selector,
    )


def test_ac_iw_01_step1_one_screen_1024x768(wizard_server) -> None:
    """AC-IW-01 · 1024×768 · Step 1 无内部滚动。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1024, "height": 768})
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _open_wizard(page)
        _wait_visible(page, "v2-wizard-step-pick")
        assert _no_internal_scroll(page, "#v2-import-wizard")
        assert page.locator("#v2-wizard-pick").is_visible()
        browser.close()


def test_ac_iw_02_step2_one_screen_1024x768(wizard_server) -> None:
    """AC-IW-02 · 1024×768 · Step 2 折叠态主 CTA 完整可见，无内部滚动。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1024, "height": 768})
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _open_wizard(page)
        page.locator("#v2-wizard-more-import summary").click()
        page.locator("#v2-wizard-album-path").fill("/harness/album")
        page.locator("#v2-wizard-path-submit").click()
        _wait_visible(page, "v2-wizard-step-confirm")

        assert _no_internal_scroll(page, "#v2-import-wizard")
        start_btn = page.locator("#v2-wizard-start")
        assert start_btn.is_visible()
        box = start_btn.bounding_box()
        assert box is not None
        assert box["y"] + box["height"] <= 768
        browser.close()


def test_ac_iw_04_default_no_visible_checkbox(wizard_server) -> None:
    """AC-IW-04 · 默认态无可见 checkbox；摘要行为默认文案。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _open_wizard(page)
        page.locator("#v2-wizard-more-import summary").click()
        page.locator("#v2-wizard-album-path").fill("/harness/album")
        page.locator("#v2-wizard-path-submit").click()
        _wait_visible(page, "v2-wizard-step-confirm")

        assert not page.locator("#v2-wizard-photo-cull").is_visible()
        assert not page.locator("#v2-wizard-keep-dupes").is_visible()
        summary = page.locator("#v2-wizard-photo-summary").inner_text()
        assert "智能挑选已开启" in summary
        assert "连拍自动择优" in summary
        browser.close()


def test_ac_iw_05_drawer_toggle_updates_summary(wizard_server) -> None:
    """AC-IW-05 · 展开抽屉取消智能挑选 → 摘要行同步更新。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _open_wizard(page)
        page.locator("#v2-wizard-more-import summary").click()
        page.locator("#v2-wizard-album-path").fill("/harness/album")
        page.locator("#v2-wizard-path-submit").click()
        _wait_visible(page, "v2-wizard-step-confirm")

        page.locator("#v2-wizard-photo-adjust").click()
        _wait_visible(page, "v2-wizard-photo-drawer")
        page.locator("#v2-wizard-photo-cull").uncheck()

        summary = page.locator("#v2-wizard-photo-summary").inner_text()
        assert "不做智能挑选" in summary
        browser.close()


def test_ac_iw_09b_first_visit_forces_quick_share(wizard_server) -> None:
    """AC-IW-09b · 首次打开 Studio 强制快速分享默认（忽略 localStorage 精细偏好）。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.add_init_script(
            """
            () => { localStorage.setItem('travelogue.studio.lastImportMode', 'fine_craft'); }
            """
        )
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _open_wizard(page)
        page.locator("#v2-wizard-more-import summary").click()
        page.locator("#v2-wizard-album-path").fill("/harness/album")
        page.locator("#v2-wizard-path-submit").click()
        _wait_visible(page, "v2-wizard-step-confirm")

        checked = page.locator("#v2-wizard-mode-quick").get_attribute("aria-checked")
        assert checked == "true"
        browser.close()


def test_ac_iw_11_flag_off_falls_back_to_legacy_sheet(legacy_server) -> None:
    """AC-IW-11 · flag 关闭时开 CTA 仍呈现旧版 Sheet，Wizard 不渲染。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, legacy_server["base"])
        _wait_visible(page, "v2-frame")
        page.locator("#v2-cta").click()
        _wait_visible(page, "v2-sheet-root")
        assert page.locator("#v2-sheet-pick").is_visible()
        wizard_hidden = page.evaluate(
            "() => { const w = document.getElementById('v2-wizard-root'); return !w || w.hidden; }"
        )
        assert wizard_hidden
        browser.close()


def test_ac_iw_ds_01_quick_path_reaches_importing(wizard_server) -> None:
    """AC-IW-DS-01 · Wizard 快速路径开始制作 → 下游 Importing 面板出现（出口未变）。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _open_wizard(page)
        page.locator("#v2-wizard-more-import summary").click()
        page.locator("#v2-wizard-album-path").fill("/harness/album")
        page.locator("#v2-wizard-path-submit").click()
        _wait_visible(page, "v2-wizard-step-confirm")

        assert page.locator("#v2-wizard-start").inner_text().strip() == "开始制作 →"
        page.locator("#v2-wizard-start").click()
        _wait_visible(page, "v2-import-cancel")

        pending = page.evaluate(
            "() => JSON.parse(sessionStorage.getItem('travelogue.studio.activePending') || '{}')"
        )
        assert pending.get("mode") == "quick_share"
        assert pending.get("albumPath") == "/harness/album"
        browser.close()


def test_ac_iw_ds_upload_retry_reopens_wizard_at_step1(wizard_server) -> None:
    """AC-IW-DS-05（上传分支） · Failed 重试 → Wizard 重新打开且停在 Step 1，非 stale confirm。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, wizard_server["base"], "dev=1&studioFixture=empty")
        _wait_visible(page, "v2-frame")
        page.evaluate(
            """
            () => {
              sessionStorage.setItem(
                'travelogue.studio.activePending',
                JSON.stringify({ uploadForm: true, fileCount: 3, title: '上传测试' })
              );
              const failure = document.getElementById('v2-failure');
              if (failure) failure.hidden = false;
            }
            """
        )
        _wait_visible(page, "v2-failure-retry")
        page.locator("#v2-failure-retry").click()
        _wait_visible(page, "v2-wizard-root")

        step_pick_visible = page.evaluate(
            "() => { const el = document.getElementById('v2-wizard-step-pick'); return el && !el.hidden; }"
        )
        assert step_pick_visible
        browser.close()
