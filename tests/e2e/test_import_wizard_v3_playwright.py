"""Import Wizard v3 · AC 自动验收 e2e（Playwright）。

对照 docs/PRD-IMPORT-SHEET-v3-WIZARD.md §12 / §16.9：
  AC-IW-01/02 一屏无滚轮 · AC-IW-03 验货区 · AC-IW-04 默认无 checkbox
  AC-IW-08 日期校验 · AC-IW-09 记住精细 · AC-IW-09b 首次强制快速
  AC-IW-DS-01 下游 Importing + FirstSuccess 长图 CTA · AC-IW-DS-04 Importing 中拦截
  AC-IW-DS-05 上传失败重试回 Step 1 · AC-IW-DS-02 精细 mode payload · AC-IW-DS-07 刷新续 poll
  AC-IW-DS-03 关智能挑选 FirstSuccess 文案 · AC-IW-DS-06 上传路径
  DS-03 payload 字段 snapshot · DS-04 Success→预览链接 200

Wizard 为唯一导入入口（RET-3 · Sheet 已删除）。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tests.integration.studio.test_studio_server import _free_port, _start_studio_server
from tests.unit.web.fixtures.import_wizard_payload_contract import (
    ALLOWED_KEYS,
    FINE_CRAFT_REQUIRED_KEYS,
    QUICK_SHARE_REQUIRED_KEYS,
)
from travelogue.web.studio_jobs import reset_job_store

_THUMB_GIF = (
    "data:image/gif;base64,"
    "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
)

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


@pytest.fixture
def wizard_server(tmp_path: Path):
    trips_dir = tmp_path / "trips-wizard"
    trips_dir.mkdir(parents=True, exist_ok=True)
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
        assert "已关闭智能挑选" in summary
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


def _wizard_to_confirm(page) -> None:
    page.locator("#v2-wizard-more-import summary").click()
    page.locator("#v2-wizard-album-path").fill("/harness/album")
    page.locator("#v2-wizard-path-submit").click()
    _wait_visible(page, "v2-wizard-step-confirm")


def test_ac_iw_ds_02_fine_craft_payload(wizard_server) -> None:
    """AC-IW-DS-02 · Wizard 精细路径 → activePending.mode=fine_craft + layoutDensity。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _open_wizard(page)
        _wizard_to_confirm(page)
        page.locator("#v2-wizard-mode-fine").click()
        page.locator("#v2-wizard-start").click()
        _wait_visible(page, "v2-wizard-step-fine")
        page.locator("#v2-wizard-trip-title").fill("京都秋色")
        page.locator("#v2-wizard-advanced summary").click()
        page.locator('input[name="v2-wizard-layout-density"][value="hero_first"]').check()
        page.locator("#v2-wizard-start-fine").click()
        _wait_visible(page, "v2-import-cancel")

        pending = page.evaluate(
            "() => JSON.parse(sessionStorage.getItem('travelogue.studio.activePending') || '{}')"
        )
        assert pending.get("mode") == "fine_craft"
        assert pending.get("layoutDensity") == "hero_first"
        assert pending.get("title") == "京都秋色"
        browser.close()


def test_ac_iw_ds_04_importing_blocks_cta(wizard_server) -> None:
    """AC-IW-DS-04 · Importing 进行中尝试开 Wizard → toast，Wizard 不打开。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, wizard_server["base"], "dev=1&studioState=importing")
        page.wait_for_selector("#v2-import-cancel", timeout=20_000)
        page.evaluate(
            """
            async () => {
              const mod = await import('/__studio/homepage-v2/import-wizard.js');
              mod.openImportWizard();
            }
            """
        )
        wizard_hidden = page.evaluate(
            "() => { const w = document.getElementById('v2-wizard-root'); return !w || w.hidden; }"
        )
        assert wizard_hidden
        toast = page.locator(".studio__toast", has_text="正在制作中").inner_text(timeout=5000)
        assert "正在制作中" in toast
        browser.close()


def test_ac_iw_ds_07_reload_resumes_import_not_wizard(wizard_server) -> None:
    """AC-IW-DS-07 · 导入中刷新 → resumeImportIfNeeded 续 poll，不进 Wizard。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(
            page,
            wizard_server["base"],
            "dev=1&studioState=importing-resume&studioJob=running",
        )
        page.wait_for_selector("#v2-import-cancel", timeout=20_000)
        page.reload(wait_until="networkidle")
        page.wait_for_selector("#v2-import-cancel", timeout=20_000)
        wizard_hidden = page.evaluate(
            "() => { const w = document.getElementById('v2-wizard-root'); return !w || w.hidden; }"
        )
        assert wizard_hidden
        job_id = page.evaluate(
            "() => sessionStorage.getItem('travelogue.studio.activeJobId')"
        )
        assert job_id == "harness-job-1"
        browser.close()


