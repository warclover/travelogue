"""AC-ARC-14a-d · preview toolbar Playwright smoke (M-C5 硬性前置)."""

from __future__ import annotations

import pytest

from tests.preview_arc14_fixtures import (
    arc14_studio_browser,
    demo_assets_available,
    wait_cover_title,
    wait_preview_dock,
)

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]

pytest.importorskip("playwright")


@pytest.fixture
def arc14_trip(tmp_path):
    if not demo_assets_available():
        pytest.skip("demo assets not present")
    return tmp_path


def test_arc14a_screenplay_next_advances_present_preview(arc14_trip) -> None:
    """AC-ARC-14a · dock 放映 → present 面 → gate → 下一屏."""
    with arc14_studio_browser(arc14_trip) as (_pw, page, base, trip_id):
        wait_preview_dock(page)
        screenplay = page.locator(".preview-toolbar__screenplay--v3")
        screenplay.wait_for(state="visible", timeout=10_000)
        with page.expect_navigation(wait_until="networkidle"):
            screenplay.click()
        assert "index-present.html" in page.url

        gate = page.locator("#screenplay-gate")
        if gate.is_visible():
            page.locator("[data-screenplay-gate-start]").click()

        page.wait_for_function(
            """() => document.body.classList.contains('screenplay-active')""",
            timeout=15_000,
        )
        before = page.locator(".screenplay-counter").inner_text().strip()
        assert before, "expected screenplay counter before next"
        page.locator('[data-screenplay-action="next"]').click()
        page.wait_for_function(
            """(prev) => {
              const el = document.querySelector('.screenplay-counter');
              const text = (el && el.textContent || '').trim();
              return text.length > 0 && text !== prev;
            }""",
            arg=before,
            timeout=10_000,
        )


def test_arc14b_inline_edit_cover_title(arc14_trip) -> None:
    """AC-ARC-14b · 点击杂志名进入 inline 输入框."""
    with arc14_studio_browser(arc14_trip) as (_pw, page, _base, _trip_id):
        wait_preview_dock(page)
        wait_cover_title(page)
        title = page.locator(".cover-opening__title")
        assert "cover-opening__title--editable" in (
            title.get_attribute("class") or ""
        )
        title.click()
        editor = page.locator(".cover-opening__title-input")
        editor.wait_for(state="visible", timeout=5_000)
        editor.fill("雨后京都")
        editor.press("Enter")
        page.wait_for_function(
            """() => {
              const el = document.querySelector('.cover-opening__title');
              return el && !el.hidden && (el.textContent || '').includes('雨后京都');
            }""",
            timeout=15_000,
        )


def test_arc14c_export_longshot_starts_from_dock(arc14_trip) -> None:
    """AC-ARC-14c · dock 导出长图触发 running 态（/__travelogue/longshot）."""
    with arc14_studio_browser(arc14_trip) as (_pw, page, _base, _trip_id):
        wait_preview_dock(page)
        export_btn = page.locator(".preview-toolbar__dock-btn--export")
        export_btn.wait_for(state="visible", timeout=10_000)

        with page.expect_request(
            lambda req: req.method == "POST" and req.url.endswith("/__travelogue/longshot"),
            timeout=20_000,
        ):
            export_btn.click()

        page.wait_for_function(
            """() => {
              const btn = document.querySelector('.preview-toolbar__dock-btn--export');
              return btn && btn.classList.contains('preview-toolbar__longshot--running');
            }""",
            timeout=15_000,
        )


def test_arc14d_share_preview_minimal_toolbar(arc14_trip) -> None:
    """AC-ARC-14d · ?share=1 极简工具栏（data-preview-share）."""
    with arc14_studio_browser(arc14_trip, query="share=1") as (_pw, page, _base, _trip_id):
        share_on = page.evaluate(
            """() => document.documentElement.getAttribute('data-preview-share')"""
        )
        assert share_on == "on"
        minimal = page.locator(".preview-toolbar--share-minimal")
        minimal.wait_for(state="visible", timeout=10_000)
        assert page.locator(".preview-toolbar--v4").count() == 0
        assert page.locator(".preview-toolbar__dock").count() == 0
        assert page.locator(".preview-toolbar__menu-btn").count() == 0
        assert page.locator(".preview-toolbar__back").count() >= 1
