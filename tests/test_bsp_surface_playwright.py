"""BSP Book Surface · Playwright AC-BSP-01/02/02a/02b/02c (PRD-页面优化 §7)."""

from __future__ import annotations

import json
from functools import partial
from pathlib import Path

import pytest

from tests.test_studio_server import _free_port
from travelogue.paths import ROOT
from travelogue.render.engine import render_trip
from travelogue.web.serve import TripPreviewHandler

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]

DEMO_TRIP_ID = "demo-d66fe642a9"
LINZHI_TRIP_ID = "linzhi"
VIEWPORT_P0 = {"width": 1440, "height": 960}
DPR_P0 = 2
VIEWPORT_P1 = {"width": 2560, "height": 1440}
VIEWPORT_T3 = {"width": 1920, "height": 1080}
# Studio preview-toolbar 占用 innerHeight；略低于 CSS 0.62×dvh 属预期
VH_P0_MIN = 0.615
VH_P1_MIN = 0.575

_MEASURE_JS = """
(idx) => {
  const screen = document.querySelector(
    `.layout-screen[data-screen-index="${idx}"], .breath-pause-screen[data-screen-index="${idx}"]`
  );
  if (!screen) return null;
  const img = screen.querySelector('img.layout-slot__img');
  const slot = screen.querySelector('.layout-slot');
  const rect = screen.getBoundingClientRect();
  const vh = window.innerHeight || 1;
  const out = { width: rect.width, block: screen.getAttribute('data-block') };
  if (img && slot) {
    const ir = img.getBoundingClientRect();
    const sr = slot.getBoundingClientRect();
    out.imgHeightVh = ir.height / vh;
    out.fillRatio = sr.width > 0 ? ir.width / sr.width : 0;
    out.pattern = screen.getAttribute('data-pattern');
    out.viewportFit = screen.classList.contains('layout-screen--viewport-fit');
  }
  return out;
}
"""

_RAIL_WIDTHS_JS = """
() => {
  const chapter = document.querySelector('section.chapter');
  if (!chapter) return [];
  const nodes = chapter.querySelectorAll(
    '.layout-screen[data-block="layout-screen"], .breath-pause-screen[data-block="breath-pause-screen"]'
  );
  return Array.from(nodes).map((el) => ({
    index: el.getAttribute('data-screen-index'),
    block: el.getAttribute('data-block'),
    width: el.getBoundingClientRect().width,
    viewportFit: el.classList.contains('layout-screen--viewport-fit'),
  }));
}
"""

_ASSET_SCREEN_JS = """
(assetId) => {
  const screen = document.querySelector(
    `.layout-screen[data-asset-ids="${assetId}"], .layout-screen[data-asset-ids*="${assetId}"]`
  );
  if (!screen) return null;
  const img = screen.querySelector('img.layout-slot__img');
  const slot = screen.querySelector('.layout-slot');
  if (!img || !slot) return null;
  const vh = window.innerHeight || 1;
  const ir = img.getBoundingClientRect();
  const sr = slot.getBoundingClientRect();
  return {
    imgHeightVh: ir.height / vh,
    fillRatio: sr.width > 0 ? ir.width / sr.width : 0,
    tierUltra: screen.classList.contains('layout-screen--tier-ultra'),
    viewportFit: screen.classList.contains('layout-screen--viewport-fit'),
    screenHeightVh: screen.getBoundingClientRect().height / vh,
  };
}
"""


def _start_trips_server(trips_dir: Path, port: int):
    handler = partial(
        TripPreviewHandler,
        directory=str(trips_dir),
        trip_json=trips_dir / ".placeholder" / "trip.json",
        studio_mode=True,
        trips_dir=trips_dir,
        studio_host="127.0.0.1",
        studio_port=port,
        studio_allow_lan=False,
    )
    from http.server import ThreadingHTTPServer
    import threading

    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


@pytest.fixture(scope="module")
def bsp_trips_ready() -> dict[str, Path]:
    """Re-render dogfood trips so BSP CSS/context land in trip HTML copies."""
    trips_dir = ROOT / "trips"
    out: dict[str, Path] = {}
    for trip_id in (DEMO_TRIP_ID, LINZHI_TRIP_ID):
        trip_path = trips_dir / trip_id / "trip.json"
        if not trip_path.is_file():
            pytest.skip(f"missing trip: {trip_id}")
        render_trip(trip_path, validate=False)
        html = (trips_dir / trip_id / "index.html").read_text(encoding="utf-8")
        if trip_id == DEMO_TRIP_ID and "layout-screen--viewport-fit" not in html:
            pytest.fail("demo render missing layout-screen--viewport-fit")
        out[trip_id] = trip_path.parent
    return out


