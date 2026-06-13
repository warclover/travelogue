"""Preview toolbar v3 · static contract + Playwright smoke."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.web.studio_chrome import inject_studio_chrome

ROOT = Path(__file__).resolve().parents[1]
STUDIO = ROOT / "templates" / "studio"
PREVIEW_JS = STUDIO / "preview-toolbar.js"
PREVIEW_CSS = STUDIO / "preview-toolbar.css"
TASK_DOCK_JS = STUDIO / "preview-toolbar-v3-task-dock.js"
SHEET_JS = STUDIO / "preview-toolbar-v3-sheet.js"


def test_v3_modules_exist_and_are_imported() -> None:
    js = PREVIEW_JS.read_text(encoding="utf-8")
    assert TASK_DOCK_JS.is_file()
    assert SHEET_JS.is_file()
    for token in (
        'from "./preview-toolbar-v3-task-dock.js"',
        'from "./preview-toolbar-v3-sheet.js"',
        "initToolbarV3",
        "mountPreviewTaskDock",
        "mountPreviewUnifiedSheet",
    ):
        assert token in js


def test_v3_init_uses_single_bar_not_legacy_rows() -> None:
    js = PREVIEW_JS.read_text(encoding="utf-8")
    marker = 'root.className = "preview-toolbar preview-toolbar--v3"'
    assert marker in js
    start = js.index(marker)
    end = js.index("initToolbarV3(root, tripId)", start)
    v3_shell = js[start:end]
    assert "preview-toolbar__longshot-preview-row" not in v3_shell
    assert "preview-toolbar__pending-row" not in v3_shell
    assert "preview-toolbar__collapsed-strip" not in v3_shell


def test_v3_css_fixed_bar_and_task_dock() -> None:
    css = PREVIEW_CSS.read_text(encoding="utf-8")
    for token in (
        "preview-toolbar__bar--v3",
        "preview-task-dock",
        "preview-sheet",
        "preview-toolbar__longshot--v3",
        "preview-toolbar__menu-btn--pulse",
        "preview-sheet__tab--dot",
    ):
        assert token in css, f"missing v3 css: {token}"


def test_v3_task_dock_exports_g1_and_pending() -> None:
    dock = TASK_DOCK_JS.read_text(encoding="utf-8")
    for token in ("showG1", "showPending", "showExporting", "showSuccess", "onResultDismissed"):
        assert token in dock


def test_v3_sheet_has_four_tabs_and_leave_confirm() -> None:
    sheet = SHEET_JS.read_text(encoding="utf-8")
    for label in ("文字", "结构", "排版", "高级"):
        assert label in sheet
    assert "confirmLeaveCurrentTab" in sheet or "confirmLeave" in sheet
    assert "setStructureDot" in sheet


def _seed_preview_trip(trips_dir: Path, trip_id: str = "v3-smoke") -> str:
    trip_dir = trips_dir / trip_id
    trip_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "tripId": trip_id,
        "meta": {"title": "V3 冒烟"},
        "intent": {"title": "V3 冒烟"},
        "chapters": [{"id": "ch1", "title": "第一章", "items": []}],
        "assets": [],
    }
    (trip_dir / "trip.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    html = inject_studio_chrome(
        '<!DOCTYPE html><html><head><meta charset="utf-8"><title>V3</title></head>'
        '<body><main class="layout-scroll">preview</main></body></html>'
    )
    (trip_dir / "index.html").write_text(html, encoding="utf-8")
    return trip_id


@pytest.mark.e2e
def test_v3_preview_toolbar_playwright_smoke(tmp_path: Path) -> None:
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    from tests.test_studio_server import _free_port, _start_studio_server
    from travelogue.web.studio_jobs import reset_job_store

    reset_job_store()
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = _seed_preview_trip(trips_dir)
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(f"{base}/{trip_id}/index.html", wait_until="networkidle")

            toolbar = page.locator(".preview-toolbar--v3")
            toolbar.wait_for(state="visible", timeout=15_000)

            bar = page.locator(".preview-toolbar__bar--v3")
            box = bar.bounding_box()
            assert box is not None
            assert 44 <= box["height"] <= 52, f"bar height expected ~48px, got {box['height']}"

            assert page.locator(".preview-toolbar__back").inner_text().strip().endswith("返回")
            assert page.locator(".preview-toolbar__longshot--v3").inner_text().strip() == "导出长图"
            assert page.locator(".preview-toolbar__menu-btn").count() == 1

            assert page.locator(".preview-toolbar__longshot-preview-row").count() == 0
            assert page.locator(".preview-toolbar__pending-row").count() == 0
            assert page.locator(".preview-toolbar__reveal-folder").count() == 0

            page.locator(".preview-toolbar__menu-btn").click()
            sheet = page.locator(".preview-sheet")
            sheet.wait_for(state="visible", timeout=5_000)
            tabs = page.locator(".preview-sheet__tab")
            assert tabs.count() == 4
            tab_labels = [tabs.nth(i).inner_text().strip() for i in range(4)]
            assert tab_labels == ["文字", "结构", "排版", "高级"]

            page.locator('.preview-sheet__tab[data-sheet-tab="advanced"]').click()
            page.wait_for_selector('[data-reader-mode="reader"]', timeout=5_000)
            page.wait_for_selector('[data-copy-preset="full"]', timeout=5_000)
            page.wait_for_selector('[data-action="reveal-folder"]', timeout=5_000)

            page.locator(".preview-sheet__close").click()
            page.locator(".preview-sheet-root").wait_for(state="hidden", timeout=5_000)

            title_btn = page.locator(".preview-toolbar__title")
            title_btn.wait_for(state="visible", timeout=5_000)
            assert "V3" in title_btn.inner_text()

            browser.close()
    finally:
        server.shutdown()
        server.server_close()
