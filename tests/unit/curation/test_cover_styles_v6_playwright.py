"""Cover Styles V6 · Playwright minimal suite (skins / narrow / dock)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from travelogue.paths import ROOT
from travelogue.web.studio_chrome import inject_studio_chrome

JOURNAL_CSS = ROOT / "templates" / "visual-journal" / "journal.css"
_PLACEHOLDER_IMG = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' width='1600' height='1200'%3E"
    "%3Crect fill='%232a4a3e' width='100%25' height='100%25'/%3E%3C/svg%3E"
)
_V6_STYLES = (
    "veil-footer",
    "folio-overlap",
    "band-cut",
    "cameo-aperture",
    "type-monument",
    "scroll-head",
    "portal-arch",
    "horizon-split",
    "contact-stamp",
    "diptych-seam",
)
_LONG_TITLE = "二〇二五年东澳岛夏日纪行·海风与盐粒交织的七天七夜"
_LONG_HOOK = (
    "海风吹干盐粒的那刻，我们坐在礁石上不说话，"
    "浪花在脚边碎成白色的诗行，远处的渔船像一枚慢慢淡去的标点。"
)
_COVER_METRICS_JS = """() => {
  const cover = document.querySelector('.cover-opening');
  const panel = document.querySelector('.cover-opening__panel');
  const title = document.querySelector('.cover-opening__title');
  const hook = document.querySelector('.cover-opening__hook');
  const dock = document.querySelector('.preview-toolbar__dock');
  if (!cover || !panel || !title) return null;
  const coverRect = cover.getBoundingClientRect();
  const panelRect = panel.getBoundingClientRect();
  const titleRect = title.getBoundingClientRect();
  const dockRect = dock ? dock.getBoundingClientRect() : null;
  const csFog = getComputedStyle(cover, '::after');
  const overlapsDock = !!(dockRect && !(
    panelRect.right < dockRect.left ||
    panelRect.left > dockRect.right ||
    panelRect.bottom < dockRect.top ||
    panelRect.top > dockRect.bottom
  ));
  return {
    style: cover.getAttribute('data-cover-opening'),
    viewportH: window.innerHeight,
    viewportW: window.innerWidth,
    coverHeight: coverRect.height,
    coverOverflow: cover.scrollHeight > cover.clientHeight + 2,
    titleBottom: titleRect.bottom,
    panelBottom: panelRect.bottom,
    fogDisplay: csFog.display,
    fogHeight: csFog.height,
    dockVisible: !!(dock && getComputedStyle(dock).display !== 'none'),
    dockTop: dockRect ? dockRect.top : null,
    dockRightGap: dockRect ? (window.innerWidth - dockRect.right) : null,
    panelOverlapsDock: overlapsDock,
    hasHook: !!hook,
  };
}"""


def _cover_html(*, layout: str, style: str, title: str, hook: str, include_hook: bool) -> str:
    hook_html = (
        f'<p class="hook-line cover-opening__hook">{hook}</p>' if include_hook else ""
    )
    return (
        f'<!DOCTYPE html><html lang="zh-CN" data-layout="{layout}" data-screenplay="on">'
        '<head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
        '<link rel="stylesheet" href="journal.css">'
        f"<title>Cover {style}</title></head><body><main>"
        f'<section class="cover-opening" data-block="cover-opening" data-cover-opening="{style}">'
        '<header class="cover-hero cover-hero--photo-only">'
        '<div class="cover-hero__media" style="--focal-x: 0.5; --focal-y: 0.45;">'
        f'<img class="cover-hero__img" src="{_PLACEHOLDER_IMG}" alt="cover" />'
        "</div></header>"
        '<div class="cover-opening__panel">'
        '<p class="cover-opening__place">东澳岛</p>'
        f'<h1 class="cover-opening__title">{title}</h1>'
        f"{hook_html}"
        "</div></section>"
        "</main></body></html>"
    )


def _seed(trips_dir: Path, trip_id: str, *, style: str, include_hook: bool = True) -> str:
    trip_dir = trips_dir / trip_id
    trip_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "tripId": trip_id,
        "meta": {"title": _LONG_TITLE, "coverOpeningStyle": style},
        "chapters": [{"id": "ch1", "title": "第一章", "items": []}],
        "assets": [],
    }
    (trip_dir / "trip.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    shutil.copy2(JOURNAL_CSS, trip_dir / "journal.css")
    html = inject_studio_chrome(
        _cover_html(
            layout="web",
            style=style,
            title=_LONG_TITLE,
            hook=_LONG_HOOK,
            include_hook=include_hook,
        )
    )
    (trip_dir / "index.html").write_text(html, encoding="utf-8")
    return trip_id


def _playwright_page(tmp_path: Path, trip_id: str, *, viewport: dict):
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    from tests.integration.studio.test_studio_server import _free_port, _start_studio_server
    from travelogue.web.studio_jobs import reset_job_store

    reset_job_store()
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir(exist_ok=True)
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    url = f"http://127.0.0.1:{port}/{trip_id}/index.html"

    class _Ctx:
        def __init__(self) -> None:
            self.pw = sync_playwright().start()
            self.browser = self.pw.chromium.launch()
            self.page = self.browser.new_page(viewport=viewport)
            self.server = server

        def close(self) -> None:
            self.browser.close()
            self.pw.stop()
            self.server.shutdown()
            self.server.server_close()

    ctx = _Ctx()
    ctx.page.goto(url, wait_until="networkidle")
    ctx.page.locator(".preview-toolbar__dock").wait_for(state="visible", timeout=15_000)
    ctx.page.locator(".cover-opening").wait_for(state="visible", timeout=5_000)
    return ctx


@pytest.mark.e2e
@pytest.mark.playwright_serial
@pytest.mark.parametrize("style", list(_V6_STYLES))
def test_cover_styles_v6_wide_no_overflow(tmp_path: Path, style: str) -> None:
    """AC-CSV6-10..14 · 十款宽屏一屏无溢出。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = _seed(trips_dir, f"v6-{style}-wide", style=style)
    ctx = _playwright_page(tmp_path, trip_id, viewport={"width": 1280, "height": 800})
    try:
        m = ctx.page.evaluate(_COVER_METRICS_JS)
        assert m is not None
        assert m["style"] == style
        assert abs(m["coverHeight"] - m["viewportH"]) <= 4, m
        assert m["coverOverflow"] is False, m
        assert m["titleBottom"] <= m["viewportH"] + 2, m
    finally:
        ctx.close()


