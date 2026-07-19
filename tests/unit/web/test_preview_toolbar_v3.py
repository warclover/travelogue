"""Preview toolbar v3 · static contract + Playwright smoke."""



from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests._repo_root import repo_root
from tests.unit.web._ash_source_contracts import (
    assert_contains_all,
    assert_js_exports,
)
from tests.unit.web._preview_toolbar_css import read_preview_toolbar_css_bundle
from travelogue.web.studio_chrome import inject_studio_chrome

ROOT = repo_root(__file__)
STUDIO = ROOT / "templates" / "studio"
PREVIEW_JS = STUDIO / "preview-toolbar.js"
PREVIEW_CSS = STUDIO / "preview-toolbar.css"
PREVIEW_CSS_BUNDLE = read_preview_toolbar_css_bundle(STUDIO)
TASK_DOCK_JS = STUDIO / "preview-toolbar-v3-task-dock.js"
SHEET_JS = STUDIO / "preview-toolbar-v3-sheet.js"


def test_preview_toolbar_entry_import_contract() -> None:
    """ASH-CONTRACT: entry/init-v3 import graph (path literals consolidated)."""
    js = PREVIEW_JS.read_text(encoding="utf-8")
    init_v3 = (STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    assert TASK_DOCK_JS.is_file()
    assert SHEET_JS.is_file()
    # Critical entry + dock/sheet wiring (AC-ASH-M3-02 ≥30% cut vs scattered paths).
    assert_contains_all(
        js,
        (
            'from "./preview-toolbar/init-v3.js"',
            'from "./preview-toolbar/bootstrap.js"',
        ),
        where="preview-toolbar.js",
    )
    assert_contains_all(
        init_v3,
        (
            'from "../preview-toolbar-v3-task-dock.js"',
            'from "../preview-toolbar-v3-sheet.js"',
            'from "./shell.js"',
            'from "./core.js"',
            'from "./features.js"',
        ),
        where="init-v3.js",
    )


def test_v3_modules_exist_and_are_imported() -> None:
    js = PREVIEW_JS.read_text(encoding="utf-8")
    init_v3 = (STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    assert TASK_DOCK_JS.is_file()
    assert SHEET_JS.is_file()
    assert_contains_all(
        init_v3,
        (
            "export function initToolbarV3",
            "mountPreviewTaskDock",
            "mountPreviewUnifiedSheet",
            "registerLongshotBridge",
            "startLongshot",
        ),
        where="init-v3.js",
    )
    assert "initToolbarV3" in js
    assert "registerBootstrapBridge" in js


def test_m5_longshot_module_exports() -> None:
    longshot = (STUDIO / "preview-toolbar" / "longshot.js").read_text(encoding="utf-8")
    assert_js_exports(
        longshot,
        (
            "startLongshot",
            "pollJob",
            "registerLongshotBridge",
            "cancelPreviewLongshotExport",
        ),
        module="longshot.js",
    )
    assert "export function (job)" not in longshot


def test_m5_shell_module_exports() -> None:
    shell = (STUDIO / "preview-toolbar" / "shell.js").read_text(encoding="utf-8")
    assert_js_exports(
        shell,
        (
            "showToolbarToast",
            "syncToolbarHeight",
            "tripIdFromPath",
            "reloadPreviewAfterLayout",
        ),
        module="shell.js",
    )


def test_m5_drawers_module_exports() -> None:
    drawers = (STUDIO / "preview-toolbar" / "drawers.js").read_text(encoding="utf-8")
    assert_js_exports(
        drawers,
        (
            "initPreviewDrawers",
            "trapDrawerFocus",
            "registerDrawersBridge",
        ),
        module="drawers.js",
    )
    assert "preview-drawer__copy-intent" in drawers


def test_m5_core_module_exports() -> None:
    core = (STUDIO / "preview-toolbar" / "core.js").read_text(encoding="utf-8")
    jsconfig = STUDIO / "preview-toolbar" / "jsconfig.json"
    assert jsconfig.is_file()
    assert_js_exports(
        core,
        (
            "setLayoutPending",
            "applyLayoutRerender",
            "getLayoutPending",
            "refreshTaskDockState",
        ),
        module="core.js",
    )


def test_m5_bootstrap_module_exports() -> None:
    js = PREVIEW_JS.read_text(encoding="utf-8")
    bootstrap = (STUDIO / "preview-toolbar" / "bootstrap.js").read_text(encoding="utf-8")
    assert "registerBootstrapBridge" in js
    assert "bootstrapPreviewToolbarWhenReady" in js
    assert_js_exports(
        bootstrap,
        (
            "initPreviewToolbar",
            "bootstrapPreviewToolbarWhenReady",
        ),
        module="bootstrap.js",
    )
    assert_contains_all(
        bootstrap,
        ("preview-toolbar--v4", "preview-toolbar__dock"),
        where="bootstrap.js",
    )


def test_m5_features_module_exports() -> None:
    features = (STUDIO / "preview-toolbar" / "features.js").read_text(encoding="utf-8")
    assert_js_exports(
        features,
        (
            "mountTemplateControls",
            "initFeaturedStars",
            "applyReaderSurfaceMode",
            "mountCoverStyleControls",
        ),
        module="features.js",
    )


def test_m5_init_v3_module_exports() -> None:
    init_v3 = (STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    assert_js_exports(init_v3, ("initToolbarV3",), module="init-v3.js")
    assert_contains_all(
        init_v3,
        (
            "mountPreviewTaskDock",
            "mountPreviewUnifiedSheet",
            "insertScreenplayControl(actions, menuWrap",
            "registerLongshotBridge",
            "registerDrawersBridge",
            "registerInlineEditBridge",
        ),
        where="init-v3.js",
    )


def test_m5_css_split_modules() -> None:
    entry = PREVIEW_CSS.read_text(encoding="utf-8")
    assert '@import url("preview-toolbar/tokens.css")' in entry
    assert '@import url("preview-toolbar/sheet.css")' in entry
    for name in (
        "tokens.css",
        "shell.css",
        "longshot.css",
        "dock.css",
        "task-dock.css",
        "sheet.css",
    ):
        assert (STUDIO / "preview-toolbar" / name).is_file(), f"missing css partial: {name}"
    assert "--preview-toolbar-h:" in PREVIEW_CSS_BUNDLE
    assert ".preview-toolbar__dock" in PREVIEW_CSS_BUNDLE


def test_m5_css_import_mime_and_static_path() -> None:
    import mimetypes

    from travelogue.paths import STUDIO_TEMPLATE_DIR

    assert mimetypes.guess_type("preview-toolbar.css")[0] == "text/css"
    partial = STUDIO_TEMPLATE_DIR / "preview-toolbar" / "dock.css"
    assert partial.is_file()
    assert mimetypes.guess_type(partial.name)[0] == "text/css"


def test_m5_tsc_gate_files() -> None:
    jsconfig = STUDIO / "preview-toolbar" / "jsconfig.json"
    global_dts = STUDIO / "preview-toolbar" / "global.d.ts"
    pkg = ROOT / "package.json"
    assert jsconfig.is_file()
    assert global_dts.is_file()
    assert pkg.is_file()
    pkg_json = pkg.read_text(encoding="utf-8")
    assert "tsc:preview-toolbar" in pkg_json
    assert '"typescript"' in pkg_json


def test_v4_init_uses_icon_dock_not_legacy_rows() -> None:
    init_v3 = (STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    bootstrap = (STUDIO / "preview-toolbar" / "bootstrap.js").read_text(encoding="utf-8")
    marker = 'root.className = "preview-toolbar preview-toolbar--v4"'
    assert marker in bootstrap
    assert "export function initToolbarV3" in init_v3
    start = bootstrap.index(marker)
    end = bootstrap.index("_initToolbarV3(root, tripId)", start)
    v4_shell = bootstrap[start:end]
    assert "preview-toolbar__dock" in v4_shell
    assert "preview-toolbar__longshot-preview-row" not in v4_shell
    assert "preview-toolbar__pending-row" not in v4_shell
    assert "preview-toolbar__collapsed-strip" not in v4_shell
    assert "preview-toolbar__title-wrap" not in v4_shell


def test_v4_dock_tooltips_and_scroll_fade() -> None:
    init_v3 = (STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    inline = (STUDIO / "preview-toolbar" / "inline-edit.js").read_text(encoding="utf-8")
    dock = (STUDIO / "preview-toolbar" / "dock.js").read_text(encoding="utf-8")
    for token in (
        "initDockTooltips",
        "initDockScrollFade",
        "ensureDockTooltip",
    ):
        assert token in init_v3 or token in dock, f"missing v4 dock ux: {token}"
    for token in ("initCoverTitleEdit", "cover-opening__title--editable"):
        assert token in init_v3 or token in inline, f"missing v4 inline edit: {token}"
    css = PREVIEW_CSS_BUNDLE
    for token in (
        "preview-toolbar__dock-tip",
        "preview-toolbar__dock--dim",
        "transition-delay: 0.3s",
    ):
        assert token in css, f"missing v4 dock css: {token}"


def test_v4_toolbar_mounts_screenplay_control() -> None:
    init_v3 = (STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    dock = (STUDIO / "preview-toolbar" / "dock.js").read_text(encoding="utf-8")
    assert "insertScreenplayControl(actions, menuWrap" in init_v3
    assert "dock: true" in init_v3
    assert "preview-toolbar__screenplay--v3" in init_v3 or "preview-toolbar__screenplay--v3" in dock
    css = PREVIEW_CSS_BUNDLE
    assert "preview-toolbar__dock" in css
    assert "preview-toolbar--v4" in css


def test_v4_css_icon_dock_and_task_dock() -> None:
    css = PREVIEW_CSS_BUNDLE
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
    for token in (
        "showG1",
        "showPending",
        "showStale",
        "showExporting",
        "showSuccess",
        "onResultDismissed",
    ):
        assert token in dock


def test_v3_sheet_has_three_zone_tabs_and_leave_confirm() -> None:
    sheet = SHEET_JS.read_text(encoding="utf-8")
    for label in ("这页", "封面", "这本"):
        assert label in sheet
    assert 'label: "导出"' not in sheet
    assert "导出与更多" not in sheet
    assert "confirmLeaveCurrentTab" in sheet or "confirmLeave" in sheet
    assert "setStructureDot" in sheet
    assert "resolveDefaultOpenTab" in sheet
    assert "封底在「封面」里换" in sheet


def test_ux_be_book_tab_zones_focus_and_deeplink() -> None:
    """UX-BE · 三区（这页|封面|这本）+ 封面区内分段 + 空态深链（源码门禁）。"""
    sheet = SHEET_JS.read_text(encoding="utf-8")
    bookends = (STUDIO / "preview-toolbar" / "bookends.js").read_text(encoding="utf-8")
    css = (STUDIO / "preview-toolbar" / "sheet.css").read_text(encoding="utf-8")
    panel = (STUDIO / "js" / "longshot-export-panel.js").read_text(encoding="utf-8")

    assert "改名字与一句话" in sheet
    assert 'id: "cover"' in sheet
    assert 'data-book-zone="story"' in sheet
    assert 'data-book-zone="advanced"' in sheet
    assert "renderCoverPanel" in sheet
    assert "data-cover-side" in sheet
    assert "整本信息" in sheet
    assert "进阶" in sheet
    assert "去换封底" in sheet or "去换封面" in sheet
    assert "goto-bookends" in sheet
    assert "goto-body" in sheet
    assert "去游记正文" in sheet
    assert "preview-toolbar__collage-select" in sheet
    assert "preview-toolbar__collage-media" not in sheet
    assert "bookendsFocus" in sheet
    assert "applyBookendsFocusUi" in sheet
    assert "scrollPreviewToBookend" in sheet
    assert "手选 · 可恢复自动" in bookends
    assert "已按你的选择固定" not in bookends
    assert "data-bookends-scroll-opening" in bookends
    assert "data-bookends-scroll-closing" in bookends
    assert "preview-sheet__zone" in css
    assert 'data-cover-side="opening"' in css
    # 导出决策迁入 ▾：文案范围必显
    assert 'data-field="copy"' in panel
    assert 'data-copy-preset="photos"' in panel
    assert "长图要不要字" in panel
    assert "更多输出" in panel
    assert 'data-action="export-zip"' in panel
    assert 'data-action="reveal-folder"' in panel
    assert 'title="2×"' in panel and ">标准<" in panel
    assert 'title="3×"' in panel and ">更清晰<" in panel
    assert "标准 2×" not in panel
    assert "preview-sheet__template-slot" in sheet
    assert "preview-sheet__embed--cohort" in sheet
    assert "preview-sheet__embed--structure" in sheet
    assert "bookAdvancedToolsHtml" in sheet
    assert "放映精选" in sheet
    assert "生成杂志感文案" in sheet


def test_studio_aesthetic_debug_gated_from_default_ui() -> None:
    """Aesthetic score dump is dogfood-only (?debug=aesthetic), not default Studio UI."""
    drawers = (STUDIO / "preview-toolbar" / "drawers.js").read_text(encoding="utf-8")
    features = (STUDIO / "preview-toolbar" / "features.js").read_text(encoding="utf-8")
    assert "export function isAestheticDebugEnabled" in drawers
    assert 'get("debug") === "aesthetic"' in drawers
    assert "travelogue.aestheticDebug" in drawers
    # loadAestheticExplain itself is gated
    load_fn = drawers.split("export function loadAestheticExplain", 1)[1].split(
        "export function", 1
    )[0]
    assert "isAestheticDebugEnabled()" in load_fn
    # Structure embed only loads aesthetic when debug is on
    assert "loadAestheticExplain(tripId, aestheticEl)" in drawers
    struct_open = drawers.split(
        'targetBody.querySelector(".preview-drawer__explain")', 1
    )[1].split("var applyBtn", 1)[0]
    assert "isAestheticDebugEnabled()" in struct_open
    assert "loadAestheticExplain(tripId, aestheticEl)" in struct_open
    # Hover title scores also gated
    titles_fn = features.split("function initDisplayedAestheticTitles", 1)[1].split(
        "export function", 1
    )[0]
    assert "isAestheticDebugEnabled()" in titles_fn
    assert "· overall " in drawers  # still exists for debug panel copy
    # Default advanced lead must not promise score boards
    sheet = SHEET_JS.read_text(encoding="utf-8")
    assert "照片审美分项" not in sheet
    assert "很少需要" in sheet


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
@pytest.mark.playwright_serial
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
            # Labeled dock (返回/播放/精修 + 长图 split) is wider than icon-only era.
            assert box["width"] <= 520, f"dock width expected compact-labeled, got {box['width']}"

            assert page.locator(".preview-toolbar__dock-btn--back").count() == 1
            assert page.locator(".preview-toolbar__dock-btn--export").count() == 1
            assert page.locator(".preview-toolbar__longshot-caret").count() == 1
            assert page.locator(".preview-toolbar__longshot-split").count() == 1
            assert page.locator(".preview-toolbar__screenplay--v3").count() == 1
            assert page.locator(".preview-toolbar__menu-btn").count() == 1
            assert page.locator(".preview-toolbar__bar--v3").count() == 0
            assert page.locator(".preview-toolbar__title").count() == 0

            page.locator(".preview-toolbar__longshot-caret").click()
            page.wait_for_timeout(200)
            pop = page.locator(".preview-toolbar__export-popover")
            pop.wait_for(state="visible", timeout=5_000)
            assert page.locator("[data-studio-longshot-platform]").count() >= 2
            page.locator('.preview-toolbar__export-popover [data-action="cancel"]').click()
            page.wait_for_timeout(150)
            assert pop.is_hidden() or not pop.is_visible()

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
            assert tabs.count() == 3
            tab_labels = [tabs.nth(i).inner_text().strip() for i in range(3)]
            assert tab_labels == ["这页", "封面", "这本"]

            page.locator('.preview-sheet__tab[data-sheet-tab="cover"]').click()
            page.wait_for_selector("button[data-cover-side]", timeout=5_000)
            page.wait_for_selector(".preview-sheet__bookends-slot", timeout=5_000)

            page.locator('.preview-sheet__tab[data-sheet-tab="book"]').click()
            page.wait_for_timeout(300)
            page.locator('[data-book-zone="advanced"] > summary').click()
            page.wait_for_selector(
                '.preview-sheet [data-reader-mode="reader"]', timeout=5_000
            )
            page.wait_for_selector(
                '.preview-sheet [data-action="reveal-folder"]', timeout=5_000
            )

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

            # Trust V1 + V1.1 · 打开精修后 refine=on
            refine_on = page.evaluate(
                """() => document.documentElement.getAttribute('data-preview-refine')"""
            )
            assert refine_on == "on"

            page.locator(".preview-sheet__close").click()
            page.locator(".preview-sheet-root").wait_for(state="hidden", timeout=5_000)

            # V1.1 MF-01 · 关面板不退出模式
            refine_keep = page.evaluate(
                """() => document.documentElement.getAttribute('data-preview-refine')"""
            )
            assert refine_keep == "on"

            dock_done = page.evaluate(
                """() => {
                const btn = document.querySelector('.preview-toolbar__menu-btn');
                const label = btn && btn.querySelector('.preview-toolbar__dock-label');
                return {
                  label: label ? label.textContent.trim() : '',
                  aria: btn ? btn.getAttribute('aria-label') : '',
                  pressed: btn ? btn.getAttribute('aria-pressed') : '',
                  expanded: btn ? btn.getAttribute('aria-expanded') : '',
                  chip: !!(document.getElementById('preview-refine-mode-chip')
                    && !document.getElementById('preview-refine-mode-chip').hidden),
                };
            }"""
            )
            assert dock_done["label"] == "完成", dock_done
            assert dock_done["aria"] == "完成", dock_done
            assert dock_done["pressed"] == "true", dock_done
            assert dock_done["expanded"] == "false", dock_done
            assert dock_done["chip"] is True, dock_done

            focused_menu = page.evaluate(
                """() => {
                const btn = document.querySelector('.preview-toolbar__menu-btn');
                return btn && document.activeElement === btn;
            }"""
            )
            assert focused_menu is True

            # 导出文案范围已迁入 Dock ▾
            caret = page.locator(".preview-toolbar__longshot-caret")
            assert caret.count() >= 1
            caret.first.click(force=True)
            page.wait_for_selector(
                '.preview-toolbar__export-popover:not([hidden]) [data-copy-preset="full"]',
                timeout=5_000,
            )
            page.wait_for_selector(
                '.preview-toolbar__export-popover:not([hidden]) .preview-toolbar__export-more',
                timeout=5_000,
            )
            assert "更多输出" in page.locator(
                ".preview-toolbar__export-popover:not([hidden])"
            ).inner_text()
            page.keyboard.press("Escape")
            page.wait_for_timeout(200)

            # 「完成」退出模式
            page.locator(".preview-toolbar__menu-btn").click()
            page.wait_for_timeout(200)
            refine_off = page.evaluate(
                """() => document.documentElement.getAttribute('data-preview-refine')"""
            )
            assert refine_off == "off"
            dock_idle = page.evaluate(
                """() => {
                const btn = document.querySelector('.preview-toolbar__menu-btn');
                const label = btn && btn.querySelector('.preview-toolbar__dock-label');
                return {
                  label: label ? label.textContent.trim() : '',
                  pressed: btn ? btn.getAttribute('aria-pressed') : '',
                };
            }"""
            )
            assert dock_idle["label"] == "精修", dock_idle
            assert dock_idle["pressed"] == "false", dock_idle

            browser.close()
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
@pytest.mark.playwright_serial
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


def test_preview_refine_v1_p0_copy_and_intercept_markers() -> None:
    """PRD-PREVIEW-REFINE-V1 · P0 MF-01～06 静态门禁。"""
    dock = (STUDIO / "preview-toolbar" / "dock.js").read_text(encoding="utf-8")
    bootstrap = (STUDIO / "preview-toolbar" / "bootstrap.js").read_text(encoding="utf-8")
    longshot = (STUDIO / "preview-toolbar" / "longshot.js").read_text(encoding="utf-8")
    core = (STUDIO / "preview-toolbar" / "core.js").read_text(encoding="utf-8")
    sheet = SHEET_JS.read_text(encoding="utf-8")
    task_dock = TASK_DOCK_JS.read_text(encoding="utf-8")
    modal = (STUDIO / "studio-modal.js").read_text(encoding="utf-8")
    home = (STUDIO / "studio-home-v2.html").read_text(encoding="utf-8")

    assert 'case "refine":' in dock
    assert 'dockIconSvg("refine")' in bootstrap
    assert 'aria-label="精修"' in bootstrap
    assert "导出前先更新一下" in longshot
    assert "版面尚未更新" not in longshot
    assert "更新并导出" in longshot
    assert "仅更新版面" in longshot
    assert "_getLayoutPending()" in longshot
    assert "consumeExportAfterLayout" in longshot
    assert "export_after_layout_consumed" in longshot
    assert "longshot_export_blocked_pending" in longshot
    assert "EXPORT_AFTER_TTL_MS" in longshot
    assert "shouldShowExportPulse" in longshot
    assert "layoutUpdating" in longshot
    assert "版面没有更新成功，长图尚未开始" in longshot
    assert "再点「长图」即可导出" in longshot
    # First-Session Trust · 默认成功面 = 已保存确认（不塞发群教学）
    assert "长图已保存" in task_dock
    assert 'guide.text.replace' not in task_dock
    assert "怎么发到微信群？" in task_dock
    assert "help-onboarding" in task_dock
    assert "已保存到本机 · 拖进微信群即可" not in task_dock
    assert "showNextStepHint" in task_dock
    assert "在文件夹中显示" in task_dock
    assert 'preview-task-dock__btn--primary' in task_dock
    assert "版面有改动" in core
    assert "正在更新版面" in core
    assert "有编辑尚未应用排版" not in core
    assert "应用排版" not in task_dock
    assert "更新版面" in task_dock
    assert "版面有改动" in task_dock
    assert ">精修<" in sheet or 'preview-sheet__title">精修' in sheet
    assert "改精选或拼图后，请点「更新版面」。" not in sheet
    assert "secondaryText" in modal
    assert "studio__modal-actions--stacked" in modal
    assert "设置" in home
    assert ">设置<" in home
    assert 'aria-label="设置"' in home
    assert "导入偏好" in home
    assert "导入与分析" in home
    assert 'id="v2-settings-zone-ai"' in home
    assert 'id="studio-llm-settings-entry"' in home
    assert "工作台设置" not in home
    assert "编辑与设置" not in bootstrap
    assert "编辑与设置" not in sheet
    assert "本机文案 · 点此生成杂志感（不会自动重写）" in sheet
    assert "preview-sheet__llm-expect" in sheet
    init_v3 = (STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    assert "llmExpect" in init_v3
    assert "MF-06" in init_v3 or "不会自动重写" in init_v3 or "llmExpect.hidden = false" in init_v3


def test_preview_refine_ux_v11_m1_mode_panel_decouple_markers() -> None:
    """PRD-PREVIEW-REFINE-UX-V1.1 · M1 模式≠面板静态门禁。"""
    mode = (STUDIO / "preview-toolbar" / "preview-mode.js").read_text(encoding="utf-8")
    init = (STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    sheet = SHEET_JS.read_text(encoding="utf-8")
    dock_css = (STUDIO / "preview-toolbar" / "dock.css").read_text(encoding="utf-8")

    assert "syncRefineDockChrome" in mode
    assert "maybeShowRefineStarTip" in mode
    assert "精修中" in mode
    assert "onExitRefineMode" in init
    assert "isRefineModeOn" in init
    assert "syncRefineDockChrome(root, { panelOpen: false })" in init
    assert "版面还没更新，可稍后在下方更新" in init
    assert "收起面板，回到画面" in sheet or "先收起面板" in sheet
    assert "onExitRefineMode" in sheet
    assert "isRefineModeOn" in sheet
    assert "preview-toolbar__refine-chip" in dock_css
    assert "preview-toolbar__dock-btn--done" in dock_css


def test_preview_export_facade_v1_markers() -> None:
    """PRD-PREVIEW-EXPORT-FACADE-V1 · 续跑可靠 / 发群引导 / 埋点门禁。"""
    longshot = (STUDIO / "preview-toolbar" / "longshot.js").read_text(encoding="utf-8")
    core = (STUDIO / "preview-toolbar" / "core.js").read_text(encoding="utf-8")
    init_v3 = (STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    task_dock = TASK_DOCK_JS.read_text(encoding="utf-8")
    css = (STUDIO / "preview-toolbar" / "task-dock.css").read_text(encoding="utf-8")

    assert "expectLayoutReload" in longshot
    assert "export_after_layout_cleared" in longshot
    assert "longshot_export_block_dismissed" in longshot
    assert "layout_update_and_export" in longshot
    assert "layout_update_only" in longshot
    assert "layout_update_failed" in longshot
    assert "longshot_success_share_hint_shown" in longshot
    assert "from: from" in longshot
    assert "beforeReload" in core
    assert "failMessage" in core
    assert "shouldShowExportPulse" in init_v3
    assert "打开导出选项不停止脉冲" in init_v3
    assert "preview-task-dock--next-hint" in task_dock
    assert "preview-task-dock--next-hint" in css
    assert 'textContent = "在文件夹中显示"' in task_dock
    assert 'textContent = "打开文件夹"' not in task_dock
    # D-FST-13 · 禁止自动 reveal
    assert "autoRevealLongshotOutputs" not in longshot
    assert "longshot_auto_reveal" not in longshot
    assert "禁止自动 reveal" in longshot
    assert "已保存到此游记文件夹" in task_dock
    assert "导出时仍会提醒" in task_dock
    assert "preview-task-dock__remind" in css
    assert "按序发到朋友圈连读" in task_dock
    assert "导入小红书" in task_dock
    assert "onFail" in core
    assert "error_code" in longshot
    init_v3 = (STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    # F-EXP-09 · 非 Dock 可见「长图」
    assert 'longshotBtn.textContent = "长图"' in init_v3
    assert 'longshotBtn.textContent = "导出长图"' not in init_v3


def test_preview_refine_v1_p1_g1_banner_and_three_zone_ia() -> None:
    """PRD-PREVIEW-REFINE-V1 · 三区 IA；G1 默认黄条已被 PCU 取代（D-PCU-01/10）。"""
    features = (STUDIO / "preview-toolbar" / "features.js").read_text(encoding="utf-8")
    core = (STUDIO / "preview-toolbar" / "core.js").read_text(encoding="utf-8")
    init_v3 = (STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    sheet = SHEET_JS.read_text(encoding="utf-8")
    drawers = (STUDIO / "preview-toolbar" / "drawers.js").read_text(encoding="utf-8")
    shell = (STUDIO / "preview-toolbar" / "shell.js").read_text(encoding="utf-8")
    chap = (STUDIO / "preview-toolbar" / "chapter-panel.js").read_text(encoding="utf-8")

    # 废弃函数仍可存在，但 init 不得挂默认黄条
    assert "mountG1Banner" in features
    assert "mountG1Banner(root, drawers)" not in features.split("export function initG1V3")[1].split(
        "export function mountG1Banner"
    )[0]
    assert "pcu_legacy_g1_autoconfirm" in features
    assert "_openChapterPanel" in features or "mountChapterPanel" in init_v3
    assert "dock-btn--chapters" in init_v3
    assert "preview-dock-stat" in init_v3
    assert "studio-help-open--dock" in init_v3
    assert "showG1" not in core.split("export function refreshTaskDockState")[1].split(
        "if (_layoutPending"
    )[0]
    assert "preview-chapter-panel" in chap
    assert "确认并继续" in chap
    dock_css = (STUDIO / "preview-toolbar" / "dock.css").read_text(encoding="utf-8")
    # MF-05 · Dock 触控目标 ≥40px（含窄屏折叠态）
    assert "min-width: 40px" in dock_css
    assert "min-height: 40px" in dock_css
    assert (
        ".preview-toolbar--v4 .preview-toolbar__dock .preview-toolbar__dock-btn--labeled {\n"
        "    padding: 0;\n"
        "    width: 40px;"
    ) in dock_css or "width: 40px;\n    min-width: 40px;\n    max-width: 40px;" in dock_css
    assert 'label: "这页"' in sheet
    assert 'label: "封面"' in sheet
    assert 'label: "这本"' in sheet
    assert 'label: "导出"' not in sheet
    assert 'label: "导出与更多"' not in sheet
    assert "封底在「封面」里换" in sheet
    assert "regenerateStructure" in drawers
    assert 'label: "文字"' not in sheet
    assert 'label: "高级"' not in sheet
    assert "精修 · 这本" in shell
    assert "可在「排版」中更换" not in shell
    assert "preview-dock-stat" in shell or "准备高清 ·" in shell


def test_preview_refine_ux_v11_m2_markers() -> None:
    """PRD-PREVIEW-REFINE-UX-V1.1 · M2 演进：封面 Tab + 导出决策迁入 ▾。"""
    sheet = SHEET_JS.read_text(encoding="utf-8")
    drawers = (STUDIO / "preview-toolbar" / "drawers.js").read_text(encoding="utf-8")
    mode = (STUDIO / "preview-toolbar" / "preview-mode.js").read_text(encoding="utf-8")
    init = (STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    bookends = (STUDIO / "preview-toolbar" / "bookends.js").read_text(encoding="utf-8")
    css = (STUDIO / "preview-toolbar" / "sheet.css").read_text(encoding="utf-8")
    panel = (STUDIO / "js" / "longshot-export-panel.js").read_text(encoding="utf-8")

    assert "bookEditTpl" in drawers
    assert "pageEditTpl" in drawers
    assert "edit-page" in drawers
    assert "给这本游记的一句话" in drawers
    assert "写给编辑的一句话" not in drawers
    assert "想写进图说的词" in drawers
    assert "记忆锚点" not in drawers
    assert "preview-drawer__featured-help" not in drawers
    assert 'openEmbed("edit-page"' in sheet
    assert "renderCoverPanel" in sheet
    assert "bookAdvancedToolsHtml" in sheet
    assert "preview-sheet__more-tools" not in sheet
    assert "长图要不要字" in panel
    assert 'data-copy-preset="full"' in panel
    assert "当前为本机文案 · 配置写作引擎后可升级" in sheet
    assert 'data-action="llm-setup"' in sheet
    assert "preview-sheet__llm-expect" in sheet
    assert "本机文案 · 点此生成杂志感（不会自动重写）" in sheet
    assert "maybeShowBookTabMigrateTip" in mode
    assert "book_tab_migrate_tip_show" in mode
    assert "onBookTabRendered" in init
    assert "aria-label" in bookends
    assert 'data-cover-side="opening"' in css
    assert "preview-sheet__bookends-thumb-badge" in bookends
    assert "预览手机效果" in bookends
    assert "bookendsMobileOnce" in bookends
    assert "在画面上看封面" in bookends
    assert "在画面上看封底" in bookends
    assert 'class="preview-sheet__primary" data-bookends-scroll-opening' in bookends
    assert "height: 64px" in css
    assert "repeat(3, 48px)" in css
    assert "repeat(5, 48px)" in css
    assert sheet.count("更新版面") <= 2  # 进阶主按钮 + 可能的文案对照
    css_vj = (ROOT / "templates" / "visual-journal" / "journal-screens.css").read_text(
        encoding="utf-8"
    )
    assert 'content: "\\201C"' in css_vj or 'content: "\\201C";' in css_vj
    assert "C" not in css_vj

    home = (STUDIO / "studio-home-v2.html").read_text(encoding="utf-8")
    assert "给这本游记的一句话" in home
    assert "写给编辑的一句话" not in home

    features = (STUDIO / "preview-toolbar" / "features.js").read_text(encoding="utf-8")
    assert 'trackStudioEvent("refine_mode_enter"' in init
    assert 'trackStudioEvent("refine_panel_close"' in init
    assert 'trackStudioEvent("refine_mode_exit"' in init
    assert 'trackStudioEvent("featured_star_click"' in features
    assert 'trackStudioEvent("cover_candidate_click"' in bookends
    assert "长图要不要字" in panel
    assert 'data-field="copy"' in panel
    assert "更多输出" in panel
    assert ">更清晰<" in panel


def test_preview_refine_v1_d_ref_13_rewrite_copy() -> None:
    """D-REF-13 · 按新感觉重写：文案 + 二次确认 + busy。"""
    drawers = (STUDIO / "preview-toolbar" / "drawers.js").read_text(encoding="utf-8")
    core = (STUDIO / "preview-toolbar" / "core.js").read_text(encoding="utf-8")
    assert "按新感觉重写这段" in drawers
    assert "正在重写…" in drawers
    assert "skipConfirm: true" in drawers
    assert "保存并重新生成文案" not in drawers
    assert "opts.skipConfirm" in core or "skipConfirm" in core


def test_preview_refine_v1_p2_feedback_and_cohort_gate() -> None:
    """PRD-PREVIEW-REFINE-V1 · P2 M5 inline ✓ + M6 cohort 藏入口。"""
    inline_js = (ROOT / "templates" / "visual-journal" / "inline-edit.js").read_text(
        encoding="utf-8"
    )
    inline_css = (ROOT / "templates" / "visual-journal" / "inline-edit.css").read_text(
        encoding="utf-8"
    )
    cover_js = (STUDIO / "preview-toolbar" / "inline-edit.js").read_text(encoding="utf-8")
    sheet = SHEET_JS.read_text(encoding="utf-8")
    task_dock = TASK_DOCK_JS.read_text(encoding="utf-8")
    init_v3 = (STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    longshot = (STUDIO / "preview-toolbar" / "longshot.js").read_text(encoding="utf-8")
    hbs = (
        ROOT / "templates" / "visual-journal" / "partials" / "longshot-toolbar.hbs"
    ).read_text(encoding="utf-8")

    assert "已保存到 trip.json" not in inline_js
    assert "showFieldSavedMark" in inline_js
    assert "点一下文案可修改" in inline_js
    assert "inline-edit__field--saved::after" in inline_css
    assert 'content: "✓"' in inline_css
    assert "cover-opening__title--saved" in cover_js
    assert "杂志名已保存" not in cover_js
    assert "cohortEmbed.hidden = true" in sheet
    assert "旅行主角 · 同框未开启" not in sheet
    assert "showStale" in task_dock
    assert "分享图需更新" in task_dock
    assert "重新导出" in task_dock
    assert "onReExport" in init_v3
    assert "未保存的编辑" not in init_v3
    assert "_longshotStale" in longshot
    assert "保存到 trip.json" not in hbs