@pytest.fixture(scope="module")
def bsp_server(bsp_trips_ready):
    port = _free_port()
    trips_dir = ROOT / "trips"
    server = _start_trips_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"
    try:
        yield {"base": base}
    finally:
        server.shutdown()
        server.server_close()


def _open_demo(page, base: str) -> None:
    page.goto(f"{base}/{DEMO_TRIP_ID}/index.html", wait_until="networkidle")


def _viewport_fit_full_frame_indices(page) -> list[int]:
    indices = page.evaluate(
        """() => Array.from(
            document.querySelectorAll(
              '.layout-screen[data-pattern="screen-full-frame"].layout-screen--viewport-fit'
            )
          )
          .map((el) => parseInt(el.getAttribute('data-screen-index') || '0', 10))
          .filter((n) => n > 0)"""
    )
    return sorted(indices)


@pytest.mark.e2e
def test_ac_bsp_01_content_rail_same_width(bsp_server) -> None:
    """AC-BSP-01 · breath-pause 与满 rail 的 layout-screen 同宽（±1px）。

    viewport-fit 屏在 vh 触顶时可收窄宽度以保持原生比例，不参与同宽断言。
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT_P0, device_scale_factor=DPR_P0)
        _open_demo(page, bsp_server["base"])
        rows = page.evaluate(_RAIL_WIDTHS_JS)
        assert len(rows) >= 10, f"expected chapter blocks, got {len(rows)}"
        rail_rows = [
            r
            for r in rows
            if r["block"] == "breath-pause-screen" or not r.get("viewportFit")
        ]
        assert len(rail_rows) >= 4, rail_rows
        ref = rail_rows[0]["width"]
        for row in rail_rows:
            assert abs(row["width"] - ref) <= 1.0, row
        browser.close()


@pytest.mark.e2e
def test_ac_bsp_01_breath_pause_s3_indices(bsp_server) -> None:
    """S3 · breath-pause index 5/10 与 content-rail 满宽块同宽。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT_P0, device_scale_factor=DPR_P0)
        _open_demo(page, bsp_server["base"])
        rows = page.evaluate(_RAIL_WIDTHS_JS)
        rail_w = max(
            r["width"]
            for r in rows
            if r["block"] == "breath-pause-screen" or not r.get("viewportFit")
        )
        for idx in (5, 10):
            breath = page.evaluate(_MEASURE_JS, idx)
            assert breath and breath["block"] == "breath-pause-screen", idx
            assert abs(breath["width"] - rail_w) <= 1.0, (idx, breath, rail_w)
        browser.close()


@pytest.mark.e2e
def test_ac_bsp_02_p0_full_frame_height_and_fill(bsp_server) -> None:
    """AC-BSP-02 · P0 1440×960@2x full-frame ≥62vh · 无信箱。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT_P0, device_scale_factor=DPR_P0)
        _open_demo(page, bsp_server["base"])
        indices = _viewport_fit_full_frame_indices(page)
        assert len(indices) >= 4, "expected viewport-fit full-frame screens"
        sample = indices[:4]
        for idx in sample:
            m = page.evaluate(_MEASURE_JS, idx)
            assert m and m.get("pattern") == "screen-full-frame", idx
            assert m.get("viewportFit") is True, idx
            assert m["imgHeightVh"] >= VH_P0_MIN, (idx, m)
            assert m["fillRatio"] >= 0.98, (idx, m)
        browser.close()


@pytest.mark.e2e
def test_ac_bsp_02a_p1_full_frame_height_and_fill(bsp_server) -> None:
    """AC-BSP-02a · P1 2560×1440 full-frame ≥58vh · 无信箱。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT_P1)
        _open_demo(page, bsp_server["base"])
        indices = _viewport_fit_full_frame_indices(page)
        assert len(indices) >= 4
        sample = indices[:4]
        for idx in sample:
            m = page.evaluate(_MEASURE_JS, idx)
            assert m and m.get("pattern") == "screen-full-frame", idx
            assert m["imgHeightVh"] >= VH_P1_MIN, (idx, m)
            assert m["fillRatio"] >= 0.98, (idx, m)
        browser.close()


