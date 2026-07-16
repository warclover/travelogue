"""Flow scroll must adopt native scrollbar / keyboard jumps (AC-BR-03)."""

from __future__ import annotations

import pytest

pytest.importorskip("playwright")
from playwright.sync_api import expect, sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]

VIEWPORT = {"width": 1440, "height": 960}


def test_flow_scroll_adopts_external_scroll_jump() -> None:
    from pathlib import Path

    trip_html = Path("trips/demo-1d4f92d534/index.html").resolve()
    if not trip_html.is_file():
        pytest.skip("demo trip not rendered")

    url = trip_html.as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT)
        page.goto(url, wait_until="networkidle", timeout=120_000)

        # Lenis boot is async after networkidle — wait for class, not fixed sleep.
        expect(page.locator("html.lenis-flow")).to_be_attached(timeout=15_000)

        page.mouse.move(720, 480)
        for _ in range(8):
            page.mouse.wheel(0, 400)

        page.wait_for_function(
            "() => window.scrollY > 100",
            timeout=10_000,
        )

        max_y = page.evaluate(
            "() => Math.max(0, document.documentElement.scrollHeight - window.innerHeight)"
        )
        page.evaluate("(y) => window.scrollTo(0, y)", max_y)

        page.wait_for_function(
            """(maxY) => {
              const y = window.scrollY;
              return maxY <= 0 || y >= maxY * 0.95;
            }""",
            arg=max_y,
            timeout=15_000,
        )

        final_y = page.evaluate("() => window.scrollY")
        assert final_y >= max_y * 0.95, f"scroll snapped back: {final_y} < {max_y}"
        browser.close()
