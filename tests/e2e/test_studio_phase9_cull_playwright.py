"""Phase 9 · Studio UX Playwright (AC-P9-UX-02/03)."""

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

CULL_LINE = "经挑选 10 张进入排版（精选 2 张已为您保留）"


def _open_wizard(page) -> None:
    page.evaluate(
        """
        async () => {
          const mod = await import('/__studio/homepage-v2/import-entry.js');
          mod.openImportSheet();
        }
        """
    )
    _wait_visible(page, "v2-wizard-root")


def _unhide_bento_for_narrow_viewport(page) -> None:
    """<768px 会显示 unsupported 并隐藏 #v2-bento-main；FirstSuccess 在其内，窄屏 CSS 测试需先露出。"""
    page.evaluate(
        """
        () => {
          const u = document.getElementById('v2-unsupported');
          const m = document.getElementById('v2-bento-main');
          if (u) u.hidden = true;
          if (m) m.hidden = false;
        }
        """
    )


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
        msg = _success_dialog_text(page)
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


def test_ac_p9_ux_cluster_notice_non_blocking(studio_server) -> None:
    """UX-P3-04 · clusterNotice 非阻断 toast（v2 first-success）。"""
    notice = "部分照片缺少位置信息，已按时间顺序排版"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"], "dev=1&studioFixture=multi")
        page.evaluate(
            """
            async (payload) => {
              window.studioToast = function(msg) {
                var el = document.createElement('div');
                el.className = 'studio__toast';
                el.id = 'ux-cluster-notice-toast';
                el.textContent = msg;
                document.body.appendChild(el);
              };
              const mod = await import('/__studio/homepage-v2/first-success.js');
              mod.showFirstSuccess({ result: payload });
            }
            """,
            {
                "tripId": "ux-trip",
                "title": "测试",
                "photoCount": 12,
                "clusterNotice": notice,
            },
        )
        page.wait_for_selector("#ux-cluster-notice-toast", timeout=10_000)
        assert page.locator("#ux-cluster-notice-toast").inner_text() == notice
        _wait_visible(page, "v2-success-open")
        browser.close()


def test_ac_p9_ux_04_max_photos_warn_non_blocking(studio_server) -> None:
    """AC-P9-UX-04 · maxPhotos WARN 非阻断 toast（v2 first-success）。"""
    warn = "共 297 张进入排版，超过建议上限 250 张，生成可能较慢"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"], "dev=1&studioFixture=multi")
        page.evaluate(
            """
            async (payload) => {
              window.studioToast = function(msg) {
                var el = document.createElement('div');
                el.className = 'studio__toast';
                el.id = 'ux-cull-warn-toast';
                el.textContent = msg;
                document.body.appendChild(el);
              };
              const mod = await import('/__studio/homepage-v2/first-success.js');
              mod.showFirstSuccess({ result: payload });
            }
            """,
            {
                "tripId": "ux-trip",
                "title": "测试",
                "photoCount": 297,
                "cullUserLine": "经挑选 297 张进入排版",
                "cullWarn": warn,
            },
        )
        page.wait_for_selector("#ux-cull-warn-toast", timeout=10_000)
        assert page.locator("#ux-cull-warn-toast").inner_text() == warn
        assert "超过建议上限" in warn
        _wait_visible(page, "v2-success-open")
        assert "经挑选" in _success_dialog_text(page)
        browser.close()