def _route_harness_import_mocks(
    page,
    *,
    photo_count: int = 129,
    layout_eligible: int = 120,
    photo_cull_enabled: bool = False,
    folder_name: str = "harness-album",
    thumbs: list[str] | None = None,
    preview_ok: bool = True,
    import_bodies: list[dict[str, Any]] | None = None,
    preview_url: str = "/harness-trip/index.html",
    import_mode: str = "quick_share",
) -> None:
    """Playwright 路由：album-preview + import + status（不依赖真实 pipeline）。"""

    def _album_preview(route) -> None:
        if not preview_ok:
            route.fulfill(
                status=500,
                content_type="application/json",
                body=json.dumps({"ok": False, "error": "preview_failed"}),
            )
            return
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "ok": True,
                    "photoCount": photo_count,
                    "folderName": folder_name,
                    "thumbs": thumbs if thumbs is not None else [],
                }
            ),
        )

    def _import_post(route) -> None:
        try:
            raw = route.request.post_data or "{}"
            body = json.loads(raw)
        except Exception:
            body = {}
        if import_bodies is not None:
            import_bodies.append(body)
        route.fulfill(
            status=202,
            content_type="application/json",
            body=json.dumps({"jobId": "harness-job-1"}),
        )

    def _status_poll(route) -> None:
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "jobId": "harness-job-1",
                    "status": "succeeded",
                    "result": {
                        "tripId": "harness-trip",
                        "title": "Harness · 测试",
                        "previewUrl": preview_url,
                        "photoCount": photo_count,
                        "layoutEligibleCount": layout_eligible,
                        "photoCullEnabled": photo_cull_enabled,
                        "segmentCount": 3,
                        "mode": import_mode,
                        "importMode": import_mode,
                    },
                }
            ),
        )

    def _preview_html(route) -> None:
        route.fulfill(
            status=200,
            content_type="text/html; charset=utf-8",
            body="<!doctype html><title>Harness Trip</title><h1>ok</h1>",
        )

    page.route("**/__travelogue/album-preview", _album_preview)
    page.route("**/__travelogue/import", _import_post)
    page.route("**/__travelogue/status**", _status_poll)
    page.route(f"**{preview_url}", _preview_html)


def _wizard_quick_folder_to_confirm(page) -> None:
    _open_wizard(page)
    page.locator("#v2-wizard-more-import summary").click()
    page.locator("#v2-wizard-album-path").fill("/harness/album")
    page.locator("#v2-wizard-path-submit").click()
    _wait_visible(page, "v2-wizard-step-confirm")


