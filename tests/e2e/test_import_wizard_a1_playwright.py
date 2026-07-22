"""Import Wizard A.1 · AC 自动验收 e2e（Playwright）。

对照 docs/PRD-IMPORT-WIZARD-A1-DELTA.md §5 + IMPLEMENTATION-IMPORT-WIZARD-A1.md。
Wizard 为唯一生产入口。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.e2e.test_import_wizard_v3_playwright import (
    _goto_v2,
    _open_wizard,
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
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir(parents=True, exist_ok=True)
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"
    try:
        yield {"base": base}
    finally:
        server.shutdown()
        server.server_close()


def _route_preview(page, *, photo_count: int = 134, date_start=None, date_end=None) -> None:
    body = {
        "ok": True,
        "photoCount": photo_count,
        "folderName": "贵州暑假游",
        "thumbs": [
            "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
        ],
        "thumbNames": ["IMG_1024.JPG"],
    }
    if date_start:
        body["dateStart"] = date_start
    if date_end:
        body["dateEnd"] = date_end

    def _album_preview(route) -> None:
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(body),
        )

    page.route("**/__travelogue/album-preview", _album_preview)


def test_ac_a1_01_no_back_reselect_change_returns(wizard_server) -> None:
    """AC-A1-01 · 头栏无「重新选择」；「更换」回 Step 1。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _route_preview(page)
        _wizard_quick_folder_to_confirm(page)
        assert page.locator("#v2-wizard-back-confirm").count() == 0
        assert page.locator("#v2-wizard-change-folder").get_attribute("aria-label")
        page.locator("#v2-wizard-change-folder").click()
        _wait_visible(page, "v2-wizard-step-pick")
        browser.close()


def test_ac_a1_02_advanced_collapsed_payload_complete(wizard_server) -> None:
    """AC-A1-02 · 2b 默认折叠；展开后密度进 payload。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _route_harness_import_mocks(page)
        _wizard_quick_folder_to_confirm(page)
        page.locator("#v2-wizard-mode-fine").click()
        page.locator("#v2-wizard-start").click()
        _wait_visible(page, "v2-wizard-step-fine")
        advanced_open = page.evaluate(
            "() => !!document.getElementById('v2-wizard-advanced')?.open"
        )
        assert advanced_open is False
        assert page.locator("#v2-wizard-date-start").count() == 1
        page.locator("#v2-wizard-advanced summary").click()
        page.locator('input[name="v2-wizard-layout-density"][value="collage_first"]').check()
        page.locator("#v2-wizard-start-fine").click()
        _wait_visible(page, "v2-import-cancel")
        pending = page.evaluate(
            "() => JSON.parse(sessionStorage.getItem('travelogue.studio.activePending') || '{}')"
        )
        assert pending.get("mode") == "fine_craft"
        assert pending.get("layoutDensity") == "collage_first"
        browser.close()


def test_ac_a1_03_photo_count_hints(wizard_server) -> None:
    """AC-A1-03 · N=3 / N=301 弱提示且可开始。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _route_preview(page, photo_count=3)
        _wizard_quick_folder_to_confirm(page)
        page.wait_for_function(
            """() => {
              const el = document.getElementById('v2-wizard-count-hint');
              return el && !el.hidden && el.textContent.includes('偏少');
            }"""
        )
        assert page.locator("#v2-wizard-start").is_enabled()
        browser.close()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _route_preview(page, photo_count=301)
        _wizard_quick_folder_to_confirm(page)
        page.wait_for_function(
            """() => {
              const el = document.getElementById('v2-wizard-count-hint');
              return el && !el.hidden && el.textContent.includes('较多');
            }"""
        )
        assert page.locator("#v2-wizard-start").is_enabled()
        browser.close()


