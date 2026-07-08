"""Preview toolbar v3 · static contract + Playwright smoke."""



from __future__ import annotations
from tests._repo_root import repo_root

import json
from pathlib import Path

import pytest

from travelogue.web.studio_chrome import inject_studio_chrome

ROOT = repo_root(__file__)
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
        'from "./preview-toolbar/dock.js"',
        'from "./preview-toolbar/longshot.js"',
        "initToolbarV3",
        "mountPreviewTaskDock",
        "mountPreviewUnifiedSheet",
        "registerLongshotBridge",
        "startLongshot",
    ):
        assert token in js


def test_m5_longshot_module_exports() -> None:
    longshot = (STUDIO / "preview-toolbar" / "longshot.js").read_text(encoding="utf-8")
    for token in (
        "export function startLongshot",
        "export function pollJob",
        "export function registerLongshotBridge",
        "export function cancelPreviewLongshotExport",
    ):
        assert token in longshot, f"missing longshot export: {token}"
    assert "export function (job)" not in longshot


def test_m5_shell_module_exports() -> None:
    js = PREVIEW_JS.read_text(encoding="utf-8")
    shell = (STUDIO / "preview-toolbar" / "shell.js").read_text(encoding="utf-8")
    assert 'from "./preview-toolbar/shell.js"' in js
    for token in (
        "export function showToolbarToast",
        "export function syncToolbarHeight",
        "export function tripIdFromPath",
        "export function reloadPreviewAfterLayout",
    ):
        assert token in shell, f"missing shell export: {token}"


def test_m5_drawers_module_exports() -> None:
    js = PREVIEW_JS.read_text(encoding="utf-8")
    drawers = (STUDIO / "preview-toolbar" / "drawers.js").read_text(encoding="utf-8")
    assert 'from "./preview-toolbar/drawers.js"' in js
    for token in (
        "export function initPreviewDrawers",
        "export function trapDrawerFocus",
        "export function registerDrawersBridge",
        "preview-drawer__copy-intent",
    ):
        assert token in drawers, f"missing drawers export: {token}"


def test_m5_core_module_exports() -> None:
    js = PREVIEW_JS.read_text(encoding="utf-8")
    core = (STUDIO / "preview-toolbar" / "core.js").read_text(encoding="utf-8")
    jsconfig = STUDIO / "preview-toolbar" / "jsconfig.json"
    assert jsconfig.is_file()
    assert 'from "./preview-toolbar/core.js"' in js
    for token in (
        "export function setLayoutPending",
        "export function applyLayoutRerender",
        "export function getLayoutPending",
        "export function refreshTaskDockState",
    ):
        assert token in core, f"missing core export: {token}"


def test_m5_bootstrap_module_exports() -> None:
    js = PREVIEW_JS.read_text(encoding="utf-8")
    bootstrap = (STUDIO / "preview-toolbar" / "bootstrap.js").read_text(encoding="utf-8")
    assert 'from "./preview-toolbar/bootstrap.js"' in js
    assert "registerBootstrapBridge" in js
    assert "bootstrapPreviewToolbarWhenReady" in js
    for token in (
        "export function initPreviewToolbar",
        "export function bootstrapPreviewToolbarWhenReady",
        "preview-toolbar--v4",
        "preview-toolbar__dock",
    ):
        assert token in bootstrap, f"missing bootstrap export: {token}"


def test_v4_init_uses_icon_dock_not_legacy_rows() -> None:
    js = PREVIEW_JS.read_text(encoding="utf-8")
    bootstrap = (STUDIO / "preview-toolbar" / "bootstrap.js").read_text(encoding="utf-8")
    marker = 'root.className = "preview-toolbar preview-toolbar--v4"'
    assert marker in bootstrap
    assert "initToolbarV3(root, tripId)" in js
    start = bootstrap.index(marker)
    end = bootstrap.index("_initToolbarV3(root, tripId)", start)
    v4_shell = bootstrap[start:end]
    assert "preview-toolbar__dock" in v4_shell
    assert "preview-toolbar__longshot-preview-row" not in v4_shell
    assert "preview-toolbar__pending-row" not in v4_shell
    assert "preview-toolbar__collapsed-strip" not in v4_shell
    assert "preview-toolbar__title-wrap" not in v4_shell


