"""Import Wizard A.1.1 · P2 增量 e2e（Playwright）。

A1-11 决策问句 · A1-12 chips · A1-14 继续编辑细节 · A1-15 首次弱提示 · A1-16 同名脚注。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.e2e.test_import_wizard_a1_playwright import _route_preview
from tests.e2e.test_import_wizard_v3_playwright import (
    _goto_v2,
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


def test_ac_a1_11_decision_group_titles(wizard_server) -> None:
    """A1-11 · 2b 分组标题为决策问句。"""
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
        body = page.locator("#v2-wizard-step-fine").inner_text()
        assert "这趟旅行叫什么？" in body
        assert "想强调什么感觉？" in body
        page.locator("#v2-wizard-advanced summary").click()
        body2 = page.locator("#v2-wizard-step-fine").inner_text()
        assert "照片怎么组织？" in body2
        assert "版面气质怎样？" in body2
        assert "基本信息" not in body2
        browser.close()


def test_ac_a1_12_chip_pressed_and_extra(wizard_server) -> None:
    """A1-12 · chips 按下态 + 扩展文案。"""
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
        chips = page.locator(".v2-wizard__chip[data-fill='v2-wizard-user-notes']")
        assert chips.count() >= 5
        assert page.get_by_role("button", name="风光为主，少写攻略").count() == 1
        chip = page.get_by_role("button", name="第3天最难忘")
        chip.click()
        assert chip.get_attribute("aria-pressed") == "true"
        assert page.locator("#v2-wizard-user-notes").input_value() == "第3天最难忘"
        browser.close()


def test_ac_a1_14_continue_edit_cta(wizard_server) -> None:
    """A1-14 · 从 2b 返回后 CTA「继续编辑细节 →」。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _route_preview(page)
        _wizard_quick_folder_to_confirm(page)
        page.locator("#v2-wizard-mode-fine").click()
        assert page.locator("#v2-wizard-start").inner_text().strip() == "填写细节 →"
        page.locator("#v2-wizard-start").click()
        _wait_visible(page, "v2-wizard-step-fine")
        page.locator("#v2-wizard-back-fine-action").click()
        _wait_visible(page, "v2-wizard-step-confirm")
        assert page.locator("#v2-wizard-mode-fine").get_attribute("aria-checked") == "true"
        assert page.locator("#v2-wizard-start").inner_text().strip() == "继续编辑细节 →"
        browser.close()


def test_ac_a1_15_first_tip_once(wizard_server) -> None:
    """A1-15 · Step1 首次弱提示可关且只出一次。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.add_init_script(
            """
            () => {
              try { localStorage.removeItem('travelogue.studio.importWizardFirstTipDismissed'); } catch (e) {}
            }
            """
        )
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        page.locator("#v2-cta").click()
        _wait_visible(page, "v2-wizard-root")
        tip = page.locator("#v2-wizard-first-tip")
        assert tip.is_visible()
        assert "选一次旅行的文件夹即可" in tip.inner_text()
        page.locator("#v2-wizard-first-tip-dismiss").click()
        assert tip.is_hidden()
        page.locator("#v2-wizard-close-pick").click()
        page.wait_for_function(
            "() => { const w = document.getElementById('v2-wizard-root'); return !w || w.hidden; }"
        )
        page.locator("#v2-cta").click()
        _wait_visible(page, "v2-wizard-root")
        assert page.locator("#v2-wizard-first-tip").is_hidden()
        browser.close()


def test_ac_a1_16_duplicate_title_footnote(wizard_server) -> None:
    """A1-16 · 同名 trip 脚注。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        page.evaluate(
            """
            () => {
              window.V2 = window.V2 || {};
              // store module V2 is not on window; patch via trips cache used by shelf
            }
            """
        )
        # Inject into module store via open path after setting session trips is hard;
        # use page evaluate against import-wizard by setting trips on the shared store.
        page.evaluate(
            """
            async () => {
              const mod = await import('/__studio/homepage-v2/store.js');
              mod.V2.trips = [
                { tripId: 'user-trip-1', title: '贵州暑假游' },
                { tripId: 'demo-2021', title: 'Demo', isDemo: true },
              ];
            }
            """
        )
        _route_preview(page, photo_count=10)
        _wizard_quick_folder_to_confirm(page)
        page.wait_for_function(
            """() => {
              const el = document.getElementById('v2-wizard-dup-note');
              return el && !el.hidden && el.textContent.includes('不会覆盖');
            }"""
        )
        note = page.locator("#v2-wizard-dup-note").inner_text()
        assert "将新建一本，不会覆盖《贵州暑假游》" in note
        page.locator("#v2-wizard-mode-fine").click()
        page.locator("#v2-wizard-start").click()
        _wait_visible(page, "v2-wizard-step-fine")
        fine_note = page.locator("#v2-wizard-dup-note-fine")
        assert fine_note.is_visible()
        assert "贵州暑假游" in fine_note.inner_text()
        browser.close()


def test_wizard_is_sole_import_entry_without_yaml(tmp_path: Path) -> None:
    """RET-3 · CTA 开 Wizard；旧 Sheet 根节点已删除。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir(parents=True, exist_ok=True)
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            _goto_v2(page, base)
            _wait_visible(page, "v2-frame")
            page.locator("#v2-cta").click()
            _wait_visible(page, "v2-wizard-root")
            assert page.locator("#v2-wizard-step-pick").is_visible()
            assert page.evaluate("() => !document.getElementById('v2-sheet-root')")
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