def test_ac_p9_ux_05_fail_open_no_cull_line(studio_server) -> None:
    """AC-P9-UX-05 · cull 失败/fail-open 时成功态无 cullUserLine 第二行。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"], "dev=1&studioFixture=multi")
        page.evaluate(
            """
            async () => {
              window.studioToast = function() {};
              const mod = await import('/__studio/homepage-v2/first-success.js');
              mod.showFirstSuccess({
                result: {
                  tripId: 'ux-trip',
                  title: '测试',
                  photoCount: 12,
                  cullUserLine: '',
                },
              });
            }
            """
        )
        _wait_visible(page, "v2-success-open")
        text = _success_dialog_text(page)
        assert "已生成" in text
        assert "经挑选" not in text
        browser.close()


def test_ac_p9_ux_06_compact_success_msg_no_overflow(studio_server) -> None:
    """AC-P9-UX-06 · 390px 成功 toast 文案不横向溢出。"""
    long_line = "经挑选 120 张进入排版（精选 15 张已为您保留）"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        _goto_v2(page, studio_server["base"], "dev=1&studioFixture=multi")
        _unhide_bento_for_narrow_viewport(page)
        page.evaluate(
            """
            async (line) => {
              window.studioToast = function() {};
              const mod = await import('/__studio/homepage-v2/first-success.js');
              mod.showFirstSuccess({
                result: {
                  tripId: 'ux-trip',
                  title: '京都 · 雨后初晴的慢旅行',
                  photoCount: 120,
                  featuredCount: 15,
                  cullUserLine: line,
                },
              });
            }
            """,
            long_line,
        )
        _wait_visible(page, "v2-success-open")
        overflow = page.evaluate(
            """
            () => {
              const ids = ['v2-success-msg', 'v2-success-details'];
              return ids.every((id) => {
                const el = document.getElementById(id);
                if (!el || el.hidden) return true;
                return el.scrollWidth <= el.clientWidth + 2;
              });
            }
            """
        )
        assert overflow is True
        browser.close()


def test_ac_f1_photo_cull_disabled_success_copy(studio_server) -> None:
    """AC-F1-09 · photoCullEnabled=false 时不出现「经挑选」，展示 N/M 文案。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"], "dev=1&studioFixture=multi")
        page.evaluate(
            """
            async () => {
              const mod = await import('/__studio/homepage-v2/first-success.js');
              mod.showFirstSuccess({
                result: {
                  tripId: 'f1-trip',
                  title: '预筛选集',
                  photoCount: 58,
                  layoutEligibleCount: 55,
                  photoCullEnabled: false,
                  cullUserLine: '',
                },
              });
            }
            """
        )
        _wait_visible(page, "v2-success-open")
        text = _success_dialog_text(page)
        assert "经挑选" not in text
        assert "不做智能挑选" in text
        assert "58" in text
        assert "55" in text
        assert "极低清晰度" in text
        browser.close()


def test_ac_f1_07_photo_cull_checkbox_no_overflow_390(studio_server) -> None:
    """AC-F1-07 · 390px 视口 Wizard 照片处理 checkbox 区不横向溢出。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        _goto_v2(page, studio_server["base"], "dev=1")
        _unhide_bento_for_narrow_viewport(page)
        page.evaluate(
            """
            () => {
              const u = document.getElementById('v2-unsupported');
              if (u) u.hidden = true;
            }
            """
        )
        _open_wizard(page)
        page.locator("#v2-wizard-more-import summary").click()
        page.locator("#v2-wizard-album-path").fill("/harness/album")
        page.locator("#v2-wizard-path-submit").click()
        _wait_visible(page, "v2-wizard-step-confirm")
        page.locator("#v2-wizard-photo-adjust").click()
        page.evaluate(
            """
            () => {
              const drawer = document.getElementById('v2-wizard-photo-drawer');
              if (drawer) drawer.hidden = false;
              const risk = document.getElementById('v2-wizard-photo-keep-all-risk');
              if (risk) {
                risk.hidden = false;
                risk.textContent = '照片很多时成册更密、导出更长，观感可能变碎。';
              }
            }
            """
        )
        overflow = page.evaluate(
            """
            () => {
              const drawer = document.getElementById('v2-wizard-photo-drawer');
              if (!drawer) return false;
              return drawer.scrollWidth <= drawer.clientWidth + 2;
            }
            """
        )
        assert overflow is True
        browser.close()


def test_ac_f1_08_mode_switch_keeps_photo_cull_checkbox(studio_server) -> None:
    """AC-F1-08 / AC-F3 · 快速/精细模式切换不重置照片处理三选一。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        _goto_v2(page, studio_server["base"], "dev=1")
        _open_wizard(page)
        page.locator("#v2-wizard-more-import summary").click()
        page.locator("#v2-wizard-album-path").fill("/harness/album")
        page.locator("#v2-wizard-path-submit").click()
        _wait_visible(page, "v2-wizard-step-confirm")
        page.locator("#v2-wizard-photo-adjust").click()
        page.locator("#v2-wizard-photo-mode-keep-all").check()
        page.locator("#v2-wizard-mode-fine").click()
        keep_all_fine = page.locator("#v2-wizard-photo-mode-keep-all").is_checked()
        page.locator("#v2-wizard-mode-quick").click()
        keep_all_quick = page.locator("#v2-wizard-photo-mode-keep-all").is_checked()
        assert keep_all_fine and keep_all_quick
        browser.close()