@pytest.mark.e2e
@pytest.mark.playwright_serial
@pytest.mark.parametrize("style", ["folio-overlap", "band-cut", "cameo-aperture"])
def test_cover_styles_v6_narrow_presents_as_veil(tmp_path: Path, style: str) -> None:
    """AC-CSV6-31 · <1024px 呈现回落雾底，但 data-cover-opening 不变。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = _seed(trips_dir, f"v6-{style}-narrow", style=style)
    ctx = _playwright_page(tmp_path, trip_id, viewport={"width": 1023, "height": 800})
    try:
        m = ctx.page.evaluate(_COVER_METRICS_JS)
        assert m is not None
        assert m["style"] == style
        # V6 skins gated at 64rem; narrow keeps veil fog (::after visible)
        assert m["fogDisplay"] != "none", m
        assert m["coverOverflow"] is False, m
    finally:
        ctx.close()


@pytest.mark.e2e
@pytest.mark.playwright_serial
def test_cover_styles_v6_dock_safe_zone(tmp_path: Path) -> None:
    """AC-CSV6-33/34 · Dock 可见且不与题签 panel 重叠。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = _seed(trips_dir, "v6-dock-safe", style="veil-footer")
    ctx = _playwright_page(tmp_path, trip_id, viewport={"width": 1280, "height": 800})
    try:
        m = ctx.page.evaluate(_COVER_METRICS_JS)
        assert m is not None
        assert m["dockVisible"] is True
        assert m["dockTop"] is not None and m["dockTop"] < 80
        assert m["panelOverlapsDock"] is False, m
    finally:
        ctx.close()


@pytest.mark.e2e
@pytest.mark.playwright_serial
def test_cover_styles_v6_folio_no_hook_hides_accent(tmp_path: Path) -> None:
    """AC-CSV6-15 · folio 无 hook 去掉 accent 细线。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = _seed(
        trips_dir, "v6-folio-no-hook", style="folio-overlap", include_hook=False
    )
    ctx = _playwright_page(tmp_path, trip_id, viewport={"width": 1280, "height": 800})
    try:
        display = ctx.page.evaluate(
            """() => {
              const title = document.querySelector('.cover-opening__title');
              if (!title) return null;
              return getComputedStyle(title, '::after').display;
            }"""
        )
        assert display == "none"
        m = ctx.page.evaluate(_COVER_METRICS_JS)
        assert m is not None
        assert m["hasHook"] is False
        assert m["coverOverflow"] is False, m
    finally:
        ctx.close()


def test_cover_styles_v6_css_tokens_present() -> None:
    css = JOURNAL_CSS.read_text(encoding="utf-8")
    for token in (
        "--cover-folio-fade",
        "--cover-cameo-ground",
        "--cover-cameo-ring",
        "--cover-cameo-r",
        "--cover-monument-dim",
        "--cover-band-ink",
        "--cover-band-label-max",
        "--cover-veil-glow",
        "--cover-folio-cut",
        "--cover-dock-safe",
        "--cover-panel-z",
        "cover-opening__placeholder-badge",
        "cover-opening__explain-line",
    ):
        assert token in css, f"missing {token}"
    assert "--cover-band-center: 63%" in css or "--cover-band-center:63%" in css.replace(" ", "")
    assert "--cover-veil-fog-height: 70%" in css or "--cover-veil-fog-height:70%" in css.replace(" ", "")
    assert "--cover-folio-margin: 13%" in css or "--cover-folio-margin:13%" in css.replace(" ", "")