@pytest.mark.e2e
def test_ac_bsp_02b_p0_not_thinner_than_p1(bsp_server) -> None:
    """AC-BSP-02b · 同屏 P0 画面重量 ≥ P1。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        indices: list[int] = []
        p0_heights: dict[int, float] = {}
        p1_heights: dict[int, float] = {}
        page0 = browser.new_page(viewport=VIEWPORT_P0, device_scale_factor=DPR_P0)
        _open_demo(page0, bsp_server["base"])
        indices = _viewport_fit_full_frame_indices(page0)
        assert len(indices) >= 4
        sample = indices[:4]
        for idx in sample:
            m = page0.evaluate(_MEASURE_JS, idx)
            assert m and m.get("imgHeightVh") is not None
            p0_heights[idx] = m["imgHeightVh"]
        page0.close()
        page1 = browser.new_page(viewport=VIEWPORT_P1)
        _open_demo(page1, bsp_server["base"])
        for idx in sample:
            m = page1.evaluate(_MEASURE_JS, idx)
            assert m and m.get("imgHeightVh") is not None
            p1_heights[idx] = m["imgHeightVh"]
        page1.close()
        browser.close()
        for idx in sample:
            assert p0_heights[idx] >= p1_heights[idx] - 0.01, (idx, p0_heights[idx], p1_heights[idx])


@pytest.mark.e2e
def test_ac_bsp_02c_linzhi_ultra_wide_vh_anchor(bsp_server) -> None:
    """AC-BSP-02c · 林芝 asset-026 · 1920×1080 ≥52vh。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT_T3)
        page.goto(f"{bsp_server['base']}/{LINZHI_TRIP_ID}/index.html", wait_until="networkidle")
        m = page.evaluate(_ASSET_SCREEN_JS, "asset-026")
        assert m is not None, "asset-026 screen not found"
        assert m.get("tierUltra") is True or m.get("viewportFit") is True, m
        assert m["imgHeightVh"] >= 0.52, m
        browser.close()


@pytest.mark.e2e
def test_ac_bsp_s1_plate_asset_006_p0(bsp_server) -> None:
    """§7.3 S1 · Plate screen-index=1 · asset-006 · P0 重量。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT_P0, device_scale_factor=DPR_P0)
        _open_demo(page, bsp_server["base"])
        m = page.evaluate(_MEASURE_JS, 1)
        assert m and m.get("block") == "layout-screen", m
        assert m["fillRatio"] >= 0.98, m
        assert m["imgHeightVh"] >= VH_P0_MIN, m
        browser.close()


@pytest.mark.e2e
def test_ac_bsp_03_reduced_motion_no_scrub_transform(bsp_server) -> None:
    """AC-BSP-03 · prefers-reduced-motion 下 breath-image 无 transform。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT_P0, device_scale_factor=DPR_P0)
        page.emulate_media(reduced_motion="reduce")
        _open_demo(page, bsp_server["base"])
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3)")
        page.wait_for_timeout(800)
        transforms = page.evaluate(
            """() => Array.from(document.querySelectorAll('.layout-slot__img'))
              .map((img) => img.style.transform || '')"""
        )
        assert transforms, "expected layout images"
        assert all(not t.strip() for t in transforms), transforms[:5]
        browser.close()


@pytest.mark.e2e
def test_ac_bsp_04_reader_hides_plate_meta(bsp_server) -> None:
    """AC-BSP-04 · reader_immersive 隐藏 folio-plate-meta。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT_P0, device_scale_factor=DPR_P0)
        _open_demo(page, bsp_server["base"])
        visible_studio = page.locator(".folio-plate-meta").first.is_visible()
        assert visible_studio is True
        page.evaluate(
            """() => {
              document.documentElement.setAttribute('data-reading-profile', 'reader_immersive');
              document.documentElement.setAttribute('data-surface-mode', 'reader');
              document.documentElement.removeAttribute('data-folio');
            }"""
        )
        assert page.locator(".folio-plate-meta").first.is_hidden()
        browser.close()


@pytest.mark.e2e
def test_linzhi_ultra_wide_sequence_026_028(bsp_server) -> None:
    """§7.3 林芝 · asset-026→028 连续 ultra-wide ≥52vh。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT_T3)
        page.goto(f"{bsp_server['base']}/{LINZHI_TRIP_ID}/index.html", wait_until="networkidle")
        for aid in ("asset-026", "asset-027", "asset-028"):
            m = page.evaluate(_ASSET_SCREEN_JS, aid)
            assert m is not None, aid
            assert m["imgHeightVh"] >= 0.52, (aid, m)
        browser.close()


@pytest.mark.unit
def test_bsp_surface_report_template_exists() -> None:
    """R-BSP-P3-04 · surface 截图报告模板占位。"""
    path = ROOT / "docs" / "templates" / "bsp-surface-report.json"
    assert path.is_file(), "add docs/templates/bsp-surface-report.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert DEMO_TRIP_ID in data.get("trips", {})
    assert "S1" in data["trips"][DEMO_TRIP_ID].get("shots", {})
