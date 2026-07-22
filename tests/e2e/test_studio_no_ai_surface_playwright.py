"""NAS · No-AI Surface 默认面 Playwright（AC-NAS-01/02/03/04/05/06/14/15/16 + HTTP 13）。

对照 docs/ACCEPTANCE-NO-AI-SURFACE-V1.md。默认门控 off（不设 TRAVELOGUE_AI_SURFACE）。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.e2e.test_studio_home_v2_ac_playwright import _goto_v2, _wait_visible
from tests.integration.studio.test_studio_server import _free_port, _start_studio_server
from tests.preview_arc14_fixtures import (
    arc14_studio_browser,
    demo_assets_available,
    wait_preview_dock,
)
from travelogue.web.studio_jobs import reset_job_store

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]

COPY_NAS_FS_01 = "游记已做好，可预览与导出长图。"


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
        yield {"base": base, "trips_dir": trips_dir}
    finally:
        server.shutdown()
        server.server_close()


def _goto_v2_clean(page, base: str, query: str = "") -> None:
    """冷启：不预写 capabilityCard seen（AC-NAS-01）。"""
    url = base + "/" + (("?" + query) if query else "")
    page.goto(url, wait_until="networkidle")


def _wait_ai_surface_off(page) -> None:
    enabled = page.evaluate(
        """
        async () => {
          const m = await import('/__studio/js/ai-surface.js');
          await m.ensureAiSurfaceHydrated();
          return m.isAiSurfaceEnabled();
        }
        """
    )
    assert enabled is False


def _open_preview_sheet_book(page) -> None:
    wait_preview_dock(page)
    _wait_ai_surface_off(page)
    opened = page.evaluate(
        """() => {
          const root = document.querySelector('.preview-sheet-root');
          return !!(root && root.classList.contains('preview-sheet-root--open'));
        }"""
    )
    if not opened:
        page.locator(".preview-toolbar__menu-btn").click(force=True)
        page.wait_for_function(
            """() => {
              const root = document.querySelector('.preview-sheet-root');
              return !!(root && root.classList.contains('preview-sheet-root--open'));
            }""",
            timeout=10_000,
        )
    # UI Detail 波次下 tab 可能在视口外；用 JS 切换避免 Playwright 几何点击失败
    page.evaluate(
        """() => {
          const tab = document.querySelector('.preview-sheet__tab[data-sheet-tab="book"]');
          if (tab) tab.click();
        }"""
    )
    page.wait_for_timeout(200)


def test_ac_nas_01_no_capability_card(studio_server) -> None:
    """AC-NAS-01 · 干净首访无能力卡。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        _goto_v2_clean(page, studio_server["base"], "dev=1")
        _wait_visible(page, "v2-frame")
        _wait_ai_surface_off(page)
        state = page.evaluate(
            """
            async () => {
              const m = await import('/__studio/js/capability-card.js');
              const root = document.getElementById('studio-capability-card-root');
              return {
                showReturned: m.showCapabilityCard(),
                visible: m.isCapabilityCardVisible(),
                rootHidden: !root || !!root.hidden,
              };
            }
            """
        )
        assert state["showReturned"] is False
        assert state["visible"] is False
        assert state["rootHidden"] is True
        browser.close()


def test_ac_nas_02_settings_hides_ai_zone(studio_server) -> None:
    """AC-NAS-02 · 设置无 AI zone / 写作引擎入口。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        _goto_v2(page, studio_server["base"], "dev=1")
        _wait_visible(page, "v2-frame")
        _wait_ai_surface_off(page)
        page.locator("#v2-settings-toggle").click()
        page.wait_for_function(
            "() => { const p = document.getElementById('v2-settings-popover'); return p && !p.hidden; }",
            timeout=10_000,
        )
        state = page.evaluate(
            """
            () => {
              const zone = document.getElementById('v2-settings-zone-ai');
              const entry = document.getElementById('studio-llm-settings-entry');
              const pop = document.getElementById('v2-settings-popover');
              const text = (pop && pop.innerText) || '';
              return {
                zoneHidden: !zone || !!zone.hidden,
                hasEntryVisible: !!(entry && !entry.hidden && entry.offsetParent !== null),
                text,
              };
            }
            """
        )
        assert state["zoneHidden"] is True
        assert state["hasEntryVisible"] is False
        assert "写作引擎" not in state["text"]
        assert "AI 文案" not in state["text"]
        browser.close()


def test_ac_nas_03_help_without_h7(studio_server) -> None:
    """AC-NAS-03 · 帮助无 H7 / AI 文案配置句。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        _goto_v2(page, studio_server["base"], "dev=1")
        _wait_visible(page, "v2-frame")
        page.evaluate(
            """
            async () => {
              const mod = await import('/__studio/js/help-drawer.js');
              mod.openHelpDrawer({ source: 'test' });
            }
            """
        )
        page.wait_for_selector(".studio-help-drawer__item summary", timeout=5000)
        titles = page.evaluate(
            """
            () => Array.from(document.querySelectorAll('.studio-help-drawer__item summary'))
              .map((el) => (el.textContent || '').trim())
            """
        )
        blob = "\n".join(titles)
        assert titles
        assert "要不要配置 AI 文案" not in blob
        assert "AI 文案" not in blob
        assert "写作引擎" not in blob
        browser.close()


