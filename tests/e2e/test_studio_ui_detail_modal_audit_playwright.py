"""Studio UI Detail · modal-family runtime audit (pilot).

Collects computed styles for:
  - studioModal (homepage · studio-modal.css)
  - FirstSuccess / Failure overlays
  - Import Wizard

Writes JSON + screenshots under docs/acceptance-records/attachments/ui-detail-modal-pilot/.
Fails on P0/P1 findings (semantic color families); P2 is reported only.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.studio_ui_detail_static_audit import run_audit as run_static_audit
from tests.e2e.ui_detail_runtime_helpers import (
    assert_no_blocking_findings,
    findings_from_panel_metrics,
)
from tests.integration.studio.test_studio_server import _free_port, _start_studio_server
from travelogue.paths import ROOT

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]

OUT_DIR = ROOT / "docs" / "acceptance-records" / "attachments" / "ui-detail-modal-pilot"
VIEWPORT = {"width": 1280, "height": 900}

# Contract §1 (studio-modal.css)
CONTRACT_MODAL = {
    "titleFontPx": 17.0,
    "bodyFontPx": 14.0,
    "btnFontPx": 13.0,
    "titleColor": "rgb(20, 17, 13)",
    "bodyColor": "rgba(20, 17, 13, 0.72)",
    "radiusPx": 10.0,
    "widthMaxPx": 400.0,
    "btnMinHeightPx": 40.0,
    "btnRadiusPx": 6.0,
}


def _goto_v2(page, base: str) -> None:
    page.add_init_script(
        """
        try {
          localStorage.setItem('travelogue.desktop.capabilityCard.v1', '1');
        } catch (e) {}
        """
    )
    page.goto(base + "/", wait_until="networkidle")
    page.evaluate(
        """
        () => {
          const el = document.getElementById('studio-capability-card-root');
          if (el) el.hidden = true;
        }
        """
    )


_MEASURE_MODAL_JS = """
async (opts) => {
  const p = window.studioModal(opts || {
    title: '确认删除这本游记？',
    body: '删除后无法恢复，书架与本地缓存中的预览都会移除。',
    confirmText: '删除',
    cancelText: '取消',
    danger: true,
    helpItemId: 'H2',
    helpLinkText: '了解更多 →',
  });
  // leave open for measurement
  const modal = document.querySelector('.studio__modal');
  const title = modal.querySelector('h3');
  const body = modal.querySelector('.studio__modal-body, p');
  const help = modal.querySelector('.studio__modal-help-link');
  const btns = [...modal.querySelectorAll('.studio__btn')];
  const cs = (el) => el ? getComputedStyle(el) : null;
  const box = (el) => {
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { left: r.left, top: r.top, width: r.width, height: r.height };
  };
  const titleCs = cs(title);
  const bodyCs = cs(body);
  const modalCs = cs(modal);
  const btnMetrics = btns.map((b) => {
    const s = cs(b);
    return {
      text: (b.textContent || '').trim(),
      fontSize: parseFloat(s.fontSize),
      color: s.color,
      minHeight: parseFloat(s.minHeight) || b.getBoundingClientRect().height,
      height: b.getBoundingClientRect().height,
      borderRadius: s.borderRadius,
      fontWeight: s.fontWeight,
    };
  });
  const textNodes = [title, body, help, ...btns].filter(Boolean);
  const fonts = new Set();
  const colors = new Set();
  for (const el of textNodes) {
    const s = cs(el);
    fonts.add(parseFloat(s.fontSize).toFixed(1));
    colors.add(s.color);
  }
  const titleBox = box(title);
  const bodyBox = box(body);
  return {
    surface: 'S-MODAL',
    modal: {
      width: modal.getBoundingClientRect().width,
      padding: modalCs.padding,
      borderRadius: modalCs.borderRadius,
      color: modalCs.color,
      background: modalCs.backgroundColor,
    },
    title: {
      fontSize: parseFloat(titleCs.fontSize),
      lineHeight: titleCs.lineHeight,
      fontWeight: titleCs.fontWeight,
      color: titleCs.color,
      left: titleBox.left,
    },
    body: {
      fontSize: parseFloat(bodyCs.fontSize),
      lineHeight: bodyCs.lineHeight,
      color: bodyCs.color,
      left: bodyBox.left,
    },
    help: help ? {
      fontSize: parseFloat(cs(help).fontSize),
      color: cs(help).color,
    } : null,
    buttons: btnMetrics,
    uniqueFontSizes: [...fonts].sort(),
    uniqueColors: [...colors].sort(),
    titleBodyLeftDelta: Math.abs(titleBox.left - bodyBox.left),
  };
}
"""

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
      cur = cur.parentElement;
      if (cur === root.parentElement) break;
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
      className: String(n.className || '').slice(0, 80),
      text: text.slice(0, 40),
      fontSize: parseFloat(s.fontSize),
      color: s.color,
      fontWeight: s.fontWeight,
      lineHeight: s.lineHeight,
      left: n.getBoundingClientRect().left,
    });
  }
  const fonts = [...new Set(walk.map((x) => x.fontSize.toFixed(1)))].sort(
    (a, b) => parseFloat(a) - parseFloat(b)
  );
  const colors = [...new Set(walk.map((x) => x.color))];
  // left-edge cluster of first two text rows if present
  let leftDelta = null;
  if (walk.length >= 2) {
    leftDelta = Math.abs(walk[0].left - walk[1].left);
  }
  return {
    surface: rootSel,
    textSampleCount: walk.length,
    uniqueFontSizes: fonts,
    uniqueColors: colors,
    fontSizeCount: fonts.length,
    colorCount: colors.length,
    leftDeltaFirstTwo: leftDelta,
    samples: walk.slice(0, 24),
  };
}
"""