def test_ac_f1_09_photo_cull_disabled_success_copy_m_equals_n(studio_server) -> None:
    """AC-F1-09 · cull 关且 M=N 时展示单数字文案，无「经挑选」。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"], "dev=1&studioFixture=multi")
        page.evaluate(
            """
            async () => {
              const mod = await import('/__studio/homepage-v2/first-success.js');
              mod.showFirstSuccess({
                result: {
                  tripId: 'f1-trip-eq',
                  title: '精选集',
                  photoCount: 30,
                  layoutEligibleCount: 30,
                  photoCullEnabled: false,
                  cullUserLine: '',
                },
              });
            }
            """
        )
        _wait_visible(page, "v2-success-open")
        text = _success_dialog_text(page)
        assert "经挑选" not in text
        assert "不做智能挑选" in text
        assert "30" in text
        assert "极低清晰度" not in text
        browser.close()


def test_demo_first_success_hides_set_preview(studio_server) -> None:
    """BUG-01 · 示例成功页不得出现无效的「设为首页预览」。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"], "dev=1&studioFixture=empty")
        page.evaluate(
            """
            async () => {
              const mod = await import('/__studio/homepage-v2/first-success.js');
              mod.showFirstSuccess({
                result: {
                  tripId: 'demo-album',
                  title: '斯里兰卡见闻录',
                  photoCount: 16,
                  segmentCount: 3,
                },
              });
            }
            """
        )
        _wait_visible(page, "v2-success-open")
        set_preview = page.locator("#v2-success-set-preview")
        assert set_preview.count() == 1
        assert not set_preview.is_visible()
        page.evaluate(
            """
            async () => {
              const mod = await import('/__studio/homepage-v2/first-success.js');
              mod.showFirstSuccess({
                result: {
                  tripId: 'user-trip',
                  title: '京都 · 雨后',
                  photoCount: 12,
                  segmentCount: 2,
                },
              });
            }
            """
        )
        page.wait_for_function(
            "() => { const el = document.getElementById('v2-success-set-preview'); return el && !el.hidden; }"
        )
        browser.close()


def test_permanent_import_failure_offers_change_folder(studio_server) -> None:
    """BUG-04 · 永久路径错误主按钮是更换文件夹，并保留留在首页。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"], "dev=1&studioFixture=empty")
        page.evaluate(
            """
            async () => {
              const mod = await import('/__studio/homepage-v2/import-failed.js');
              try {
                sessionStorage.setItem(
                  'travelogue.studio.activePending',
                  JSON.stringify({ albumPath: 'C:/__travelogue_missing_folder__' })
                );
              } catch (e) {}
              mod.showImportFailed({
                code: 'E_STUDIO_ALBUM_DENIED',
                message: '不允许从该路径导入',
              });
            }
            """
        )
        _wait_visible(page, "v2-failure-retry")
        assert page.locator("#v2-failure-retry").inner_text().strip() == "更换文件夹"
        assert page.locator("#v2-failure-stay").is_visible()
        assert "Sheet" not in page.locator("#v2-failure-hint").inner_text()
        browser.close()
