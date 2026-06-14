"""Phase 23 · moment-screen DOM assertions (AC-P23-01–07)."""

from __future__ import annotations

import pytest

from travelogue.render.engine import render_html
from tests.test_moment_render import _moment_trip

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]

VIEWPORT = {"width": 1440, "height": 960}


def test_moment_screen_dom_ac_p23() -> None:
    trip = _moment_trip()
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="default_hybrid",
    )
    style = (
        "<style>.moment-exif-line{font-family:'JetBrains Mono',ui-monospace,monospace;"
        "font-size:13px;}</style>"
    )
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT, device_scale_factor=2)
        page.set_content(style + html, wait_until="domcontentloaded")
        moments = page.locator('[data-block="moment-screen"]')
        assert moments.count() == 1
        exif = page.locator(".moment-exif-line")
        assert exif.count() == 1
        assert exif.first.is_visible()
        font = exif.first.evaluate(
            "el => getComputedStyle(el).fontFamily + '|' + getComputedStyle(el).fontSize"
        )
        assert "mono" in font.lower() or "jetbrains" in font.lower()
        closing = page.locator('[data-block="cover-closing"]')
        assert closing.count() == 1
        moment_box = moments.first.bounding_box()
        closing_box = closing.first.bounding_box()
        assert moment_box and closing_box
        assert moment_box["y"] < closing_box["y"]
        chapter_exif = page.locator("section.chapter .moment-exif-line")
        assert chapter_exif.count() == 0
        browser.close()


def test_performance_profile_omits_moment_screen() -> None:
    trip = _moment_trip()
    html = render_html(
        trip,
        export_mode="share",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="performance",
    )
    assert 'data-block="moment-screen"' not in html