def test_v4_dock_tooltips_and_scroll_fade() -> None:
    js = PREVIEW_JS.read_text(encoding="utf-8")
    inline = (STUDIO / "preview-toolbar" / "inline-edit.js").read_text(encoding="utf-8")
    dock = (STUDIO / "preview-toolbar" / "dock.js").read_text(encoding="utf-8")
    for token in (
        "initDockTooltips",
        "initDockScrollFade",
        "ensureDockTooltip",
    ):
        assert token in js or token in dock, f"missing v4 dock ux: {token}"
    for token in ("initCoverTitleEdit", "cover-opening__title--editable"):
        assert token in js or token in inline, f"missing v4 inline edit: {token}"
    css = PREVIEW_CSS.read_text(encoding="utf-8")
    for token in (
        "preview-toolbar__dock-tip",
        "preview-toolbar__dock--dim",
        "transition-delay: 0.3s",
    ):
        assert token in css, f"missing v4 dock css: {token}"


def test_v4_toolbar_mounts_screenplay_control() -> None:
    js = PREVIEW_JS.read_text(encoding="utf-8")
    dock = (STUDIO / "preview-toolbar" / "dock.js").read_text(encoding="utf-8")
    assert "insertScreenplayControl(actions, menuWrap" in js
    assert "dock: true" in js
    assert "preview-toolbar__screenplay--v3" in js or "preview-toolbar__screenplay--v3" in dock
    css = PREVIEW_CSS.read_text(encoding="utf-8")
    assert "preview-toolbar__dock" in css
    assert "preview-toolbar--v4" in css


def test_v4_css_icon_dock_and_task_dock() -> None:
    css = PREVIEW_CSS.read_text(encoding="utf-8")
    for token in (
        "preview-toolbar__dock",
        "preview-toolbar--v4",
        "--preview-toolbar-h: 0px",
        "preview-task-dock",
        "preview-sheet",
        "preview-sheet__content",
        "--preview-sheet-side-w",
        "preview-toolbar__longshot--v3",
        "preview-toolbar__menu-btn--pulse",
        "preview-sheet__tab--dot",
        "preview-sheet__tabs",
        "flex-shrink: 0",
        "translate3d",
        "--preview-sheet-ease-enter",
        "preview-sheet-root--open",
        "preview-sheet-duration-enter",
    ):
        assert token in css, f"missing v3 css: {token}"
    tabs_block = css.split(".preview-sheet__tabs {", 1)[1].split("}", 1)[0]
    assert "flex-shrink: 0" in tabs_block
    sheet_template = css.split(".preview-toolbar__template--sheet {", 1)[1].split("}", 1)[0]
    assert "#1a2f28" in sheet_template


def test_v3_sheet_has_content_wrapper() -> None:
    sheet = SHEET_JS.read_text(encoding="utf-8")
    assert "preview-sheet__content" in sheet
    assert "beginSheetEnter" in sheet
    assert "beginSheetExit" in sheet


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
        '<!DOCTYPE html><html data-screenplay="on"><head><meta charset="utf-8"><title>V3</title></head>'
        '<body><main class="layout-scroll">preview</main>'
        '<button id="screenplay-start" type="button" hidden></button></body></html>'
    )
    (trip_dir / "index.html").write_text(html, encoding="utf-8")
    return trip_id


