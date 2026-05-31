"""P10 · Playwright layout tier smoke (390 compact vs 1280 wide)."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.web.studio_jobs import reset_job_store
from tests.test_studio_server import _free_port, _start_studio_server

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]

P10_VIEWPORTS = (
    (1280, "wide"),
    (390, "compact"),
)

MOCK_IMPORT_JOB = {
    "status": "running",
    "stage": "ingest",
    "stageIndex": 1,
    "stageCount": 4,
    "stageHint": "已处理 1/12 张",
}


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


def _wait_empty_hero(page) -> None:
    page.wait_for_function(
        """
        () => {
          const empty = document.getElementById('studio-hero-empty');
          const loading = document.getElementById('studio-hero-loading');
          return empty && !empty.hidden && loading && loading.hidden;
        }
        """,
        timeout=20_000,
    )


def _hide_hero_shells(page) -> None:
    page.evaluate(
        """
        () => {
          [
            'studio-hero-empty', 'studio-hero-returning', 'studio-hero-loading',
            'studio-hero-importing', 'studio-success', 'studio-failure',
          ].forEach(function (id) {
            var el = document.getElementById(id);
            if (el) el.hidden = true;
          });
        }
        """
    )


def _show_importing_demo(page) -> None:
    _hide_hero_shells(page)
    page.evaluate(
        """
        () => {
          var imp = document.getElementById('studio-hero-importing');
          if (imp) imp.hidden = false;
          var layout = document.documentElement.getAttribute('data-studio-layout') || 'wide';
          var eyebrow = document.getElementById('studio-stage-eyebrow');
          var stage = document.getElementById('studio-stage');
          if (layout === 'compact') {
            if (eyebrow) {
              eyebrow.textContent = '第 1 步，共 4 步';
              eyebrow.hidden = false;
              eyebrow.removeAttribute('aria-hidden');
            }
            if (stage) stage.textContent = '正在读取你的照片（已处理 1/12 张）';
          } else {
            if (eyebrow) {
              eyebrow.hidden = true;
              eyebrow.setAttribute('aria-hidden', 'true');
            }
            if (stage) {
              stage.textContent = '第 1 步，共 4 步 · 正在读取你的照片（已处理 1/12 张）';
            }
          }
        }
        """
    )


def _show_importing_via_progress(page) -> None:
    _hide_hero_shells(page)
    page.evaluate(
        """
        async (job) => {
          var imp = document.getElementById('studio-hero-importing');
          if (imp) imp.hidden = false;
          var mod = await import('/__studio/js/progress.js');
          mod.updateProgress(job);
        }
        """,
        MOCK_IMPORT_JOB,
    )


def _show_success(page) -> None:
    _hide_hero_shells(page)
    page.evaluate(
        """
        () => {
          var el = document.getElementById('studio-success');
          if (el) el.hidden = false;
        }
        """
    )


def _show_failure(page) -> None:
    _hide_hero_shells(page)
    page.evaluate(
        """
        () => {
          var el = document.getElementById('studio-failure');
          var hint = document.getElementById('studio-failure-hint');
          var msg = document.getElementById('studio-failure-msg');
          if (el) el.hidden = false;
          if (msg) msg.textContent = '无法读取照片文件夹';
          if (hint) {
            hint.textContent = '请检查路径是否正确，或换一个小文件夹重试。';
            hint.hidden = false;
          }
        }
        """
    )


def _assert_no_horizontal_overflow(page, label: str) -> None:
    overflow = page.evaluate(
        """
        () => document.documentElement.scrollWidth
          > document.documentElement.clientWidth + 2
        """
    )
    assert not overflow, f"horizontal overflow {label}"


@pytest.mark.parametrize("width,layout", P10_VIEWPORTS)
def test_p10_playwright_importing_layout_tier(studio_server, width: int, layout: str) -> None:
    base = studio_server["base"]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.goto(base, wait_until="networkidle")
        _wait_empty_hero(page)
        page.wait_for_function(
            "(layout) => document.documentElement.getAttribute('data-studio-layout') === layout",
            arg=layout,
            timeout=5_000,
        )
        _show_importing_demo(page)
        page.wait_for_timeout(100)

        eyebrow_display = page.locator("#studio-stage-eyebrow").evaluate(
            "el => window.getComputedStyle(el).display"
        )
        if layout == "compact":
            assert eyebrow_display != "none"
        else:
            assert eyebrow_display == "none"

        panel_width = page.locator(".studio-import__panel").evaluate("el => el.offsetWidth")
        if layout == "wide":
            assert panel_width >= 480
        else:
            assert panel_width >= width * 0.85

        _assert_no_horizontal_overflow(page, f"importing @ {width}px")

        browser.close()


@pytest.mark.parametrize("width,layout", P10_VIEWPORTS)
def test_p10_playwright_capabilities_attr(studio_server, width: int, layout: str) -> None:
    base = studio_server["base"]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.goto(base, wait_until="networkidle")
        _wait_empty_hero(page)
        cap = page.evaluate(
            "() => document.documentElement.getAttribute('data-cap-pick-folder')"
        )
        assert cap in ("on", "off")
        page.wait_for_function(
            "(layout) => document.documentElement.getAttribute('data-studio-layout') === layout",
            arg=layout,
            timeout=5_000,
        )
        browser.close()


def test_p10_playwright_wide_success_overlay(studio_server) -> None:
    base = studio_server["base"]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(base, wait_until="networkidle")
        _wait_empty_hero(page)
        page.wait_for_function(
            "() => document.documentElement.getAttribute('data-studio-layout') === 'wide'",
            timeout=5_000,
        )
        _show_success(page)
        page.wait_for_timeout(100)

        content_width = page.locator("#studio-success").evaluate("el => el.offsetWidth")
        assert content_width >= 480

        actions_dir = page.locator("#studio-success .studio-success__actions").evaluate(
            "el => window.getComputedStyle(el).flexDirection"
        )
        assert actions_dir != "column"

        _assert_no_horizontal_overflow(page, "success @ 1280px")
        browser.close()


def test_p10_playwright_compact_failure_overlay(studio_server) -> None:
    base = studio_server["base"]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 900})
        page.goto(base, wait_until="networkidle")
        _wait_empty_hero(page)
        page.wait_for_function(
            "() => document.documentElement.getAttribute('data-studio-layout') === 'compact'",
            timeout=5_000,
        )
        _show_failure(page)
        page.wait_for_timeout(100)

        hint_visible = page.locator("#studio-failure-hint").evaluate("el => !el.hidden")
        assert hint_visible

        actions_dir = page.locator("#studio-failure .studio-failure__actions").evaluate(
            "el => window.getComputedStyle(el).flexDirection"
        )
        assert actions_dir == "column"

        btn_width = page.locator("#studio-retry").evaluate(
            "(el, vw) => el.offsetWidth >= vw * 0.75",
            390,
        )
        assert btn_width

        _assert_no_horizontal_overflow(page, "failure @ 390px")
        browser.close()


def test_p10_playwright_resize_import_stage_copy(studio_server) -> None:
    """AC-P10-03 · wide → compact 时导入文案形态切换。"""
    base = studio_server["base"]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(base, wait_until="networkidle")
        _wait_empty_hero(page)
        page.wait_for_function(
            "() => document.documentElement.getAttribute('data-studio-layout') === 'wide'",
            timeout=5_000,
        )
        _show_importing_via_progress(page)
        page.wait_for_timeout(150)

        eyebrow_hidden = page.locator("#studio-stage-eyebrow").evaluate("el => el.hidden")
        assert eyebrow_hidden

        page.set_viewport_size({"width": 390, "height": 900})
        page.wait_for_function(
            "() => document.documentElement.getAttribute('data-studio-layout') === 'compact'",
            timeout=5_000,
        )
        page.wait_for_timeout(150)

        eyebrow_display = page.locator("#studio-stage-eyebrow").evaluate(
            "el => window.getComputedStyle(el).display"
        )
        assert eyebrow_display != "none"
        stage_text = page.locator("#studio-stage").inner_text()
        assert "第 1 步，共 4 步" not in stage_text
        assert "正在读取" in stage_text

        browser.close()