def _findings_from_modal(metrics: dict) -> list[dict]:
    out: list[dict] = []
    t = metrics["title"]["fontSize"]
    b = metrics["body"]["fontSize"]
    if abs(t - CONTRACT_MODAL["titleFontPx"]) > 0.5:
        out.append(
            {
                "id": "D-UID-02",
                "severity": "P0",
                "detail": f"标题字号 {t}px ≠ {CONTRACT_MODAL['titleFontPx']}px",
            }
        )
    if abs(b - CONTRACT_MODAL["bodyFontPx"]) > 0.5:
        out.append(
            {
                "id": "D-UID-02",
                "severity": "P0",
                "detail": f"正文字号 {b}px ≠ {CONTRACT_MODAL['bodyFontPx']}px",
            }
        )
    if metrics["title"]["color"] != CONTRACT_MODAL["titleColor"]:
        out.append(
            {
                "id": "D-UID-02",
                "severity": "P0",
                "detail": f"标题色 {metrics['title']['color']} ≠ {CONTRACT_MODAL['titleColor']}",
            }
        )
    if metrics["body"]["color"] != CONTRACT_MODAL["bodyColor"]:
        out.append(
            {
                "id": "D-UID-02",
                "severity": "P0",
                "detail": f"正文色 {metrics['body']['color']} ≠ {CONTRACT_MODAL['bodyColor']}",
            }
        )
    radius = metrics["modal"]["borderRadius"]
    # borderRadius may be "10px" or "10px 10px ..."
    r0 = float(str(radius).split()[0].replace("px", "") or 0)
    if abs(r0 - CONTRACT_MODAL["radiusPx"]) > 0.5:
        out.append(
            {
                "id": "D-UID-02",
                "severity": "P0",
                "detail": f"面板圆角 {radius} ≠ {CONTRACT_MODAL['radiusPx']}px",
            }
        )
    if metrics.get("titleBodyLeftDelta", 0) > 1.0:
        out.append(
            {
                "id": "D-UID-05",
                "severity": "P1",
                "detail": f"标题/正文左缘差 {metrics['titleBodyLeftDelta']:.2f}px",
            }
        )
    if len(metrics.get("uniqueFontSizes") or []) > 5:
        out.append(
            {
                "id": "D-UID-03",
                "severity": "P1",
                "detail": f"确认框字号种类 {metrics['uniqueFontSizes']}",
            }
        )
    # help 链 + danger CTA 白字时允许到 5（合同 §1 角色齐全）
    color_cap = 5 if metrics.get("help") else 4
    if len(metrics.get("uniqueColors") or []) > color_cap:
        out.append(
            {
                "id": "D-UID-04",
                "severity": "P1",
                "detail": f"确认框颜色种类 {len(metrics['uniqueColors'])}: {metrics['uniqueColors']}",
            }
        )
    # button radius / height consistency
    radii = set()
    heights = []
    for btn in metrics.get("buttons") or []:
        radii.add(str(btn.get("borderRadius")))
        heights.append(float(btn.get("height") or 0))
        fs = float(btn.get("fontSize") or 0)
        if abs(fs - CONTRACT_MODAL["btnFontPx"]) > 0.5:
            out.append(
                {
                    "id": "D-UID-02",
                    "severity": "P0",
                    "detail": f"按钮「{btn.get('text')}」字号 {fs}px",
                }
            )
    if len(radii) > 1:
        out.append(
            {
                "id": "D-UID-06",
                "severity": "P1",
                "detail": f"按钮圆角混用: {sorted(radii)}",
            }
        )
    if heights and (max(heights) - min(heights) > 2.0):
        out.append(
            {
                "id": "D-UID-06",
                "severity": "P1",
                "detail": f"按钮高度差 {max(heights) - min(heights):.1f}px",
            }
        )
    # pill vs 6px: if any radius looks like 999px
    for btn in metrics.get("buttons") or []:
        br = str(btn.get("borderRadius") or "")
        if "999" in br or br.startswith("20") or br.startswith("999"):
            out.append(
                {
                    "id": "D-UID-06",
                    "severity": "P1",
                    "detail": f"按钮「{btn.get('text')}」使用 pill 圆角 {br}（规范 6px）",
                }
            )
    return out


