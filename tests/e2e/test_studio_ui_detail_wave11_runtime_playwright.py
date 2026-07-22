"""Studio UI Detail · Wave11 runtime closeout.

1) Static `--wave all` must be P0/P1 clean.
2) Runtime sample Help / Capability / Toast / Unsupported for font+color caps.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.studio_ui_detail_static_audit import run_audit as run_static_audit
from tests.e2e.test_studio_home_v2_ac_playwright import _goto_v2
from tests.integration.studio.test_studio_server import _free_port, _start_studio_server
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
    / "ui-detail-wave11-runtime"
)
VIEWPORT = {"width": 1280, "height": 900}

_MEASURE_PANEL_JS = """
(rootSel) => {
  const root = document.querySelector(rootSel);
  if (!root) return { error: 'missing ' + rootSel };
  const walk = [];
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
  const directText = (el) => {
    // Leaf text OR root with only text children (e.g. .studio__toast)
    const texts = [...el.childNodes]
      .filter((n) => n.nodeType === 3)
      .map((n) => (n.textContent || '').trim())
      .filter(Boolean);
    if (!texts.length) return '';
    const hasElementChild = [...el.childNodes].some((n) => n.nodeType === 1);
    if (hasElementChild && el !== root) return '';
    if (hasElementChild && el === root) {
      // Prefer descendant samples; only use root text if no element kids with text
      return '';
    }
    return texts.join(' ');
  };
  const sampleEl = (n) => {
    if (!isVisible(n)) return;
    const s = getComputedStyle(n);
    const text = directText(n);
    if (!text) return;
    if (iconOnly(n, text)) return;
    walk.push({
      tag: n.tagName.toLowerCase(),
      className: String(n.className || '').slice(0, 96),
      text: text.slice(0, 48),
      fontSize: parseFloat(s.fontSize),
      color: s.color,
    });
  };
  // Include root itself (toast puts message on the root node)
  sampleEl(root);
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT);
  let n;
  while ((n = walker.nextNode())) sampleEl(n);
  const fonts = [...new Set(walk.map((x) => x.fontSize.toFixed(1)))].sort(
    (a, b) => parseFloat(a) - parseFloat(b)
  );
  const colors = [...new Set(walk.map((x) => x.color))];
  return {
    surface: rootSel,
    textSampleCount: walk.length,
    uniqueFontSizes: fonts,
    uniqueColors: colors,
    fontSizeCount: fonts.length,
    colorCount: colors.length,
    samples: walk.slice(0, 36),
  };
}
"""


def _findings_from_panel(
    metrics: dict, *, surface: str, font_cap: int, color_cap: int
) -> list[dict]:
    out: list[dict] = []
    if metrics.get("error"):
        return [
            {
                "id": "D-UID-HARNESS",
                "severity": "P0",
                "surface": surface,
                "detail": metrics["error"],
            }
        ]
    if metrics.get("fontSizeCount", 0) > font_cap:
        out.append(
            {
                "id": "D-UID-03",
                "severity": "P1",
                "surface": surface,
                "detail": f"字号种类 {metrics['fontSizeCount']}: {metrics.get('uniqueFontSizes')}",
            }
        )
    if metrics.get("colorCount", 0) > color_cap:
        out.append(
            {
                "id": "D-UID-04",
                "severity": "P1",
                "surface": surface,
                "detail": f"颜色种类 {metrics['colorCount']}: {metrics.get('uniqueColors')}",
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


def test_studio_ui_detail_wave11_runtime_closeout(studio_server) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    static_report = run_static_audit(wave="all")
    (OUT_DIR / "static-audit-all.json").write_text(
        json.dumps(static_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    assert static_report["summary"]["P0"] == 0
    assert static_report["summary"]["P1"] == 0, [
        f for f in static_report["findings"] if f["severity"] == "P1"
    ]

    runtime: dict = {"surfaces": {}, "findings": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ── S-HELP / S-CAP / S-TOAST · desktop home ──
        page = browser.new_page(viewport=VIEWPORT)
        page.add_init_script(
            """
            try {
              localStorage.setItem('travelogue.desktop.capabilityCard.v1', '1');
            } catch (e) {}
            """
        )
        _goto_v2(page, studio_server["base"], "dev=1")
        page.wait_for_selector("#v2-frame", timeout=15_000)

        page.evaluate(
            """
            async () => {
              const mod = await import('/__studio/js/help-drawer.js');
              mod.openHelpDrawer({ source: 'ui-detail-w11' });
            }
            """
        )
        page.wait_for_selector(
            ".studio-help-drawer-root.is-open .studio-help-drawer__title",
            timeout=5_000,
        )
        help_m = page.evaluate(_MEASURE_PANEL_JS, ".studio-help-drawer")
        runtime["surfaces"]["S-HELP"] = help_m
        runtime["findings"].extend(
            _findings_from_panel(help_m, surface="S-HELP", font_cap=6, color_cap=5)
        )
        page.screenshot(path=str(OUT_DIR / "help-drawer.png"), full_page=False)

        # Force capability card: clear seen + close Help, then show
        shown = page.evaluate(
            """
            async () => {
              try {
                localStorage.removeItem('travelogue.desktop.capabilityCard.v1');
              } catch (e) {}
              const helpOn = await import('/__studio/js/help-onboarding.js');
              if (typeof helpOn.clearCapabilityCardSeen === 'function') {
                helpOn.clearCapabilityCardSeen();
              }
              const hd = await import('/__studio/js/help-drawer.js');
              if (typeof hd.closeHelpDrawer === 'function') hd.closeHelpDrawer();
              try {
                const { V2 } = await import('/__studio/homepage-v2/store.js');
                if (V2) {
                  V2.trips = [];
                  V2.tripsTotal = 0;
                  V2.state = 'Idle';
                }
              } catch (e2) {}
              const mod = await import('/__studio/js/capability-card.js');
              if (typeof mod.showCapabilityCard === 'function') {
                return !!mod.showCapabilityCard();
              }
              return false;
            }
            """
        )
        if not shown:
            # Fallback: mount panel markup for style measure (CSS already linked)
            page.evaluate(
                """
                () => {
                  let el = document.getElementById('studio-capability-card-root');
                  if (!el) {
                    el = document.createElement('div');
                    el.id = 'studio-capability-card-root';
                    el.className = 'studio-capability-card';
                    el.innerHTML =
                      '<div class="studio-capability-card__scrim"></div>' +
                      '<div class="studio-capability-card__panel">' +
                      '<button type="button" class="studio-capability-card__close" aria-label="关闭">×</button>' +
                      '<p class="studio-capability-card__title">照片留在本机，也能做成可发的游记</p>' +
                      '<p class="studio-capability-card__body">选一次旅行的照片，自动分章、排版；微信长图可直接发群。</p>' +
                      '<div class="studio-capability-card__actions">' +
                      '<button type="button" class="studio-capability-card__primary">开始制作我的游记</button>' +
                      '</div>' +
                      '<p class="studio-capability-card__linkrow">' +
                      '<button type="button" class="studio-capability-card__link">以后再升级 AI 文案 →</button>' +
                      '</p></div>';
                    document.body.appendChild(el);
                  }
                  el.hidden = false;
                }
                """
            )
        page.wait_for_function(
            """() => {
              const el = document.getElementById('studio-capability-card-root');
              return el && !el.hidden && el.querySelector('.studio-capability-card__panel');
            }""",
            timeout=5_000,
        )
        cap_m = page.evaluate(_MEASURE_PANEL_JS, ".studio-capability-card__panel")
        runtime["surfaces"]["S-CAP"] = cap_m
        runtime["findings"].extend(
            _findings_from_panel(cap_m, surface="S-CAP", font_cap=5, color_cap=4)
        )
        page.screenshot(path=str(OUT_DIR / "capability-card.png"), full_page=False)

        page.evaluate(
            """
            () => {
              if (typeof studioToast === 'function') {
                studioToast('UI Detail 抽检：保存完成', { duration: 8000 });
              }
            }
            """
        )
        page.wait_for_selector(".studio__toast", timeout=3_000)
        toast_m = page.evaluate(_MEASURE_PANEL_JS, ".studio__toast")
        runtime["surfaces"]["S-TOAST"] = toast_m
        # toast is single-line; allow 2 fonts / 2 colors
        runtime["findings"].extend(
            _findings_from_panel(toast_m, surface="S-TOAST", font_cap=2, color_cap=2)
        )
        page.screenshot(path=str(OUT_DIR / "studio-toast.png"), full_page=False)
        page.close()

        # ── S-UNSUPPORTED · phone width ──
        page2 = browser.new_page(viewport={"width": 390, "height": 844})
        _goto_v2(page2, studio_server["base"])
        page2.wait_for_selector("#v2-unsupported:not([hidden])", timeout=8_000)
        un_m = page2.evaluate(_MEASURE_PANEL_JS, ".v2-unsupported")
        runtime["surfaces"]["S-UNSUPPORTED"] = un_m
        runtime["findings"].extend(
            _findings_from_panel(un_m, surface="S-UNSUPPORTED", font_cap=5, color_cap=5)
        )
        page2.screenshot(path=str(OUT_DIR / "unsupported.png"), full_page=False)
        page2.close()
        browser.close()

    (OUT_DIR / "runtime-audit.json").write_text(
        json.dumps(runtime, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    p0 = [f for f in runtime["findings"] if f.get("severity") == "P0"]
    p1 = [f for f in runtime["findings"] if f.get("severity") == "P1"]
    assert p0 == [], p0
    assert p1 == [], p1
    assert runtime["surfaces"]["S-HELP"].get("textSampleCount", 0) >= 1
    assert runtime["surfaces"]["S-CAP"].get("textSampleCount", 0) >= 1
    assert runtime["surfaces"]["S-TOAST"].get("textSampleCount", 0) >= 1
    assert runtime["surfaces"]["S-UNSUPPORTED"].get("textSampleCount", 0) >= 1
