"""P9-P0-05 · Playwright smoke: keyboard path, sheet a11y, responsive overflow."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.web.studio_jobs import reset_job_store
from tests.test_studio_p9_qa_matrix import QA_BREAKPOINTS_PX
from tests.test_studio_server import _free_port, _start_studio_server

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.playwright_serial,
    pytest.mark.skip(
        reason="M21-e2 retired full v3 homepage (studio.html); QA covered by v2 AC suite",
    ),
]


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


def _seed_trip(trips_dir: Path, trip_id: str = "qa-return") -> None:
    trip_dir = trips_dir / trip_id
    trip_dir.mkdir(parents=True)
    (trip_dir / "trip.json").write_text(
        json.dumps(
            {
                "meta": {"title": "QA 回访"},
                "updatedAt": "2026-05-30T12:00:00+00:00",
                "assets": [{"type": "image", "id": "a1"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


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


def _wait_returning_hero(page) -> None:
    page.wait_for_function(
        """
        () => {
          const ret = document.getElementById('studio-hero-returning');
          const loading = document.getElementById('studio-hero-loading');
          return ret && !ret.hidden && loading && loading.hidden;
        }
        """,
        timeout=20_000,
    )


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


def test_p9_qa_playwright_empty_keyboard_and_sheet(studio_server) -> None:
    base = studio_server["base"]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(base, wait_until="networkidle")
        _wait_empty_hero(page)

        skip = page.locator(".studio-skip-link")
        skip.focus()
        assert skip.evaluate("el => el === document.activeElement")
        href = skip.get_attribute("href")
        assert href == "#studio-open-sheet"

        page.locator("#studio-open-sheet").click()
        page.wait_for_selector("#studio-import-sheet", state="visible")
        assert page.locator("#studio-import-sheet").get_attribute("role") == "dialog"
        assert page.locator("#studio-hero-empty").evaluate("el => el.hasAttribute('inert')")
        assert page.locator("#studio-import-sheet").evaluate(
            "el => !el.closest('[inert]')"
        )

        page.keyboard.press("Escape")
        page.wait_for_function(
            "() => document.getElementById('studio-sheet-root').hidden",
            timeout=5_000,
        )
        assert page.locator("#studio-hero-empty").evaluate("el => !el.hasAttribute('inert')")

        browser.close()


def test_p9_qa_playwright_returning_skip_link_target(studio_server) -> None:
    _seed_trip(studio_server["trips_dir"])
    base = studio_server["base"]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(base, wait_until="networkidle")
        _wait_returning_hero(page)

        href = page.locator(".studio-skip-link").get_attribute("href")
        assert href == "#studio-open-sheet-returning"
        assert page.locator("#studio-open-sheet-returning").is_visible()

        browser.close()


@pytest.mark.parametrize("width", QA_BREAKPOINTS_PX)
def test_p9_qa_playwright_no_horizontal_overflow_empty(studio_server, width: int) -> None:
    base = studio_server["base"]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.goto(base, wait_until="networkidle")
        _wait_empty_hero(page)
        page.wait_for_timeout(150)

        overflow = page.evaluate(
            """
            () => document.documentElement.scrollWidth
              > document.documentElement.clientWidth + 2
            """
        )
        assert not overflow, f"horizontal overflow at {width}px"
        assert page.locator("#studio-open-sheet").is_visible()
        assert page.locator('[data-entry-tier="primary"]').first.is_visible()

        browser.close()


@pytest.mark.parametrize("width", QA_BREAKPOINTS_PX)
def test_p9_qa_playwright_no_horizontal_overflow_returning(studio_server, width: int) -> None:
    _seed_trip(studio_server["trips_dir"])
    base = studio_server["base"]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.goto(base, wait_until="networkidle")
        _wait_returning_hero(page)
        page.wait_for_timeout(150)

        overflow = page.evaluate(
            """
            () => document.documentElement.scrollWidth
              > document.documentElement.clientWidth + 2
            """
        )
        assert not overflow, f"horizontal overflow at {width}px returning @ {width}"
        assert page.locator("#studio-open-sheet-returning").is_visible()

        browser.close()


def test_p9_qa_playwright_sheet_pick_button_clickable(studio_server, monkeypatch) -> None:
    """Regression: sheet must stay outside hero inert subtree (P8 a11y fix)."""
    import travelogue.desktop.folder_picker_service as picker_service
    from travelogue.desktop.folder_picker_service import FolderPickResult

    album = studio_server["trips_dir"].parent / "pick-album"
    album.mkdir(exist_ok=True)
    monkeypatch.setattr(
        picker_service,
        "request_folder",
        lambda **_: FolderPickResult(path=album),
    )
    base = studio_server["base"]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(base, wait_until="networkidle")
        _wait_empty_hero(page)
        page.locator("#studio-open-sheet").click()
        page.wait_for_selector("#studio-import-sheet", state="visible")
        with page.expect_response(lambda r: "/pick-folder" in r.url) as resp_info:
            page.locator("#studio-sheet-pick").click()
        assert resp_info.value.status == 200
        page.wait_for_selector("#studio-sheet-picked", state="visible")
        assert "pick-album" in (page.locator("#studio-sheet-picked").text_content() or "")
        browser.close()