def test_ac_nas_04_first_success_copy(studio_server) -> None:
    """AC-NAS-04 · FirstSuccess 下一句 = COPY-NAS-FS-01。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        _goto_v2(page, studio_server["base"], "dev=1")
        _wait_visible(page, "v2-frame")
        page.evaluate(
            """
            async () => {
              const mod = await import('/__studio/homepage-v2/first-success.js');
              mod.showFirstSuccess({
                result: {
                  tripId: 'nas-fs',
                  title: '测试游记',
                  photoCount: 6,
                  featuredCount: 1,
                  segmentCount: 1,
                },
              });
            }
            """
        )
        page.wait_for_selector("#v2-success-next-hint", timeout=5000)
        lead = page.evaluate(
            """
            () => {
              const el = document.querySelector('#v2-success-next-hint .v2-first-success__guidance-lead');
              return el ? (el.textContent || '').trim() : '';
            }
            """
        )
        assert lead == COPY_NAS_FS_01
        browser.close()


def test_ac_nas_15_llm_setup_deeplink_noop(studio_server) -> None:
    """AC-NAS-15 · ?llmSetup=1 不弹写作引擎 Modal。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        _goto_v2_clean(page, studio_server["base"], "dev=1&llmSetup=1")
        _wait_visible(page, "v2-frame")
        _wait_ai_surface_off(page)
        page.wait_for_timeout(800)
        hidden = page.evaluate(
            """
            () => {
              const r = document.getElementById('studio-llm-settings-root');
              return !r || !!r.hidden;
            }
            """
        )
        assert hidden is True
        browser.close()


def test_ac_nas_16_help_replay_keeps_ai_dormant(studio_server) -> None:
    """AC-NAS-16 · 帮助重播后仍无能力卡 / stub banner。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        _goto_v2_clean(page, studio_server["base"], "dev=1")
        _wait_visible(page, "v2-frame")
        _wait_ai_surface_off(page)
        page.evaluate(
            """
            async () => {
              const help = await import('/__studio/js/help-onboarding.js');
              help.replayHelpHints();
              const cap = await import('/__studio/js/capability-card.js');
              cap.maybeShowCapabilityCard();
              cap.showCapabilityCard();
            }
            """
        )
        page.wait_for_timeout(400)
        state = page.evaluate(
            """
            async () => {
              const cap = await import('/__studio/js/capability-card.js');
              const root = document.getElementById('studio-capability-card-root');
              const banner = document.getElementById('studio-home-stub-banner');
              return {
                visible: cap.isCapabilityCardVisible(),
                rootHidden: !root || !!root.hidden,
                bannerHidden: !banner || !!banner.hidden,
              };
            }
            """
        )
        assert state["visible"] is False
        assert state["rootHidden"] is True
        assert state["bannerHidden"] is True
        browser.close()


def test_ac_nas_13_narrate_http_403(studio_server) -> None:
    """AC-NAS-13 · POST /narrate → 403 E_AI_SURFACE_DISABLED。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(studio_server["base"] + "/", wait_until="domcontentloaded")
        resp = page.request.post(
            studio_server["base"] + "/__travelogue/narrate",
            data=json.dumps({"tripId": "any-trip"}),
            headers={"Content-Type": "application/json"},
        )
        assert resp.status == 403
        body = resp.json()
        assert body.get("error") == "E_AI_SURFACE_DISABLED"
        assert "写作引擎" not in (body.get("message") or "")
        browser.close()


@pytest.fixture
def arc14_trip(tmp_path):
    if not demo_assets_available():
        pytest.skip("demo assets not present")
    return tmp_path


def test_ac_nas_05_06_14_preview_no_ai_surface(arc14_trip) -> None:
    """AC-NAS-05/06/14 · Sheet/Dock 无 AI 入口；会话 0× POST /narrate。"""
    narrates: list[str] = []
    with arc14_studio_browser(arc14_trip) as (_pw, page, _base, _trip_id):
        page.on(
            "request",
            lambda req: narrates.append(req.url)
            if req.method == "POST" and "/__travelogue/narrate" in req.url
            else None,
        )
        _open_preview_sheet_book(page)
        sheet_text = page.evaluate(
            """() => {
              const el = document.querySelector('.preview-sheet');
              return el ? (el.innerText || '') : '';
            }"""
        )
        assert "重新生成文案" not in sheet_text
        assert "写作引擎" not in sheet_text
        assert "按新感觉重写" not in sheet_text
        assert (
            page.locator('.preview-sheet [data-action="llm"]').count() == 0
        )
        assert (
            page.locator('.preview-sheet [data-action="llm-setup"]').count() == 0
        )

        dock_text = page.evaluate(
            """() => {
              const el = document.querySelector('.preview-task-dock, .preview-toolbar__task-dock, [data-task-dock]');
              return el ? (el.innerText || '') : document.body.innerText || '';
            }"""
        )
        assert "AI 文案已就绪" not in dock_text
        assert "重新生成文案" not in dock_text

        # 打开编辑抽屉（若有）再点保存路径；仍不得触发 narrate
        page.evaluate(
            """() => {
              const edit = document.querySelector(
                '[data-action="edit-book"], [data-action="edit"], .preview-sheet__link[data-action="edit-meta"]'
              );
              if (edit) edit.click();
            }"""
        )
        page.wait_for_timeout(500)
        drawer_text = page.evaluate(
            """() => {
              const d = document.querySelector('.preview-drawer, .preview-edit-overlay');
              return d ? (d.innerText || '') : '';
            }"""
        )
        assert "按新感觉重写" not in drawer_text
        assert narrates == []
