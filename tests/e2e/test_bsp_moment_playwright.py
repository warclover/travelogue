"""Phase 23 · inline moment EXIF DOM assertions."""

from __future__ import annotations

import pytest

from tests.unit.render.test_moment_render import _moment_trip
from travelogue.render.engine import render_html

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]

VIEWPORT = {"width": 1440, "height": 960}


def test_inline_moment_exif_dom() -> None:
    trip = _moment_trip()
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="default_hybrid",
    )
    style = (
        "<style>.moment-exif-bar{font-family:'JetBrains Mono',ui-monospace,monospace;"
        "font-size:13px;background:#0a0a0a;color:rgba(255,255,255,.88);}</style>"
    )
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT, device_scale_factor=2)
        page.set_content(style + html, wait_until="domcontentloaded")
        assert page.locator('[data-block="moment-screen"]').count() == 0
        moment = page.locator('.layout-screen[data-role="moment"]')
        assert moment.count() == 1
        exif = page.locator(".moment-exif-bar")
        assert exif.count() == 1
        assert exif.first.is_visible()
        bg = exif.first.evaluate("el => getComputedStyle(el).backgroundColor")
        assert bg in ("rgb(10, 10, 10)", "rgba(10, 10, 10, 1)")
        font = exif.first.evaluate(
            "el => getComputedStyle(el).fontFamily + '|' + getComputedStyle(el).fontSize"
        )
        assert "mono" in font.lower() or "jetbrains" in font.lower()
        chapter_exif = page.locator("section.chapter .moment-exif-bar")
        assert chapter_exif.count() == 1
        browser.close()


def test_performance_profile_omits_moment_exif() -> None:
    trip = _moment_trip()
    html = render_html(
        trip,
        export_mode="share",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="performance",
    )
    assert "moment-exif-bar" not in html
    assert 'data-role="moment"' in html


def test_performance_profile_pool_solo_without_exif() -> None:
    from tests.unit.render.test_moment_render import _pool_moment_trip

    trip = _pool_moment_trip()
    html = render_html(
        trip,
        export_mode="share",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="performance",
    )
    assert "moment-exif-bar" not in html
    assert html.count('data-role="moment"') == 1
    assert html.count('data-role="peak"') == 1


def test_pool_exif_bars_dom_count() -> None:
    from tests.unit.render.test_moment_render import _pool_moment_trip

    trip = _pool_moment_trip()
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="reader_immersive",
    )
    style = (
        "<style>.moment-exif-bar{font-family:'JetBrains Mono',ui-monospace,monospace;"
        "font-size:13px;background:#0a0a0a;color:rgba(255,255,255,.88);}</style>"
    )
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT, device_scale_factor=2)
        page.set_content(style + html, wait_until="domcontentloaded")
        assert page.locator('[data-block="moment-screen"]').count() == 0
        assert page.locator('.layout-screen[data-role="moment"]').count() == 1
        assert page.locator('.layout-screen[data-role="peak"]').count() == 1
        assert page.locator(".moment-exif-bar").count() == 2
        assert page.locator(".layout-screen__moment-label").count() == 1
        browser.close()