def test_ac_iw_ds_03_cull_disabled_first_success_copy(wizard_server) -> None:
    """AC-IW-DS-03 · 关智能挑选 + 129 张 → FirstSuccess「不做智能挑选 · N/M 张…」。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _route_harness_import_mocks(
            page,
            photo_count=129,
            layout_eligible=120,
            photo_cull_enabled=False,
        )
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _wizard_quick_folder_to_confirm(page)

        page.locator("#v2-wizard-photo-adjust").click()
        _wait_visible(page, "v2-wizard-photo-drawer")
        page.locator("#v2-wizard-photo-cull").uncheck()

        page.locator("#v2-wizard-start").click()
        page.wait_for_selector("#v2-success-open", timeout=30_000)

        details = page.locator("#v2-success-details").inner_text()
        assert "不做智能挑选" in details
        assert "129" in details
        assert "120" in details
        assert "经挑选" not in details
        browser.close()


def test_ac_iw_ds_06_upload_path_reaches_importing(wizard_server, tmp_path: Path) -> None:
    """AC-IW-DS-06 · Wizard 浏览器上传 → activePending.uploadForm + Importing 面板。"""
    upload_dir = tmp_path / "browser-upload"
    upload_dir.mkdir()
    for i in range(3):
        (upload_dir / f"trip-{i}.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 64)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _route_harness_import_mocks(page, photo_count=3, layout_eligible=3)
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _open_wizard(page)
        page.locator("#v2-wizard-album-upload").set_input_files(str(upload_dir))
        _wait_visible(page, "v2-wizard-step-confirm")
        page.locator("#v2-wizard-start").click()
        page.wait_for_selector("#v2-import-cancel", timeout=20_000)

        pending = page.evaluate(
            "() => JSON.parse(sessionStorage.getItem('travelogue.studio.activePending') || '{}')"
        )
        assert pending.get("uploadForm") is True
        assert pending.get("fileCount") == 3
        assert pending.get("mode") == "quick_share"
        browser.close()


def test_ac_iw_03_verify_line_and_thumbs(wizard_server) -> None:
    """AC-IW-03 · 验货区：folderName + N 张 + ≥1 缩略图。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _route_harness_import_mocks(
            page,
            photo_count=12,
            layout_eligible=12,
            folder_name="京都秋色",
            thumbs=[_THUMB_GIF, _THUMB_GIF],
        )
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _wizard_quick_folder_to_confirm(page)
        page.wait_for_function(
            """
            () => {
              const line = document.getElementById('v2-wizard-verify-line');
              return line && line.textContent && line.textContent.includes('已清点');
            }
            """,
            timeout=10_000,
        )
        line = page.locator("#v2-wizard-verify-line").inner_text()
        assert "京都秋色" in line
        assert "12" in line
        thumbs = page.locator("#v2-wizard-thumbs .v2-wizard__thumb")
        assert thumbs.count() >= 1
        assert page.locator("#v2-wizard-thumbs").is_visible()
        browser.close()


def test_ac_iw_03_preview_degrade_still_startable(wizard_server) -> None:
    """AC-IW-03 · preview 失败降级：不阻塞确认步，仍可开始制作。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _route_harness_import_mocks(page, preview_ok=False, photo_count=0)
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _wizard_quick_folder_to_confirm(page)
        page.wait_for_timeout(400)
        assert page.locator("#v2-wizard-start").is_enabled()
        page.locator("#v2-wizard-start").click()
        _wait_visible(page, "v2-import-cancel")
        browser.close()


def test_ac_iw_08_date_range_validation(wizard_server) -> None:
    """AC-IW-08 · 开始日期不能晚于结束日期。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _route_harness_import_mocks(page, photo_count=5, layout_eligible=5)
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _wizard_quick_folder_to_confirm(page)
        page.locator("#v2-wizard-mode-fine").click()
        page.locator("#v2-wizard-start").click()
        _wait_visible(page, "v2-wizard-step-fine")
        page.locator("#v2-wizard-advanced summary").click()
        page.locator("#v2-wizard-date-start").fill("2025-08-10")
        page.locator("#v2-wizard-date-end").fill("2025-08-01")
        page.locator("#v2-wizard-start-fine").click()
        err = page.locator("#v2-wizard-error-fine").inner_text(timeout=5000)
        assert "开始日期不能晚于结束日期" in err
        assert page.locator("#v2-wizard-step-fine").is_visible()
        browser.close()


def test_ac_iw_09_remembers_fine_craft(wizard_server) -> None:
    """AC-IW-09 · 非首次 + 上次精细 → 精细卡默认选中。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        page.evaluate(
            """
            () => {
              localStorage.setItem('travelogue.studio.importWizardVisited', '1');
              localStorage.setItem('travelogue.studio.lastImportMode', 'fine_craft');
            }
            """
        )
        _open_wizard(page)
        page.locator("#v2-wizard-more-import summary").click()
        page.locator("#v2-wizard-album-path").fill("/harness/album")
        page.locator("#v2-wizard-path-submit").click()
        _wait_visible(page, "v2-wizard-step-confirm")
        assert page.locator("#v2-wizard-mode-fine").get_attribute("aria-checked") == "true"
        assert page.locator("#v2-wizard-mode-quick").get_attribute("aria-checked") == "false"
        browser.close()


def test_ac_iw_ds_01_first_success_longshot_cta(wizard_server) -> None:
    """AC-IW-DS-01 后半 · 快速路径成功 → FirstSuccess 主 CTA=保存长图。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _route_harness_import_mocks(
            page,
            photo_count=8,
            layout_eligible=8,
            photo_cull_enabled=True,
            import_mode="quick_share",
        )
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _wizard_quick_folder_to_confirm(page)
        page.locator("#v2-wizard-start").click()
        page.wait_for_selector("#v2-success-open", timeout=30_000)
        cta = page.locator("#v2-success-open").inner_text().strip()
        assert cta == "保存长图"
        browser.close()


