"""Phase 13 G8 · Studio 浏览器走查（Playwright）。"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.g8_playwright_suite import (
    check_g8_08_hint_switch,
    check_g8_09_template_feedback,
    check_g8_10_lan_permission_ui,
    check_g8_11_preview_toolbar,
    check_g8_11_shelf_template_label,
    collapse_g8_items,
    run_g8_playwright_suite,
    seed_g8_preview_trip,
)
from tests.integration.studio.test_studio_server import _free_port, _start_studio_server

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]


@pytest.fixture
def studio_server(tmp_path: Path):
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    preview_id = seed_g8_preview_trip(trips_dir)
    port = _free_port()
    server = _start_studio_server(trips_dir, port, studio_allow_lan=False)
    base = f"http://127.0.0.1:{port}"
    try:
        yield {"base": base, "preview_trip_id": preview_id}
    finally:
        server.shutdown()
        server.server_close()


def test_g8_playwright_suite_collapsed(studio_server) -> None:
    items = run_g8_playwright_suite(
        base=studio_server["base"],
        base_lan=studio_server["base"],
        preview_trip_id=studio_server["preview_trip_id"],
    )
    collapsed = collapse_g8_items(items)
    for row in collapsed:
        assert row.get("pass"), row


def test_g8_08_template_hint_manual(studio_server) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            row = check_g8_08_hint_switch(page, studio_server["base"])
            assert row["pass"]
        finally:
            browser.close()


def test_g8_09_template_feedback_message(studio_server) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            row = check_g8_09_template_feedback(page, studio_server["base"])
            assert row["pass"]
        finally:
            browser.close()


def test_g8_10_lan_permission_denied(studio_server) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            row = check_g8_10_lan_permission_ui(page, studio_server["base"])
            assert row["pass"]
        finally:
            browser.close()


def test_g8_11_shelf_and_preview(studio_server) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            shelf = check_g8_11_shelf_template_label(page, studio_server["base"])
            preview = check_g8_11_preview_toolbar(
                page, studio_server["base"], studio_server["preview_trip_id"]
            )
            assert shelf["pass"] and preview["pass"]
        finally:
            browser.close()
