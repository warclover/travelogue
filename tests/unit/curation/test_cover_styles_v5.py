"""Cover Styles V5 · assignment, resolve, render binding + Playwright AC."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from travelogue.paths import ROOT, TEMPLATE_VISUAL_JOURNAL
from travelogue.render.assemble import build_render_context
from travelogue.render.cover_opening import resolve_split_mat_title_layout
from travelogue.render.engine import render_trip
from travelogue.render.golden_regression import load_golden_trip
from travelogue.services.cover_opening_style import (
    COVER_OPENING_STYLES,
    assign_cover_opening_style,
    resolve_cover_opening_style,
)
from travelogue.services.trip_factory import create_trip
from travelogue.web.studio_chrome import inject_studio_chrome

JOURNAL_CSS = ROOT / "templates" / "visual-journal" / "journal.css"
_TEMPLATE_JOURNAL = JOURNAL_CSS
_FIXTURE = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"
_PLACEHOLDER_IMG = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' width='1600' height='1200'%3E"
    "%3Crect fill='%232a4a3e' width='100%25' height='100%25'/%3E%3C/svg%3E"
)
_LONG_TITLE = "二〇二五年东澳岛夏日纪行·海风与盐粒交织的七天七夜"
_LONG_HOOK = (
    "海风吹干盐粒的那刻，我们坐在礁石上不说话，"
    "浪花在脚边碎成白色的诗行，远处的渔船像一枚慢慢淡去的标点，"
    "而天空正把最后一抹橘红收进海平线。"
)
_COVER_METRICS_JS = """() => {
  const cover = document.querySelector('.cover-opening');
  const panel = document.querySelector('.cover-opening__panel');
  const hero = document.querySelector('.cover-hero');
  const title = document.querySelector('.cover-opening__title');
  const hook = document.querySelector('.cover-opening__hook');
  const dock = document.querySelector('.preview-toolbar__dock');
  if (!cover || !panel || !hero) return null;
  const csCover = getComputedStyle(cover);
  const csPanel = getComputedStyle(panel);
  const csHero = getComputedStyle(hero);
  const csTitle = title ? getComputedStyle(title) : null;
  const vh = window.innerHeight;
  const coverRect = cover.getBoundingClientRect();
  const panelRect = panel.getBoundingClientRect();
  const heroRect = hero.getBoundingClientRect();
  function parseRgb(color) {
    const m = color.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
    if (!m) return null;
    return [Number(m[1]), Number(m[2]), Number(m[3])];
  }
  function relLum(rgb) {
    const f = rgb.map((v) => {
      const c = v / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2];
  }
  function contrast(a, b) {
    const la = relLum(a);
    const lb = relLum(b);
    const hi = Math.max(la, lb);
    const lo = Math.min(la, lb);
    return (hi + 0.05) / (lo + 0.05);
  }
  const panelFg = parseRgb(csPanel.color);
  const panelBg = parseRgb(csPanel.backgroundColor);
  const titleFg = csTitle ? parseRgb(csTitle.color) : null;
  const headerBg = parseRgb(csPanel.backgroundColor);
  return {
    style: cover.getAttribute('data-cover-opening'),
    coverDisplay: csCover.display,
    coverHeight: coverRect.height,
    viewportH: vh,
    panelPosition: csPanel.position,
    heroPosition: csHero.position,
    panelTextAlign: csPanel.textAlign,
    titleTextAlign: csTitle ? csTitle.textAlign : '',
    panelBg: csPanel.backgroundColor,
    coverOverflow: cover.scrollHeight > cover.clientHeight + 2,
    titleOverflow: title ? title.scrollHeight > title.clientHeight + 4 : false,
    hookOverflow: hook ? hook.scrollHeight > hook.clientHeight + 4 : false,
    heroHeight: heroRect.height,
    panelHeight: panelRect.height,
    panelAboveHero: panelRect.bottom <= heroRect.top + 2,
    sideBySide: panelRect.left > heroRect.left + 80 && heroRect.width > 120 && panelRect.width > 120,
    heroRight: heroRect.right,
    panelLeft: panelRect.left,
    panelPaddingLeft: parseFloat(csPanel.paddingLeft) || 0,
    panelContrast: panelFg && panelBg ? contrast(panelFg, panelBg) : null,
    titleContrast: titleFg && headerBg ? contrast(titleFg, headerBg) : null,
    dockVisible: dock ? getComputedStyle(dock).visibility !== 'hidden' && parseFloat(getComputedStyle(dock).opacity) > 0.5 : false,
  };
}"""


def _attach_studio_event_collector(page) -> list[dict]:
    events: list[dict] = []

    def _on_request(req) -> None:
        if req.method == "POST" and req.url.endswith("/__travelogue/studio-event"):
            try:
                events.append(json.loads(req.post_data or "{}"))
            except (ValueError, TypeError):
                pass

    page.on("request", _on_request)
    return events


_LONGSHOT_CAPTURE_METRICS_JS = """async () => {
  const main = document.querySelector('main');
  const chapters = Array.from(main.querySelectorAll('section.chapter'));
  const coverOpening = main.querySelector('.cover-opening');
  const cover = coverOpening || main.querySelector('.cover-hero');
  const pageEl = main.querySelector('.page');
  const hook = main.querySelector('.hook-line');
  const epilogue = pageEl && pageEl.querySelector('.epilogue');
  const tripMeta = main.querySelector('.trip-meta');
  function stash(el, show) {
    if (!el) return;
    el.hidden = !show;
    el.style.display = show ? '' : 'none';
  }
  chapters.forEach((ch, i) => stash(ch, i === 0));
  stash(cover, true);
  if (!coverOpening) {
    stash(hook, true);
    stash(tripMeta, true);
  }
  stash(epilogue, false);
  const linkCountBefore = document.querySelectorAll('link[rel=stylesheet]').length;
  const patchCountBefore = document.querySelectorAll('style[data-longshot-live-patch]').length;
  const out = await window.TravelogueLongshot.captureMainToBlob({
    scale: 1,
    format: 'png',
    quietProgress: true,
  });
  const coverEl = document.querySelector('.cover-opening');
  const rect = coverEl ? coverEl.getBoundingClientRect() : null;
  return {
    blobBytes: out.blob.size,
    style: coverEl ? coverEl.getAttribute('data-cover-opening') : null,
    height: rect ? rect.height : 0,
    width: rect ? rect.width : 0,
    linkCountBefore,
    linkCountAfter: document.querySelectorAll('link[rel=stylesheet]').length,
    patchCountBefore,
    patchCountAfter: document.querySelectorAll('style[data-longshot-live-patch]').length,
  };
}"""


def _copy_journal_css(trip_dir: Path) -> None:
    shutil.copy2(_TEMPLATE_JOURNAL, trip_dir / "journal.css")


def _cover_opening_html(
    *,
    layout: str = "web",
    style: str = "card-br",
    title: str = "东澳岛",
    hook: str = "海风吹干盐粒的那刻，我们坐在礁石上。",
    include_hook: bool = True,
) -> str:
    title_layout = resolve_split_mat_title_layout(title)
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
        '<div class="trip-meta" data-block="trip-meta">'
        '<time datetime="2025-06-01/2025-06-03">'
        '<span class="trip-meta__line trip-meta__line--full">2025.06.01 – 06.03 · 东澳岛</span>'
        "</time></div>"
        f'<h1 class="cover-opening__title cover-opening__title--{title_layout}">{title}</h1>'
        f"{hook_html}"
        "</div></section>"
        "</main>"
        '<button id="screenplay-start" type="button" hidden></button>'
        "</body></html>"
    )


def _seed_cover_style_trip(
    trips_dir: Path,
    trip_id: str,
    *,
    style: str,
    layout: str = "web",
    title: str = "东澳岛",
    hook: str = _LONG_HOOK,
    include_hook: bool = True,
) -> str:
    trip_dir = trips_dir / trip_id
    trip_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "tripId": trip_id,
        "meta": {"title": title, "coverOpeningStyle": style},
        "chapters": [{"id": "ch1", "title": "第一章", "items": []}],
        "assets": [],
    }
    (trip_dir / "trip.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    _copy_journal_css(trip_dir)
    html = inject_studio_chrome(
        _cover_opening_html(
            layout=layout,
            style=style,
            title=title,
            hook=hook,
            include_hook=include_hook,
        )
    )
    (trip_dir / "index.html").write_text(html, encoding="utf-8")
    return trip_id


def _seed_rendered_cover_style_trip(
    trips_dir: Path,
    trip_id: str,
    *,
    style: str,
) -> str:
    """Golden fixture + render_trip for Studio rerender E2E."""
    trip_dir = trips_dir / trip_id
    trip_dir.mkdir(parents=True, exist_ok=True)
    trip = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    trip["tripId"] = trip_id
    trip.setdefault("meta", {})["coverOpeningStyle"] = style
    shutil.copytree(TEMPLATE_VISUAL_JOURNAL / "assets", trip_dir / "assets")
    (trip_dir / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (trip_dir / "assets" / "demo" / "video.mp4").write_bytes(b"")
    (trip_dir / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    render_trip(trip_dir / "trip.json", validate=False, layout_engine="screens")
    return trip_id


def _read_cover_opening_style(page) -> str:
    return page.evaluate(
        """() => document.querySelector('.cover-opening')?.getAttribute('data-cover-opening') || ''"""
    )


def _playwright_cover_page(tmp_path: Path, trip_id: str, *, viewport: dict, query: str = ""):
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    from tests.integration.studio.test_studio_server import _free_port, _start_studio_server
    from travelogue.web.studio_jobs import reset_job_store

    reset_job_store()
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir(exist_ok=True)
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"
    url = f"{base}/{trip_id}/index.html{query}"

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
    if "share=1" not in query:
        ctx.page.locator(".preview-toolbar__dock").wait_for(state="visible", timeout=15_000)
    ctx.page.locator(".cover-opening").wait_for(state="visible", timeout=5_000)
    return ctx


@pytest.fixture
def cover_styles_workspace(tmp_path: Path) -> Path:
    trip = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    ws = tmp_path / "cover-styles-v5"
    ws.mkdir()
    shutil.copytree(TEMPLATE_VISUAL_JOURNAL / "assets", ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    trip.setdefault("meta", {})["coverOpeningStyle"] = "magazine-head"
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws


def test_assign_cover_opening_style_deterministic() -> None:
    a = assign_cover_opening_style("linzhi")
    b = assign_cover_opening_style("linzhi")
    assert a == b
    assert a in COVER_OPENING_STYLES


@pytest.mark.parametrize(
    "trip_id,expected",
    [
        ("cover-v5-a", assign_cover_opening_style("cover-v5-a")),
        ("cover-v5-b", assign_cover_opening_style("cover-v5-b")),
        ("cover-v5-c", assign_cover_opening_style("cover-v5-c")),
    ],
)
def test_assign_cover_opening_style_samples(trip_id: str, expected: str) -> None:
    assert assign_cover_opening_style(trip_id) == expected


def test_assign_distribution_covers_all_styles() -> None:
    counts = {style: 0 for style in COVER_OPENING_STYLES}
    for i in range(1000):
        style = assign_cover_opening_style(f"trip-{i}")
        counts[style] += 1
    for style in COVER_OPENING_STYLES:
        assert counts[style] > 200


def test_resolve_cover_opening_style_defaults() -> None:
    assert resolve_cover_opening_style({}) == "card-br"
    assert resolve_cover_opening_style({"meta": {}}) == "card-br"
    assert resolve_cover_opening_style({"meta": {"coverOpeningStyle": "nope"}}) == "card-br"


def test_resolve_cover_opening_style_reads_meta() -> None:
    trip = {"meta": {"coverOpeningStyle": "magazine-head"}}
    assert resolve_cover_opening_style(trip) == "magazine-head"


def test_create_trip_writes_cover_opening_style(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_json = create_trip("csv-v5-new", trips_dir, title="林芝", place="林芝")
    data = json.loads(trip_json.read_text(encoding="utf-8"))
    style = data["meta"]["coverOpeningStyle"]
    assert style in COVER_OPENING_STYLES
    assert style == assign_cover_opening_style("csv-v5-new")


def test_create_trip_records_cover_opening_style_assigned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """G-CSV-09 · 创建时 telemetry 一次。"""
    calls: list[tuple[str, dict | None]] = []

    def _fake_append(event: str, meta: dict | None = None) -> Path:
        calls.append((event, meta))
        return tmp_path / "events.jsonl"

    monkeypatch.setattr(
        "travelogue.services.studio_homepage_telemetry.append_studio_homepage_event",
        _fake_append,
    )
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    create_trip("telemetry-cover", trips_dir)
    assigned = [c for c in calls if c[0] == "cover_opening_style_assigned"]
    assert len(assigned) == 1
    meta = assigned[0][1] or {}
    assert meta.get("tripId") == "telemetry-cover"
    assert meta.get("coverOpeningStyle") in COVER_OPENING_STYLES


def test_cover_opening_style_events_allowlisted() -> None:
    from travelogue.web.studio_homepage_telemetry import ALLOWED_STUDIO_HOMEPAGE_EVENTS

    analytics = (ROOT / "templates" / "studio" / "js" / "analytics.js").read_text(encoding="utf-8")
    for event in (
        "cover_opening_style_assigned",
        "cover_opening_style_render",
        "cover_opening_style_change",
        "cover_opening_style_selector_impression",
    ):
        assert event in ALLOWED_STUDIO_HOMEPAGE_EVENTS
        assert f'"{event}"' in analytics


def test_build_render_context_injects_cover_opening_style() -> None:
    trip = load_golden_trip()
    trip.setdefault("meta", {})["coverOpeningStyle"] = "split-mat"
    trip["meta"]["title"] = "斯里兰卡风光精选"
    ctx = build_render_context(trip, export_mode="draft")
    assert ctx["coverOpeningStyle"] == "split-mat"
    assert ctx["coverTitleLayout"] == "vertical"


def test_build_render_context_long_title_layout_horizontal() -> None:
    trip = load_golden_trip()
    trip.setdefault("meta", {})["coverOpeningStyle"] = "split-mat"
    trip["meta"]["title"] = _LONG_TITLE
    ctx = build_render_context(trip, export_mode="draft")
    assert ctx["coverTitleLayout"] == "horizontal"


def test_build_render_context_legacy_trip_defaults_card_br() -> None:
    trip = load_golden_trip()
    trip.get("meta", {}).pop("coverOpeningStyle", None)
    ctx = build_render_context(trip, export_mode="draft")
    assert ctx["coverOpeningStyle"] == "card-br"


def test_render_html_emits_data_cover_opening(cover_styles_workspace: Path) -> None:
    render_trip(cover_styles_workspace / "trip.json", validate=False, layout_engine="screens")
    html = (cover_styles_workspace / "index.html").read_text(encoding="utf-8")
    assert 'data-cover-opening="magazine-head"' in html


def test_render_illegal_cover_opening_style_falls_back_card_br(cover_styles_workspace: Path) -> None:
    """AC-CSV-05 · 非法枚举 render 回退 card-br。"""
    trip_path = cover_styles_workspace / "trip.json"
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    trip.setdefault("meta", {})["coverOpeningStyle"] = "nope"
    trip_path.write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    render_trip(trip_path, validate=False, layout_engine="screens")
    html = (cover_styles_workspace / "index.html").read_text(encoding="utf-8")
    assert 'data-cover-opening="card-br"' in html
    assert 'data-cover-opening="nope"' not in html


def test_render_twice_preserves_cover_opening_style(cover_styles_workspace: Path) -> None:
    """AC-CSV-03 · render ×2 + rerender_draft_trip 后 data-cover-opening 不变。"""
    trip_path = cover_styles_workspace / "trip.json"
    render_trip(trip_path, validate=False, layout_engine="screens")
    html1 = (cover_styles_workspace / "index.html").read_text(encoding="utf-8")
    render_trip(trip_path, validate=False, layout_engine="screens")
    html2 = (cover_styles_workspace / "index.html").read_text(encoding="utf-8")
    from travelogue.web.rerender import rerender_draft_trip

    rerender_draft_trip(trip_path)
    html3 = (cover_styles_workspace / "index.html").read_text(encoding="utf-8")
    for html in (html1, html2, html3):
        assert 'data-cover-opening="magazine-head"' in html


@pytest.mark.parametrize("cover_style", ["card-br", "magazine-head", "split-mat"])
@pytest.mark.playwright_serial
def test_cover_styles_v5_longshot_cover_smoke(cover_styles_workspace: Path, cover_style: str) -> None:
    """AC-CSV-44 · longshot 含封面块、首屏可见且首章 PNG 捕获成功。"""
    trip_path = cover_styles_workspace / "trip.json"
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    trip.setdefault("meta", {})["coverOpeningStyle"] = cover_style
    trip_path.write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    render_trip(trip_path, validate=False, layout_engine="screens")
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    from travelogue.render.engine import write_longshot_sidecar

    write_longshot_sidecar(trip, cover_styles_workspace, export_mode="draft", trip_root=cover_styles_workspace)
    longshot_html = cover_styles_workspace / "index-longshot.html"
    assert longshot_html.is_file()
    assert f'data-cover-opening="{cover_style}"' in longshot_html.read_text(encoding="utf-8")
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    from travelogue.web.longshot_smoke import _start_static_server

    server = _start_static_server(cover_styles_workspace, "127.0.0.1", 0)
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/index-longshot.html"
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 428, "height": 844})
            page.goto(url, wait_until="networkidle")
            page.wait_for_function(
                "() => window.TravelogueLongshot && document.documentElement.dataset.longshot === 'on'",
                timeout=30_000,
            )
            metrics = page.evaluate(_LONGSHOT_CAPTURE_METRICS_JS)
            browser.close()
    finally:
        server.shutdown()
        server.server_close()

    assert metrics is not None
    assert metrics["blobBytes"] > 1024
    assert metrics["style"] == cover_style
    assert metrics["height"] >= 120
    assert metrics["width"] >= 120
    assert metrics["linkCountAfter"] == metrics["linkCountBefore"]
    assert metrics["patchCountAfter"] == metrics["patchCountBefore"]


_SPLIT_MAT_LONGSHOT_TITLE_CAPTURE_JS = """async () => {
  const title = document.querySelector('.cover-opening__title');
  if (!title) return null;
  document.body.classList.add('longshot-capturing');
  document.documentElement.classList.add('longshot-capturing-root');
  document.documentElement.setAttribute('data-layout', 'mobile');
  await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  const cs = getComputedStyle(title);
  const out = {
    writingMode: cs.writingMode,
    textAlign: cs.textAlign,
    fontSize: cs.fontSize,
    titleClass: title.className,
  };
  document.body.classList.remove('longshot-capturing');
  document.documentElement.classList.remove('longshot-capturing-root');
  return out;
}"""


@pytest.mark.e2e
@pytest.mark.playwright_serial
def test_cover_styles_v5_split_mat_longshot_title_horizontal(tmp_path: Path) -> None:
    """split-mat 短书名：长图截图态横排 + 居中。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = "cover-split-mat-longshot-title"
    trip_dir = trips_dir / trip_id
    trip_dir.mkdir(parents=True)
    trip = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    trip["tripId"] = trip_id
    trip.setdefault("meta", {})["coverOpeningStyle"] = "split-mat"
    trip["meta"]["title"] = "斯里兰卡风光精选"
    shutil.copytree(TEMPLATE_VISUAL_JOURNAL / "assets", trip_dir / "assets")
    (trip_dir / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (trip_dir / "assets" / "demo" / "video.mp4").write_bytes(b"")
    (trip_dir / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    render_trip(trip_dir / "trip.json", validate=False, layout_engine="screens")
    from travelogue.render.engine import write_longshot_sidecar

    trip = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
    write_longshot_sidecar(trip, trip_dir, export_mode="draft", trip_root=trip_dir)
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    from travelogue.web.longshot_smoke import _start_static_server

    server = _start_static_server(trip_dir, "127.0.0.1", 0)
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/index-longshot.html"
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 428, "height": 844})
            page.goto(url, wait_until="networkidle")
            metrics = page.evaluate(_SPLIT_MAT_LONGSHOT_TITLE_CAPTURE_JS)
            browser.close()
    finally:
        server.shutdown()
        server.server_close()

    assert metrics is not None
    assert "cover-opening__title--vertical" in metrics["titleClass"]
    assert metrics["writingMode"] in ("horizontal-tb", "lr-tb")
    assert metrics["textAlign"] == "center"
    assert float(metrics["fontSize"].replace("px", "")) >= 24


def test_resolve_split_mat_title_layout_tiers() -> None:
    assert resolve_split_mat_title_layout("斯里兰卡风光精选") == "vertical"
    assert resolve_split_mat_title_layout("东澳岛") == "vertical"
    assert resolve_split_mat_title_layout("二〇二五年东澳岛夏日纪行") == "vertical-compact"
    assert resolve_split_mat_title_layout(_LONG_TITLE) == "horizontal"


def test_cover_styles_v5_journal_css_tokens() -> None:
    """§4.6 token + split-mat / magazine-head selectors present."""
    css = JOURNAL_CSS.read_text(encoding="utf-8")
    for token in (
        "--cover-mat-ground",
        "--cover-mat-panel-bg",
        "--cover-mat-accent",
        "--cover-mag-header-bg",
        'data-cover-opening="split-mat"',
        'data-cover-opening="magazine-head"',
        "min-width: 64rem",
        "grid-template-columns: 1.45fr 0.5fr",
        "cover-opening__title--vertical",
        "#f2efe7",
        "min-height: 20vh",
        "max-height: 32vh",
        "flex: 1 1 0",
        "text-align: center",
    ):
        assert token in css, f"missing cover v5 token: {token}"


@pytest.mark.e2e
@pytest.mark.playwright_serial
@pytest.mark.parametrize("style", ["split-mat", "magazine-head"])
def test_cover_styles_v5_wide_viewport_no_overflow(tmp_path: Path, style: str) -> None:
    """AC-CSV-20/22/30/32 · 三款宽屏一屏无溢出。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = _seed_cover_style_trip(
        trips_dir,
        f"cover-{style}-wide",
        style=style,
        title=_LONG_TITLE,
        hook=_LONG_HOOK,
    )
    ctx = _playwright_cover_page(tmp_path, trip_id, viewport={"width": 1280, "height": 800})
    try:
        m = ctx.page.evaluate(_COVER_METRICS_JS)
        assert m is not None
        assert m["style"] == style
        assert abs(m["coverHeight"] - m["viewportH"]) <= 2, m
        assert m["coverOverflow"] is False, m
    finally:
        ctx.close()


@pytest.mark.e2e
@pytest.mark.playwright_serial
def test_cover_styles_v5_split_mat_vertical_title(tmp_path: Path) -> None:
    """split-mat 短书名竖排 + 窄侧栏。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = _seed_cover_style_trip(
        trips_dir,
        "cover-split-mat-vertical",
        style="split-mat",
        title="斯里兰卡风光精选",
    )
    ctx = _playwright_cover_page(tmp_path, trip_id, viewport={"width": 1280, "height": 800})
    try:
        metrics = ctx.page.evaluate("""() => {
          const cover = document.querySelector('.cover-opening');
          const panel = document.querySelector('.cover-opening__panel');
          const title = document.querySelector('.cover-opening__title');
          if (!cover || !panel || !title) return null;
          const csCover = getComputedStyle(cover);
          const csTitle = getComputedStyle(title);
          const coverRect = cover.getBoundingClientRect();
          const panelRect = panel.getBoundingClientRect();
          return {
            gridCols: csCover.gridTemplateColumns,
            writingMode: csTitle.writingMode,
            titleClass: title.className,
            panelWidth: panelRect.width,
            coverWidth: coverRect.width,
            panelShare: panelRect.width / coverRect.width,
          };
        }""")
        assert metrics is not None
        # getComputedStyle resolves fr → px; narrow sidebar ratio is the stable check.
        cols = [c.strip() for c in metrics["gridCols"].split() if c.strip()]
        assert len(cols) == 2, metrics
        assert metrics["panelShare"] < 0.28, metrics
        assert metrics["writingMode"] in ("vertical-rl", "sideways-rl")
        assert "cover-opening__title--vertical" in metrics["titleClass"]
    finally:
        ctx.close()


@pytest.mark.e2e
@pytest.mark.playwright_serial
def test_cover_styles_v5_split_mat_layout(tmp_path: Path) -> None:
    """AC-CSV-21 · 分屏画框 + 摄影/文案区同时可见。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = _seed_cover_style_trip(trips_dir, "cover-split-mat", style="split-mat")
    ctx = _playwright_cover_page(tmp_path, trip_id, viewport={"width": 1280, "height": 800})
    try:
        m = ctx.page.evaluate(_COVER_METRICS_JS)
        assert m["coverDisplay"] == "grid", m
        assert m["heroPosition"] == "relative", m
        assert m["panelPosition"] == "relative", m
        assert m["sideBySide"] is True, m
        assert m["panelContrast"] is not None and m["panelContrast"] >= 4.5, m
        assert m["dockVisible"] is True, m
    finally:
        ctx.close()


@pytest.mark.e2e
@pytest.mark.playwright_serial
def test_cover_styles_v5_magazine_head_layout(tmp_path: Path) -> None:
    """AC-CSV-31/36 · 上文下图 + 摄影区 ≥58vh + 标题居中。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = _seed_cover_style_trip(trips_dir, "cover-magazine", style="magazine-head")
    ctx = _playwright_cover_page(tmp_path, trip_id, viewport={"width": 1280, "height": 800})
    try:
        m = ctx.page.evaluate(_COVER_METRICS_JS)
        assert m["coverDisplay"] == "flex", m
        assert m["panelAboveHero"] is True, m
        assert m["titleTextAlign"] == "center", m
        assert m["heroHeight"] >= m["viewportH"] * 0.58 - 8, m
        assert m["panelHeight"] <= m["viewportH"] * 0.32 + 4, m
        assert m["titleContrast"] is not None and m["titleContrast"] >= 3.0, m
        assert m["dockVisible"] is True, m
    finally:
        ctx.close()


@pytest.mark.e2e
@pytest.mark.playwright_serial
@pytest.mark.parametrize("style", ["split-mat", "magazine-head"])
def test_cover_styles_v5_narrow_viewport_falls_back_card_br(tmp_path: Path, style: str) -> None:
    """AC-CSV-25/35/51 · <1024px CSS 回落 card-br，属性不变。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = _seed_cover_style_trip(trips_dir, f"cover-{style}-narrow", style=style)
    ctx = _playwright_cover_page(tmp_path, trip_id, viewport={"width": 1023, "height": 800})
    try:
        m = ctx.page.evaluate(_COVER_METRICS_JS)
        assert m["style"] == style, m
        assert m["panelPosition"] == "absolute", m
        assert m["coverDisplay"] == "block", m
        assert m["heroPosition"] == "absolute", m
    finally:
        ctx.close()


@pytest.mark.e2e
@pytest.mark.playwright_serial
def test_cover_styles_v5_short_title_panel_padding(tmp_path: Path) -> None:
    """AC-CSV-47 · 短书名不贴边（窄侧栏 panel padding 20px 14px 18px）。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = _seed_cover_style_trip(
        trips_dir,
        "cover-short-title",
        style="split-mat",
        title="林芝",
        hook="",
        include_hook=False,
    )
    ctx = _playwright_cover_page(tmp_path, trip_id, viewport={"width": 1280, "height": 800})
    try:
        m = ctx.page.evaluate(_COVER_METRICS_JS)
        assert m["panelPaddingLeft"] >= 12, m
    finally:
        ctx.close()


@pytest.mark.e2e
@pytest.mark.playwright_serial
def test_cover_styles_v5_empty_hook_no_collapse(tmp_path: Path) -> None:
    """AC-CSV-23/33 · hook 为空时 panel 仍可读。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    for style in ("split-mat", "magazine-head"):
        trip_id = _seed_cover_style_trip(
            trips_dir,
            f"cover-no-hook-{style}",
            style=style,
            title="林芝",
            hook="",
            include_hook=False,
        )
        ctx = _playwright_cover_page(tmp_path, trip_id, viewport={"width": 1280, "height": 800})
        try:
            m = ctx.page.evaluate(_COVER_METRICS_JS)
            assert m["coverOverflow"] is False, m
            if style == "magazine-head":
                assert m["panelHeight"] >= m["viewportH"] * 0.20 - 4, m
        finally:
            ctx.close()


@pytest.mark.e2e
@pytest.mark.playwright_serial
def test_cover_styles_v5_share_keeps_style(tmp_path: Path) -> None:
    """AC-CSV-34 · Share 模式保留 data-cover-opening。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = _seed_cover_style_trip(trips_dir, "cover-share-mag", style="magazine-head")
    ctx = _playwright_cover_page(
        tmp_path, trip_id, viewport={"width": 1280, "height": 800}, query="?share=1"
    )
    try:
        style = ctx.page.evaluate(
            """() => document.querySelector('.cover-opening')?.getAttribute('data-cover-opening')"""
        )
        assert style == "magazine-head"
        assert ctx.page.locator(".preview-toolbar--share-minimal").count() == 1
    finally:
        ctx.close()


@pytest.mark.e2e
@pytest.mark.playwright_serial
def test_cover_styles_v5_first_preview_toast_once(tmp_path: Path) -> None:
    """AC-CSV-46 · 首次预览 Toast 一次；G-CSV-09 · render 事件一次。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = _seed_cover_style_trip(trips_dir, "cover-toast", style="split-mat")
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    from tests.integration.studio.test_studio_server import _free_port, _start_studio_server
    from travelogue.web.studio_jobs import reset_job_store

    reset_job_store()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    url = f"http://127.0.0.1:{port}/{trip_id}/index.html"
    storage_key = f"travelogue.coverStyleToast.{trip_id}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            events = _attach_studio_event_collector(page)
            page.add_init_script(f"() => localStorage.removeItem({json.dumps(storage_key)})")
            page.goto(url, wait_until="networkidle")
            toast = page.locator("#preview-toolbar-toast")
            toast.wait_for(state="visible", timeout=10_000)
            text = toast.inner_text()
            assert "版式已为你选定" in text
            assert "排版" in text
            assert "即将推出" not in text
            render_events = [e for e in events if e.get("event") == "cover_opening_style_render"]
            assert len(render_events) == 1, events
            assert render_events[0].get("meta", {}).get("tripId") == trip_id
            assert render_events[0].get("meta", {}).get("coverOpeningStyle") == "split-mat"
            page.reload(wait_until="networkidle")
            page.wait_for_timeout(400)
            assert toast.is_hidden()
            render_events_after = [e for e in events if e.get("event") == "cover_opening_style_render"]
            assert len(render_events_after) == 1
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
@pytest.mark.playwright_serial
def test_cover_styles_v5_sheet_switch_and_apply_layout(tmp_path: Path) -> None:
    """P1 · Sheet 切换封面版式后立即更新预览 data-cover-opening。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = _seed_rendered_cover_style_trip(trips_dir, "cover-switch", style="split-mat")
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    from tests.integration.studio.test_studio_server import _free_port, _start_studio_server
    from travelogue.web.studio_jobs import reset_job_store

    reset_job_store()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    url = f"http://127.0.0.1:{port}/{trip_id}/index.html"
    storage_key = f"travelogue.coverStyleToast.{trip_id}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            events = _attach_studio_event_collector(page)
            page.add_init_script(f"() => localStorage.setItem({json.dumps(storage_key)}, '1')")
            page.goto(url, wait_until="networkidle")
            page.locator(".preview-toolbar__dock").wait_for(state="visible", timeout=15_000)
            page.wait_for_function(
                """() => {
                  const el = document.getElementById('preview-toolbar-toast');
                  return !el || el.hidden;
                }""",
                timeout=6_000,
            )
            assert _read_cover_opening_style(page) == "split-mat"

            page.locator(".preview-toolbar__menu-btn").click()
            page.wait_for_selector(".preview-sheet", timeout=10_000)
            page.locator('.preview-sheet__tab[data-sheet-tab="layout"]').click()
            page.wait_for_selector(".preview-sheet__cover-styles", timeout=10_000)
            assert page.locator('[data-cover-style="split-mat"].is-on').count() == 1

            with page.expect_response(
                lambda r: r.url.endswith("/save-copy") and r.request.method == "POST",
                timeout=15_000,
            ):
                page.locator('[data-cover-style="magazine-head"]').click()
            page.wait_for_function(
                """() => {
                  const el = document.getElementById('preview-toolbar-toast');
                  return el && !el.hidden && el.textContent.indexOf('封面版式已更新') >= 0;
                }""",
                timeout=10_000,
            )
            change_events = [e for e in events if e.get("event") == "cover_opening_style_change"]
            assert len(change_events) == 1, events
            change_meta = change_events[0].get("meta", {})
            assert change_meta.get("tripId") == trip_id
            assert change_meta.get("coverOpeningStyle") == "magazine-head"
            assert change_meta.get("previousCoverOpeningStyle") == "split-mat"

            assert _read_cover_opening_style(page) == "magazine-head"

            entry = page.evaluate(
                f"""async () => {{
                  const r = await fetch('/__travelogue/trips/{trip_id}/entry');
                  return r.ok ? r.json() : null;
                }}"""
            )
            assert entry and entry.get("coverOpeningStyle") == "magazine-head"

            trip_data = json.loads((trips_dir / trip_id / "trip.json").read_text(encoding="utf-8"))
            assert trip_data["meta"]["coverOpeningStyle"] == "magazine-head"
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
@pytest.mark.playwright_serial
def test_cover_styles_v5_mobile_footnote_visible(tmp_path: Path) -> None:
    """D-CSV-22 · 预览区持久 Mobile 脚注。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = _seed_cover_style_trip(trips_dir, "cover-footnote", style="split-mat")
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    from tests.integration.studio.test_studio_server import _free_port, _start_studio_server
    from travelogue.web.studio_jobs import reset_job_store

    reset_job_store()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    url = f"http://127.0.0.1:{port}/{trip_id}/index.html"
    storage_key = f"travelogue.coverStyleToast.{trip_id}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            _attach_studio_event_collector(page)
            page.add_init_script(f"() => localStorage.setItem({json.dumps(storage_key)}, '1')")
            page.goto(url, wait_until="networkidle")
            footnote = page.locator("#preview-toolbar-cover-footnote")
            footnote.wait_for(state="visible", timeout=10_000)
            assert "手机预览封面版式与电脑不同" in footnote.inner_text()
            assert "以手机效果为准" in footnote.inner_text()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
@pytest.mark.playwright_serial
def test_cover_styles_v5_split_mat_title_edit_keeps_style(tmp_path: Path) -> None:
    """AC-CSV-24 · split-mat 书名编辑后样式不变。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = _seed_rendered_cover_style_trip(trips_dir, "cover-title-edit", style="split-mat")
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    from tests.integration.studio.test_studio_server import _free_port, _start_studio_server
    from travelogue.web.studio_jobs import reset_job_store

    reset_job_store()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    url = f"http://127.0.0.1:{port}/{trip_id}/index.html"
    storage_key = f"travelogue.coverStyleToast.{trip_id}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            _attach_studio_event_collector(page)
            page.add_init_script(f"() => localStorage.setItem({json.dumps(storage_key)}, '1')")
            page.goto(url, wait_until="networkidle")
            page.locator(".cover-opening__title").wait_for(state="visible", timeout=10_000)
            assert _read_cover_opening_style(page) == "split-mat"
            page.locator(".cover-opening__title").click()
            title_input = page.locator(".cover-opening__title-input")
            title_input.wait_for(state="visible", timeout=5_000)
            title_input.fill("雨后京都")
            title_input.press("Enter")
            page.wait_for_load_state("networkidle", timeout=30_000)
            page.locator(".cover-opening").wait_for(state="visible", timeout=10_000)
            assert _read_cover_opening_style(page) == "split-mat"
            assert "雨后京都" in (page.locator(".cover-opening__title").inner_text() or "")
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