def test_ac_a1_04_trust_row_visible(wizard_server) -> None:
    """AC-A1-04 · Step 2 / 2b 信任行可见。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _route_preview(page)
        _wizard_quick_folder_to_confirm(page)
        trust = page.locator("#v2-wizard-trust")
        assert trust.is_visible()
        assert "约 3–8 分钟" in trust.inner_text()
        page.locator("#v2-wizard-mode-fine").click()
        page.locator("#v2-wizard-start").click()
        _wait_visible(page, "v2-wizard-step-fine")
        trust_fine = page.locator("#v2-wizard-trust-fine")
        assert trust_fine.is_visible()
        assert "稍后回来" in trust_fine.inner_text()
        browser.close()


def test_ac_a1_05_pick_fail_expands_fallback(wizard_server) -> None:
    """AC-A1-05 · 选夹失败 → 其他导入方式 open + 焦点路径。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")

        def _pick_fail(route) -> None:
            route.fulfill(
                status=500,
                content_type="application/json",
                body=json.dumps({"ok": False, "message": "无法打开本机选文件夹"}),
            )

        page.route("**/__travelogue/pick-folder", _pick_fail)
        _open_wizard(page)
        page.locator("#v2-wizard-pick").click()
        page.wait_for_function(
            "() => !!document.getElementById('v2-wizard-more-import')?.open"
        )
        focused = page.evaluate("() => document.activeElement?.id")
        assert focused == "v2-wizard-album-path"
        browser.close()


def test_ac_a1_06_mode_copy_and_fine_cta(wizard_server) -> None:
    """AC-A1-06 · 模式卡副文案 + 选精细 CTA「填写细节 →」。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _route_preview(page)
        _wizard_quick_folder_to_confirm(page)
        quick_desc = page.locator("#v2-wizard-mode-quick .v2-wizard__mode-card-desc").inner_text()
        fine_desc = page.locator("#v2-wizard-mode-fine .v2-wizard__mode-card-desc").inner_text()
        assert "优先出微信长图" in quick_desc
        assert "多填一点" in fine_desc
        page.locator("#v2-wizard-mode-fine").click()
        assert page.locator("#v2-wizard-start").inner_text().strip() == "填写细节 →"
        browser.close()


def test_ac_a1_07_prefill_title_and_dates(wizard_server) -> None:
    """AC-A1-07 · 进 2b 名称=folderName；有日期则预填。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _route_preview(page, date_start="2025-07-12", date_end="2025-07-18")
        _wizard_quick_folder_to_confirm(page)
        page.wait_for_function(
            "() => (document.getElementById('v2-wizard-verify-line')?.textContent || '').includes('贵州')"
        )
        page.locator("#v2-wizard-mode-fine").click()
        page.locator("#v2-wizard-start").click()
        _wait_visible(page, "v2-wizard-step-fine")
        title = page.locator("#v2-wizard-trip-title").input_value()
        assert title == "贵州暑假游"
        page.locator("#v2-wizard-advanced summary").click()
        assert page.locator("#v2-wizard-date-start").input_value() == "2025-07-12"
        assert page.locator("#v2-wizard-date-end").input_value() == "2025-07-18"
        browser.close()


def test_ac_a1_08_thumb_tip_no_lightbox(wizard_server) -> None:
    """AC-A1-08 · thumb 有可访问名称（alt/title）；click 不打开 Lightbox。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _route_preview(page)
        _wizard_quick_folder_to_confirm(page)
        page.wait_for_selector("#v2-wizard-thumbs .v2-wizard__thumb")
        thumb = page.locator("#v2-wizard-thumbs .v2-wizard__thumb").first
        tip = thumb.get_attribute("title") or ""
        assert "第 1 张" in tip
        thumb.click()
        lightbox_hidden = page.evaluate(
            "() => { const el = document.getElementById('v2-lightbox'); return !el || el.hidden; }"
        )
        assert lightbox_hidden
        browser.close()


def test_ac_a1_09_close_confirm_keep_draft(wizard_server) -> None:
    """AC-A1-09 · 2b 改过名称后 Esc → 确认；保留后再开名称仍在。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _route_preview(page)
        _wizard_quick_folder_to_confirm(page)
        page.locator("#v2-wizard-mode-fine").click()
        page.locator("#v2-wizard-start").click()
        _wait_visible(page, "v2-wizard-step-fine")
        page.locator("#v2-wizard-trip-title").fill("保留草稿名")
        page.keyboard.press("Escape")
        page.wait_for_selector(".studio__modal", timeout=5000)
        page.locator(".studio__modal button", has_text="保留并关闭").click()
        page.wait_for_function(
            "() => { const w = document.getElementById('v2-wizard-root'); return !w || w.hidden; }"
        )
        _open_wizard(page)
        page.wait_for_function(
            """() => {
              const el = document.getElementById('v2-wizard-step-fine');
              return el && !el.hidden;
            }"""
        )
        assert page.locator("#v2-wizard-trip-title").input_value() == "保留草稿名"
        browser.close()