def test_ds_03_wizard_payload_field_snapshot_quick(wizard_server) -> None:
    """DS-03 · 快速路径 POST body 键集符合冻结契约。"""
    bodies: list[dict[str, Any]] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _route_harness_import_mocks(
            page,
            photo_count=6,
            layout_eligible=6,
            import_bodies=bodies,
        )
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _wizard_quick_folder_to_confirm(page)
        page.wait_for_function(
            """
            () => {
              const line = document.getElementById('v2-wizard-verify-line');
              return line && /已清点/.test(line.textContent || '');
            }
            """,
            timeout=10_000,
        )
        page.locator("#v2-wizard-start").click()
        page.wait_for_selector("#v2-import-cancel", timeout=20_000)
        assert bodies, "expected POST /import body"
        quick = bodies[-1]
        assert QUICK_SHARE_REQUIRED_KEYS <= set(quick.keys())
        assert set(quick.keys()) <= ALLOWED_KEYS
        assert quick.get("mode") == "quick_share"
        assert quick.get("albumPath") == "/harness/album"
        assert quick.get("eligibleCount") == 6
        browser.close()


def test_ds_03_wizard_payload_field_snapshot_fine(wizard_server) -> None:
    """DS-03 · 精细路径 POST body 含 layoutDensity，键集不越界。"""
    bodies: list[dict[str, Any]] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _route_harness_import_mocks(
            page,
            photo_count=6,
            layout_eligible=6,
            import_bodies=bodies,
            import_mode="fine_craft",
        )
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _wizard_quick_folder_to_confirm(page)
        page.locator("#v2-wizard-mode-fine").click()
        page.locator("#v2-wizard-start").click()
        _wait_visible(page, "v2-wizard-step-fine")
        page.locator("#v2-wizard-trip-title").fill("精细契约")
        page.locator("#v2-wizard-advanced summary").click()
        page.locator('input[name="v2-wizard-layout-density"][value="hero_first"]').check()
        page.locator("#v2-wizard-start-fine").click()
        page.wait_for_selector("#v2-import-cancel", timeout=20_000)
        assert bodies, "expected fine_craft POST /import body"
        fine = bodies[-1]
        assert FINE_CRAFT_REQUIRED_KEYS <= set(fine.keys())
        assert set(fine.keys()) <= ALLOWED_KEYS
        assert fine.get("mode") == "fine_craft"
        assert fine.get("layoutDensity") == "hero_first"
        assert fine.get("title") == "精细契约"
        browser.close()


def test_ds_04_wizard_success_preview_link_200(wizard_server) -> None:
    """DS-04 · Wizard → Success → 预览/Editor 链接 HTTP 200。"""
    preview_url = "/harness-trip/index.html"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _route_harness_import_mocks(
            page,
            photo_count=4,
            layout_eligible=4,
            photo_cull_enabled=True,
            preview_url=preview_url,
            import_mode="fine_craft",
        )
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _wizard_quick_folder_to_confirm(page)
        page.locator("#v2-wizard-mode-fine").click()
        page.locator("#v2-wizard-start").click()
        _wait_visible(page, "v2-wizard-step-fine")
        page.locator("#v2-wizard-trip-title").fill("DS04 预览")
        page.locator("#v2-wizard-start-fine").click()
        page.wait_for_selector("#v2-success-open", timeout=30_000)
        open_btn = page.locator("#v2-success-open")
        assert "卷轴预览" in open_btn.inner_text()
        href = open_btn.get_attribute("href") or ""
        assert preview_url in href
        status = page.evaluate(
            """async (url) => {
              const res = await fetch(url, { method: 'GET' });
              return res.status;
            }""",
            href,
        )
        assert status == 200
        browser.close()