@pytest.mark.e2e
def test_v4_preview_toolbar_playwright_smoke(tmp_path: Path) -> None:
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    from tests.integration.studio.test_studio_server import _free_port, _start_studio_server
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

            dock = page.locator(".preview-toolbar__dock")
            dock.wait_for(state="visible", timeout=15_000)

            box = dock.bounding_box()
            assert box is not None
            assert box["height"] <= 52, f"dock height expected compact, got {box['height']}"
            assert box["width"] <= 240, f"dock width expected compact, got {box['width']}"

            assert page.locator(".preview-toolbar__dock-btn--back").count() == 1
            assert page.locator(".preview-toolbar__dock-btn--export").count() == 1
            assert page.locator(".preview-toolbar__screenplay--v3").count() == 1
            assert page.locator(".preview-toolbar__menu-btn").count() == 1
            assert page.locator(".preview-toolbar__bar--v3").count() == 0
            assert page.locator(".preview-toolbar__title").count() == 0

            assert page.locator(".preview-toolbar__longshot-preview-row").count() == 0
            assert page.locator(".preview-toolbar__pending-row").count() == 0
            assert page.locator(".preview-toolbar__reveal-folder").count() == 0

            page.locator(".preview-toolbar__menu-btn").click()
            page.wait_for_timeout(580)
            expect_open = page.evaluate(
                '() => document.querySelector(".preview-sheet-root").classList.contains("preview-sheet-root--open")'
            )
            assert expect_open is True

            sheet = page.locator(".preview-sheet")
            sheet.wait_for(state="visible", timeout=5_000)

            side_layout = page.evaluate(
                """() => {
                const sheet = document.querySelector('.preview-sheet');
                const rect = sheet.getBoundingClientRect();
                const toolbar = document.querySelector('.preview-toolbar--v4');
                const toolbarH = toolbar
                  ? parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--preview-toolbar-h')) || 0
                  : 0;
                return {
                    top: rect.top,
                    x: rect.x,
                    width: rect.width,
                    height: rect.height,
                    viewportW: window.innerWidth,
                    viewportH: window.innerHeight,
                    toolbarH,
                    bodyMarginRight: getComputedStyle(document.body).marginRight,
                    toolbarRight: getComputedStyle(document.querySelector('.preview-toolbar')).right,
                    borderRadius: getComputedStyle(sheet).borderRadius,
                };
            }"""
            )
            assert side_layout["width"] >= 360, side_layout
            assert side_layout["x"] >= side_layout["viewportW"] - side_layout["width"] - 16, side_layout
            assert side_layout["top"] >= side_layout["toolbarH"] + 8, side_layout
            assert side_layout["height"] <= side_layout["viewportH"] - side_layout["toolbarH"] - 20, side_layout
            assert float(side_layout["bodyMarginRight"].replace("px", "") or 0) < 20, side_layout
            assert "16" in side_layout["borderRadius"], side_layout

            tabs = page.locator(".preview-sheet__tab")
            assert tabs.count() == 4
            tab_labels = [tabs.nth(i).inner_text().strip() for i in range(4)]
            assert tab_labels == ["文字", "结构", "排版", "高级"]

            page.locator('.preview-sheet__tab[data-sheet-tab="advanced"]').click()
            page.wait_for_selector('[data-reader-mode="reader"]', timeout=5_000)
            page.wait_for_selector('[data-copy-preset="full"]', timeout=5_000)
            page.wait_for_selector('[data-action="reveal-folder"]', timeout=5_000)

            page.locator('.preview-sheet__tab[data-sheet-tab="structure"]').click()
            page.wait_for_selector(".preview-drawer__g1", timeout=5_000)
            tab_metrics = page.evaluate(
                """() => {
                const tabs = document.querySelector('.preview-sheet__tabs');
                const tab = document.querySelector('.preview-sheet__tab.is-active');
                return {
                    tabsH: tabs ? tabs.offsetHeight : 0,
                    tabBtnH: tab ? tab.offsetHeight : 0,
                };
            }"""
            )
            assert tab_metrics["tabsH"] >= 40, tab_metrics
            assert tab_metrics["tabBtnH"] >= 28, tab_metrics

            page.locator(".preview-sheet__close").click()
            page.locator(".preview-sheet-root").wait_for(state="hidden", timeout=5_000)

            focused_menu = page.evaluate(
                """() => {
                const btn = document.querySelector('.preview-toolbar__menu-btn');
                return btn && document.activeElement === btn;
            }"""
            )
            assert focused_menu is True

            browser.close()
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
def test_v3_mobile_keeps_bottom_sheet(tmp_path: Path) -> None:
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    from tests.integration.studio.test_studio_server import _free_port, _start_studio_server
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
            page = browser.new_page(viewport={"width": 390, "height": 700})
            page.goto(f"{base}/{trip_id}/index.html", wait_until="networkidle")
            page.locator(".preview-toolbar__menu-btn").click()
            page.locator(".preview-sheet").wait_for(state="visible", timeout=5_000)
            layout = page.evaluate(
                """() => {
                const sheet = document.querySelector('.preview-sheet');
                const rect = sheet.getBoundingClientRect();
                return {
                    bottom: rect.bottom,
                    viewportH: window.innerHeight,
                    bodyMarginRight: getComputedStyle(document.body).marginRight,
                };
            }"""
            )
            assert layout["bottom"] >= layout["viewportH"] - 4, layout
            margin = float(layout["bodyMarginRight"].replace("px", "") or 0)
            assert margin < 40, layout
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