def test_ac_a1_09_close_confirm_discard_resets_to_step1(wizard_server) -> None:
    """AC-A1-09 · 丢弃并关闭后重开 → Step1，不残留文件夹/精细步。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _route_preview(page)
        _wizard_quick_folder_to_confirm(page)
        page.locator("#v2-wizard-mode-fine").click()
        page.locator("#v2-wizard-start").click()
        _wait_visible(page, "v2-wizard-step-fine")
        page.locator("#v2-wizard-trip-title").fill("应被丢弃")
        page.keyboard.press("Escape")
        page.wait_for_selector(".studio__modal", timeout=5000)
        page.locator(".studio__modal button", has_text="丢弃并关闭").click()
        page.wait_for_function(
            "() => { const w = document.getElementById('v2-wizard-root'); return !w || w.hidden; }"
        )
        draft = page.evaluate(
            "() => sessionStorage.getItem('travelogue.studio.importDraft')"
        )
        assert draft in (None, "", "{}") or (
            not json.loads(draft or "{}").get("albumPath")
        )

        _open_wizard(page)
        page.wait_for_function(
            """() => {
              const pick = document.getElementById('v2-wizard-step-pick');
              const fine = document.getElementById('v2-wizard-step-fine');
              return pick && !pick.hidden && fine && fine.hidden;
            }"""
        )
        assert page.locator("#v2-wizard-step-pick").is_visible()
        assert page.locator("#v2-wizard-step-fine").is_hidden()
        browser.close()


def test_ac_a1_10_warn_summary_cull_off(wizard_server) -> None:
    """AC-A1-10 / AC-F3 · 全部保留 → warn 摘要 + payload keep_all。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _route_harness_import_mocks(page, photo_cull_enabled=False)
        _wizard_quick_folder_to_confirm(page)
        page.locator("#v2-wizard-photo-adjust").click()
        page.locator("#v2-wizard-photo-mode-keep-all").check()
        summary = page.locator("#v2-wizard-photo-summary")
        assert "全部保留" in summary.inner_text()
        assert "v2-wizard__photo-summary--warn" in (summary.get_attribute("class") or "")
        page.locator("#v2-wizard-start").click()
        _wait_visible(page, "v2-import-cancel")
        pending = page.evaluate(
            "() => JSON.parse(sessionStorage.getItem('travelogue.studio.activePending') || '{}')"
        )
        assert pending.get("photoKeepMode") == "keep_all"
        assert pending.get("photoCullEnabled") is False
        browser.close()


def test_ac_a1_13_fine_cta_label(wizard_server) -> None:
    """A1-13 · 2b 主 CTA「按这些偏好开始 →」。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _route_preview(page)
        _wizard_quick_folder_to_confirm(page)
        page.locator("#v2-wizard-mode-fine").click()
        page.locator("#v2-wizard-start").click()
        _wait_visible(page, "v2-wizard-step-fine")
        assert (
            page.locator("#v2-wizard-start-fine").inner_text().strip()
            == "按这些偏好开始 →"
        )
        browser.close()