def _findings_from_panel(metrics: dict, *, surface: str) -> list[dict]:
    # Dark overlays: ink / muted / accent / CTA；语义色族 ≤4（透明度变体合并）
    return findings_from_panel_metrics(
        metrics, surface=surface, font_cap=5, color_cap=4
    )


def _measure_preview_chrome_dual(page, base: str) -> dict:
    """On homepage: append modal-chrome.css after studio-modal.css and re-measure."""
    page.evaluate(
        """
        (href) => {
          const existing = document.querySelector('link[data-ui-detail-dual="1"]');
          if (existing) existing.remove();
          const link = document.createElement('link');
          link.rel = 'stylesheet';
          link.href = href;
          link.setAttribute('data-ui-detail-dual', '1');
          document.head.appendChild(link);
        }
        """,
        f"{base}/__studio/preview-toolbar/modal-chrome.css",
    )
    page.wait_for_timeout(200)
    return page.evaluate(
        _MEASURE_MODAL_JS,
        {"title": "预览双 CSS", "body": "后加载 modal-chrome 覆盖首页规范。"},
    )


@pytest.fixture
def studio_server(tmp_path: Path):
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"
    try:
        yield {"base": base}
    finally:
        server.shutdown()
        server.server_close()


def test_studio_ui_detail_modal_family_audit(studio_server, tmp_path: Path) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    static_report = run_static_audit()
    (OUT_DIR / "static-audit.json").write_text(
        json.dumps(static_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    runtime: dict = {"surfaces": {}, "findings": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT)

        # 1) Homepage studioModal
        _goto_v2(page, studio_server["base"])
        page.wait_for_function("() => typeof window.studioModal === 'function'")
        modal_metrics = page.evaluate(_MEASURE_MODAL_JS)
        runtime["surfaces"]["S-MODAL"] = modal_metrics
        runtime["findings"].extend(_findings_from_modal(modal_metrics))
        page.locator(".studio__modal").screenshot(path=str(OUT_DIR / "s-modal.png"))
        page.keyboard.press("Escape")

        # stacked + secondary
        stacked = page.evaluate(
            _MEASURE_MODAL_JS,
            {
                "title": "保留还是丢弃？",
                "body": "检测到未完成的导入。",
                "confirmText": "继续",
                "secondaryText": "重新开始",
                "cancelText": "取消",
                "stacked": True,
            },
        )
        runtime["surfaces"]["S-MODAL-STACKED"] = stacked
        runtime["findings"].extend(
            [{**f, "surface": "S-MODAL-STACKED"} for f in _findings_from_modal(stacked)]
        )
        page.locator(".studio__modal").screenshot(path=str(OUT_DIR / "s-modal-stacked.png"))
        page.keyboard.press("Escape")

        # 2) FirstSuccess (force visible)
        page.evaluate(
            """
            () => {
              const el = document.getElementById('v2-first-success');
              el.hidden = false;
              el.classList.add('is-open');
              const msg = document.getElementById('v2-success-msg');
              if (msg) msg.textContent = '你的第一篇游记已生成';
              const facts = document.getElementById('v2-success-details');
              if (facts) {
                facts.hidden = false;
                facts.innerHTML = '<li>12 张照片 · 3 个章节</li><li>本机生成 · 可导出长图</li>';
              }
            }
            """
        )
        fs = page.evaluate(_MEASURE_PANEL_JS, "#v2-first-success .v2-first-success__panel")
        runtime["surfaces"]["S-FS"] = fs
        runtime["findings"].extend(_findings_from_panel(fs, surface="S-FS"))
        page.locator("#v2-first-success .v2-first-success__panel").screenshot(
            path=str(OUT_DIR / "s-fs.png")
        )
        page.evaluate(
            "() => { const el = document.getElementById('v2-first-success'); el.hidden = true; el.classList.remove('is-open'); }"
        )

        # 3) Failure
        page.evaluate(
            """
            () => {
              const el = document.getElementById('v2-failure');
              el.hidden = false;
              el.classList.add('is-open');
              const eyebrow = document.getElementById('v2-failure-eyebrow');
              if (eyebrow) eyebrow.textContent = '导入失败';
              document.getElementById('v2-failure-msg').textContent = '没能读完这个文件夹';
              document.getElementById('v2-failure-hint').textContent = '可换一个文件夹重试，或先用示例照片。';
              // 非鉴权导入失败不得露出 AI 配置 CTA
              const settings = document.getElementById('v2-failure-open-settings');
              if (settings) settings.hidden = true;
            }
            """
        )
        fail = page.evaluate(_MEASURE_PANEL_JS, "#v2-failure .v2-failure__panel")
        runtime["surfaces"]["S-FAIL"] = fail
        runtime["findings"].extend(_findings_from_panel(fail, surface="S-FAIL"))
        page.locator("#v2-failure .v2-failure__panel").screenshot(
            path=str(OUT_DIR / "s-fail.png")
        )
        page.evaluate(
            "() => { const el = document.getElementById('v2-failure'); el.hidden = true; el.classList.remove('is-open'); }"
        )

        # 4) Wizard
        page.click("#v2-cta")
        page.wait_for_selector("#v2-import-wizard", state="visible")
        wiz = page.evaluate(_MEASURE_PANEL_JS, "#v2-import-wizard")
        runtime["surfaces"]["S-WIZ"] = wiz
        runtime["findings"].extend(_findings_from_panel(wiz, surface="S-WIZ"))
        page.locator("#v2-import-wizard").screenshot(path=str(OUT_DIR / "s-wiz.png"))
        # close wizard so dual modal is not obscured
        page.keyboard.press("Escape")
        page.wait_for_timeout(150)

        # 5) Dual CSS (preview chrome override on homepage)
        dual = _measure_preview_chrome_dual(page, studio_server["base"])
        runtime["surfaces"]["S-MODAL-PREVIEW-DUAL"] = dual
        dual_findings = _findings_from_modal(dual)
        for f in dual_findings:
            f["surface"] = "S-MODAL-PREVIEW-DUAL"
            f["detail"] = "双 CSS 叠载后: " + f["detail"]
        runtime["findings"].extend(dual_findings)
        page.locator(".studio__modal").screenshot(path=str(OUT_DIR / "s-modal-dual-css.png"))

        browser.close()

    # merge static P0/P1 into runtime findings（P2 仅保留在 static 报告）
    for f in static_report.get("findings") or []:
        if f.get("severity") in ("P0", "P1"):
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
        "staticP2": static_report["summary"]["P2"],
    }
    (OUT_DIR / "runtime-audit.json").write_text(
        json.dumps(runtime, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Harness health + hard gate on P0/P1（消 find-only 假绿）
    assert "S-MODAL" in runtime["surfaces"]
    assert runtime["surfaces"]["S-MODAL"].get("title", {}).get("fontSize")
    dual_p0 = [
        f
        for f in runtime["findings"]
        if f.get("surface") == "S-MODAL-PREVIEW-DUAL" and f.get("severity") == "P0"
    ]
    assert not dual_p0, f"modal-chrome must not override studio-modal: {dual_p0}"
    static_modal_p0 = [
        f
        for f in static_report.get("findings") or []
        if f.get("id") == "D-UID-01" and "studio__modal" in str(f.get("selector", ""))
    ]
    assert not static_modal_p0, f"static dual-standard remains: {static_modal_p0}"
    assert_no_blocking_findings(runtime["findings"], label="modal-pilot")
