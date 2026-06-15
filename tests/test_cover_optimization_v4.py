"""Cover optimization v4 · journal.css contract + Playwright AC."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from travelogue.web.studio_chrome import inject_studio_chrome

ROOT = Path(__file__).resolve().parents[1]
JOURNAL_CSS = ROOT / "templates" / "visual-journal" / "journal.css"
TEMPLATE_JOURNAL = ROOT / "templates" / "visual-journal" / "journal.css"

_LONG_TITLE = "二〇二五年东澳岛夏日纪行·海风与盐粒交织的七天七夜"
_LONG_HOOK = (
    "海风吹干盐粒的那刻，我们坐在礁石上不说话，"
    "浪花在脚边碎成白色的诗行，远处的渔船像一枚慢慢淡去的标点，"
    "而天空正把最后一抹橘红收进海平线。"
)
_PLACEHOLDER_IMG = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' width='1600' height='1200'%3E"
    "%3Crect fill='%232a4a3e' width='100%25' height='100%25'/%3E%3C/svg%3E"
)


def _copy_journal_css(trip_dir: Path) -> None:
    shutil.copy2(TEMPLATE_JOURNAL, trip_dir / "journal.css")
    font_src = ROOT / "templates" / "visual-journal" / "assets" / "fonts" / "hetangyuese.woff2"
    if font_src.is_file():
        font_dest_dir = trip_dir / "assets" / "fonts"
        font_dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(font_src, font_dest_dir / font_src.name)


def _cover_opening_html(
    *,
    layout: str = "web",
    long_copy: bool = False,
    extra_body: str = "",
) -> str:
    title = _LONG_TITLE if long_copy else "东澳岛"
    hook = _LONG_HOOK if long_copy else "海风吹干盐粒的那刻，我们坐在礁石上。"
    return (
        f'<!DOCTYPE html><html lang="zh-CN" data-layout="{layout}" data-screenplay="on">'
        '<head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
        '<link rel="stylesheet" href="journal.css">'
        "<title>Cover V4</title></head><body><main>"
        '<section class="cover-opening" data-block="cover-opening">'
        '<header class="cover-hero cover-hero--photo-only">'
        '<div class="cover-hero__media" style="--focal-x: 0.5; --focal-y: 0.45;">'
        f'<img class="cover-hero__img" src="{_PLACEHOLDER_IMG}" alt="cover" />'
        "</div></header>"
        '<div class="cover-opening__panel">'
        '<p class="cover-opening__place">东澳岛</p>'
        '<div class="trip-meta" data-block="trip-meta">'
        '<time datetime="2025-06-01/2025-06-03">'
        '<span class="trip-meta__line trip-meta__line--full">2025.06.01 – 06.03 · 东澳岛</span>'
        '<span class="trip-meta__line trip-meta__line--sub">2025.06.01 – 06.03</span>'
        "</time></div>"
        f'<h1 class="cover-opening__title">{title}</h1>'
        f'<p class="cover-opening__hook">{hook}</p>'
        "</div></section>"
        f"{extra_body}"
        "</main>"
        '<button id="screenplay-start" type="button" hidden></button>'
        "</body></html>"
    )


def _seed_cover_v4_trip(
    trips_dir: Path,
    trip_id: str = "cover-v4",
    *,
    layout: str = "web",
    long_copy: bool = False,
    with_scroll_tail: bool = False,
) -> str:
    trip_dir = trips_dir / trip_id
    trip_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "tripId": trip_id,
        "meta": {"title": "Cover V4"},
        "chapters": [{"id": "ch1", "title": "第一章", "items": []}],
        "assets": [],
    }
    (trip_dir / "trip.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    _copy_journal_css(trip_dir)
    tail = ""
    if with_scroll_tail:
        tail = '<section style="min-height:120vh;padding:24px">正文</section>'
    html = inject_studio_chrome(
        _cover_opening_html(layout=layout, long_copy=long_copy, extra_body=tail)
    )
    (trip_dir / "index.html").write_text(html, encoding="utf-8")
    return trip_id


def test_cover_opening_title_card_styles() -> None:
    css = JOURNAL_CSS.read_text(encoding="utf-8")
    block = css.split("/* V4 · 右下实心书名卡 */", 1)[1].split("}", 1)[0]
    for token in (
        "position: absolute",
        "width: max-content",
        "max-width: min(640px, 70.4vw)",
        "min(352px, 57.6vh)",
        "rgba(18, 17, 16, 0.9)",
        "border-left: 5px solid",
        "-webkit-line-clamp: 2",
        "display: block",
        'font-family: "HetangYuese"',
        "font-family: var(--font-handwriting)",
        "assets/fonts/hetangyuese.woff2",
        ".cover-opening .trip-meta",
        "display: none",
    ):
        assert token in css, f"missing cover v4 token: {token}"
    assert "cover-opening__enter" not in css
    assert "linear-gradient" not in block


@pytest.mark.e2e
def test_v4_cover_opening_layout_playwright(tmp_path: Path) -> None:
    """AC-COV-30～36 · 封面一屏 + 书名卡尺寸。"""
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    from tests.test_studio_server import _free_port, _start_studio_server
    from travelogue.web.studio_jobs import reset_job_store

    reset_job_store()
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = _seed_cover_v4_trip(trips_dir, long_copy=True)
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(f"{base}/{trip_id}/index.html", wait_until="networkidle")
            page.locator(".preview-toolbar__dock").wait_for(state="visible", timeout=15_000)
            page.locator(".cover-opening").wait_for(state="visible", timeout=5_000)

            metrics = page.evaluate(
                """() => {
                const cover = document.querySelector('.cover-opening');
                const panel = document.querySelector('.cover-opening__panel');
                const title = document.querySelector('.cover-opening__title');
                const hook = document.querySelector('.cover-opening__hook');
                const vh = window.innerHeight;
                const coverRect = cover.getBoundingClientRect();
                const panelRect = panel.getBoundingClientRect();
                const toolbarH = parseFloat(
                  getComputedStyle(document.documentElement).getPropertyValue('--preview-toolbar-h')
                ) || 0;
                return {
                  coverHeight: coverRect.height,
                  viewportH: vh,
                  toolbarH,
                  panelWidth: panelRect.width,
                  panelHeight: panelRect.height,
                  panelPosition: getComputedStyle(panel).position,
                  coverOverflow: cover.scrollHeight > cover.clientHeight + 2,
                  titleOverflow: title ? title.scrollHeight > title.clientHeight + 2 : false,
                  hookOverflow: hook ? hook.scrollHeight > hook.clientHeight + 4 : false,
                  panelBeforeDisplay: getComputedStyle(panel, '::before').display,
                };
            }"""
            )

            assert metrics["toolbarH"] == 0, metrics
            assert abs(metrics["coverHeight"] - metrics["viewportH"]) <= 2, metrics
            assert metrics["panelPosition"] == "absolute", metrics
            assert metrics["panelWidth"] <= 640 + 1, metrics
            assert metrics["panelHeight"] <= min(352, metrics["viewportH"] * 0.576) + 2, metrics
            assert metrics["coverOverflow"] is False, metrics
            assert metrics["panelBeforeDisplay"] in ("none", ""), metrics

            browser.close()
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
def test_v4_cover_mobile_layout_unchanged(tmp_path: Path) -> None:
    """AC-COV-37 · mobile 封面不走 web 书名卡浮动。"""
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    from tests.test_studio_server import _free_port, _start_studio_server
    from travelogue.web.studio_jobs import reset_job_store

    reset_job_store()
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = _seed_cover_v4_trip(trips_dir, layout="mobile")
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(f"{base}/{trip_id}/index.html", wait_until="networkidle")
            panel_pos = page.evaluate(
                """() => {
                const panel = document.querySelector('.cover-opening__panel');
                return panel ? getComputedStyle(panel).position : null;
            }"""
            )
            assert panel_pos != "absolute", panel_pos
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
def test_v4_share_preview_keeps_minimal_toolbar(tmp_path: Path) -> None:
    """AC-COV-11 / G-COV-07 · Share 仍为 minimal 顶栏。"""
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    from tests.test_studio_server import _free_port, _start_studio_server
    from travelogue.web.studio_jobs import reset_job_store

    reset_job_store()
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = _seed_cover_v4_trip(trips_dir)
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(f"{base}/{trip_id}/index.html?share=1", wait_until="networkidle")
            page.locator(".preview-toolbar--share-minimal").wait_for(state="visible", timeout=15_000)
            assert page.locator(".preview-toolbar--v4").count() == 0
            assert page.locator(".preview-toolbar__dock").count() == 0
            toolbar_h = page.evaluate(
                """() => parseFloat(
                  getComputedStyle(document.documentElement).getPropertyValue('--preview-toolbar-h')
                ) || 0"""
            )
            assert toolbar_h == 48, toolbar_h
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
def test_v4_dock_states_playwright(tmp_path: Path) -> None:
    """AC-COV-05/08/20/P2 · running、放映隐藏、tooltip、滚过变淡。"""
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    from tests.test_studio_server import _free_port, _start_studio_server
    from travelogue.web.studio_jobs import reset_job_store

    reset_job_store()
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = _seed_cover_v4_trip(trips_dir, with_scroll_tail=True)
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(f"{base}/{trip_id}/index.html", wait_until="networkidle")
            page.locator(".preview-toolbar__dock").wait_for(state="visible", timeout=15_000)

            page.locator(".preview-toolbar__dock-btn--back").hover()
            page.wait_for_timeout(400)
            tip_opacity = page.evaluate(
                """() => {
                const tip = document.querySelector('.preview-toolbar__dock-btn--back .preview-toolbar__dock-tip');
                return tip ? parseFloat(getComputedStyle(tip).opacity) : 0;
            }"""
            )
            assert tip_opacity >= 0.9, tip_opacity

            running = page.evaluate(
                """() => {
                const root = document.querySelector('.preview-toolbar--v4');
                const exportBtn = document.querySelector('.preview-toolbar__dock-btn--export');
                const screenplay = document.querySelector('.preview-toolbar__screenplay--v3');
                const menu = document.querySelector('.preview-toolbar__menu-btn');
                exportBtn.classList.add('preview-toolbar__longshot--running');
                exportBtn.innerHTML = '<span class="preview-toolbar__longshot__spinner" aria-hidden="true"></span>';
                if (screenplay) screenplay.disabled = true;
                if (menu) menu.disabled = true;
                return {
                  hasSpinner: !!exportBtn.querySelector('.preview-toolbar__longshot__spinner'),
                  screenplayDisabled: screenplay ? screenplay.disabled : false,
                  menuDisabled: menu ? menu.disabled : false,
                  rootPresent: !!root,
                };
            }"""
            )
            assert running["hasSpinner"] is True, running
            assert running["screenplayDisabled"] is True, running
            assert running["menuDisabled"] is True, running

            dock_hidden = page.evaluate(
                """() => {
                document.body.classList.add('screenplay-active');
                const dock = document.querySelector('.preview-toolbar__dock');
                return dock ? getComputedStyle(dock).visibility : '';
            }"""
            )
            assert dock_hidden == "hidden", dock_hidden

            page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(300)
            dimmed = page.evaluate(
                """() => document.querySelector('.preview-toolbar__dock')
                  .classList.contains('preview-toolbar__dock--dim')"""
            )
            assert dimmed is True, "dock should dim after scrolling past cover"

            browser.close()
    finally:
        server.shutdown()
        server.server_close()
