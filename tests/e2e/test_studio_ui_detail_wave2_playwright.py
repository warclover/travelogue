"""Studio UI Detail · wave2 runtime audit: Settings + Preview sheet.

Writes JSON + screenshots under
docs/acceptance-records/attachments/ui-detail-wave2-settings-sheet/.
Fails on P0/P1 (static + runtime); P2 reported only.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.studio_ui_detail_static_audit import run_audit as run_static_audit
from tests.e2e.test_studio_home_v2_ac_playwright import _goto_v2
from tests.e2e.ui_detail_runtime_helpers import (
    assert_no_blocking_findings,
    findings_from_panel_metrics,
)
from tests.integration.studio.test_studio_server import _free_port, _start_studio_server
from tests.preview_arc14_fixtures import demo_assets_available, seed_arc14_preview_trip
from travelogue.paths import ROOT
from travelogue.web.studio_jobs import reset_job_store

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]

OUT_DIR = (
    ROOT
    / "docs"
    / "acceptance-records"
    / "attachments"
    / "ui-detail-wave2-settings-sheet"
)
VIEWPORT = {"width": 1280, "height": 900}

_MEASURE_PANEL_JS = """
(rootSel) => {
  const root = document.querySelector(rootSel);
  if (!root) return { error: 'missing ' + rootSel };
  const walk = [];
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT);
  let n;
  const iconOnly = (el, text) => {
    const cls = String(el.className || '');
    if (text.length <= 2 && /[×x✕✖]/.test(text)) return true;
    if (/(^|\\s|__)(close|dismiss|back)(\\s|$|--)/i.test(cls) && text.length <= 2) return true;
    return false;
  };
  const isVisible = (el) => {
    let cur = el;
    while (cur && cur.nodeType === 1) {
      if (cur.hidden) return false;
      const s = getComputedStyle(cur);
      if (s.display === 'none' || s.visibility === 'hidden') return false;
      if (cur === root) break;
      cur = cur.parentElement;
    }
    return true;
  };
  while ((n = walker.nextNode())) {
    if (!isVisible(n)) continue;
    const s = getComputedStyle(n);
    const text = (n.childNodes.length === 1 && n.childNodes[0].nodeType === 3)
      ? (n.textContent || '').trim()
      : '';
    if (!text) continue;
    if (iconOnly(n, text)) continue;
    walk.push({
      tag: n.tagName.toLowerCase(),
      className: String(n.className || '').slice(0, 96),
      text: text.slice(0, 48),
      fontSize: parseFloat(s.fontSize),
      color: s.color,
      fontWeight: s.fontWeight,
      left: n.getBoundingClientRect().left,
    });
  }
  const fonts = [...new Set(walk.map((x) => x.fontSize.toFixed(1)))].sort(
    (a, b) => parseFloat(a) - parseFloat(b)
  );
  const colors = [...new Set(walk.map((x) => x.color))];
  let leftDelta = null;
  if (walk.length >= 2) leftDelta = Math.abs(walk[0].left - walk[1].left);
  return {
    surface: rootSel,
    textSampleCount: walk.length,
    uniqueFontSizes: fonts,
    uniqueColors: colors,
    fontSizeCount: fonts.length,
    colorCount: colors.length,
    leftDeltaFirstTwo: leftDelta,
    samples: walk.slice(0, 36),
  };
}
"""


def _findings_from_panel(
    metrics: dict, *, surface: str, font_cap: int = 5, color_cap: int = 4
) -> list[dict]:
    out = findings_from_panel_metrics(
        metrics, surface=surface, font_cap=font_cap, color_cap=color_cap
    )
    if metrics.get("leftDeltaFirstTwo") is not None and metrics["leftDeltaFirstTwo"] > 24:
        out.append(
            {
                "id": "D-UID-05",
                "severity": "P2",
                "surface": surface,
                "detail": f"前两行左缘差 {metrics['leftDeltaFirstTwo']:.1f}px",
            }
        )
    return out


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


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


def test_studio_ui_detail_wave2_settings_sheet_audit(studio_server) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    static_report = run_static_audit(wave="settings-sheet")
    (OUT_DIR / "static-audit.json").write_text(
        json.dumps(static_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    runtime: dict = {"surfaces": {}, "findings": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT)

        # ── S-SET · homepage settings popover ──
        _goto_v2(page, studio_server["base"])
        page.locator("#v2-settings-toggle").click()
        page.wait_for_function(
            "() => { const pop = document.getElementById('v2-settings-popover'); return pop && !pop.hidden; }"
        )
        # expand common zones for denser typography sample
        page.evaluate(
            """
            () => {
              for (const id of [
                'v2-settings-zone-import',
                'v2-settings-zone-ai',
                'v2-settings-zone-appearance',
                'v2-settings-storage-section',
              ]) {
                const z = document.getElementById(id);
                if (z) z.open = true;
              }
            }
            """
        )
        page.wait_for_timeout(120)
        s_set = page.evaluate(_MEASURE_PANEL_JS, "#v2-settings-popover")
        runtime["surfaces"]["S-SET"] = s_set
        # ink / muted / accent / CTA 白字；黑字浏览器默认不计超标（cap=5）
        runtime["findings"].extend(
            _findings_from_panel(s_set, surface="S-SET", font_cap=5, color_cap=5)
        )
        page.locator("#v2-settings-popover").screenshot(path=str(OUT_DIR / "s-set.png"))

        # ── S-SHEET · preview refine sheet ──
        if not demo_assets_available():
            pytest.skip("demo assets not present")
        trip_id = seed_arc14_preview_trip(studio_server["trips_dir"])
        page.goto(
            f"{studio_server['base']}/{trip_id}/index.html",
            wait_until="networkidle",
        )
        page.locator(".preview-toolbar__dock").wait_for(state="visible", timeout=15_000)
        page.locator(".preview-toolbar__menu-btn").click()
        page.wait_for_function(
            '() => document.querySelector(".preview-sheet-root")'
            '.classList.contains("preview-sheet-root--open")',
            timeout=10_000,
        )
        page.wait_for_timeout(600)
        s_sheet = page.evaluate(_MEASURE_PANEL_JS, ".preview-sheet")
        runtime["surfaces"]["S-SHEET"] = s_sheet
        runtime["findings"].extend(
            _findings_from_panel(s_sheet, surface="S-SHEET", font_cap=5, color_cap=6)
        )
        page.locator(".preview-sheet").screenshot(path=str(OUT_DIR / "s-sheet.png"))

        # cover + book tabs (extra density)
        page.locator('.preview-sheet__tab[data-sheet-tab="cover"]').click()
        page.wait_for_timeout(250)
        s_cover = page.evaluate(_MEASURE_PANEL_JS, ".preview-sheet")
        runtime["surfaces"]["S-SHEET-COVER"] = s_cover
        runtime["findings"].extend(
            _findings_from_panel(s_cover, surface="S-SHEET-COVER", font_cap=5, color_cap=6)
        )
        page.locator(".preview-sheet").screenshot(path=str(OUT_DIR / "s-sheet-cover.png"))

        page.locator('.preview-sheet__tab[data-sheet-tab="book"]').click()
        page.wait_for_timeout(250)
        page.evaluate(
            """
            () => {
              const adv = document.querySelector('[data-book-zone="advanced"]');
              if (adv) adv.open = true;
            }
            """
        )
        page.wait_for_timeout(150)
        s_book = page.evaluate(_MEASURE_PANEL_JS, ".preview-sheet")
        runtime["surfaces"]["S-SHEET-BOOK"] = s_book
        runtime["findings"].extend(
            _findings_from_panel(s_book, surface="S-SHEET-BOOK", font_cap=6, color_cap=5)
        )
        page.locator(".preview-sheet").screenshot(path=str(OUT_DIR / "s-sheet-book.png"))

        browser.close()

    for f in static_report.get("findings") or []:
        runtime["findings"].append(
            {
                "id": f["id"],
                "severity": f["severity"],
                "surface": "static",
                "selector": f.get("selector"),
                "detail": f.get("detail"),
                "files": f.get("files"),
            }
        )

    runtime["summary"] = {
        "findings": len(runtime["findings"]),
        "P0": sum(1 for f in runtime["findings"] if f.get("severity") == "P0"),
        "P1": sum(1 for f in runtime["findings"] if f.get("severity") == "P1"),
        "P2": sum(1 for f in runtime["findings"] if f.get("severity") == "P2"),
        "staticP0": static_report["summary"]["P0"],
        "staticP1": static_report["summary"]["P1"],
        "staticP2": static_report["summary"]["P2"],
    }
    (OUT_DIR / "runtime-audit.json").write_text(
        json.dumps(runtime, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    assert "S-SET" in runtime["surfaces"]
    assert runtime["surfaces"]["S-SET"].get("fontSizeCount", 0) >= 1
    assert "S-SHEET" in runtime["surfaces"]
    assert runtime["surfaces"]["S-SHEET"].get("fontSizeCount", 0) >= 1
    assert_no_blocking_findings(runtime["findings"], label="wave2-settings-sheet")
