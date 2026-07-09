"""Audit vertical scroll containers on Studio v2 homepage (GET /)."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.integration.studio.test_studio_server import (  # noqa: E402
    _free_port,
    _start_studio_server,
)

AUDIT_JS = """
() => {
  function info(el) {
    if (!el) return null;
    const cs = getComputedStyle(el);
    const canY = el.scrollHeight > el.clientHeight + 1;
    const canX = el.scrollWidth > el.clientWidth + 1;
    if (!canY && !canX && cs.overflowY === 'visible' && cs.overflowX === 'visible') {
      return null;
    }
    return {
      tag: el.tagName,
      id: el.id || null,
      class: typeof el.className === 'string' ? el.className.slice(0, 80) : null,
      overflowY: cs.overflowY,
      overflowX: cs.overflowX,
      scrollH: el.scrollHeight,
      clientH: el.clientHeight,
      scrollW: el.scrollWidth,
      clientW: el.clientWidth,
      canScrollY: canY,
      canScrollX: canX,
    };
  }

  const all = [];
  document.querySelectorAll('*').forEach((el) => {
    const row = info(el);
    if (row && (row.canScrollY || row.canScrollX || row.overflowY !== 'visible' || row.overflowX !== 'visible')) {
      all.push(row);
    }
  });

  const cssLink = [...document.querySelectorAll('link[rel=stylesheet]')]
    .map((l) => l.href)
    .find((h) => h.includes('studio-home-v2.css'));

  return fetch(cssLink)
    .then((r) => r.text())
    .then((text) => ({
      viewport: { w: innerWidth, h: innerHeight },
      docScroll: {
        el: document.documentElement.scrollHeight,
        body: document.body.scrollHeight,
      },
      cssBento: (text.match(/\\.v2-bento\\s*\\{[^}]*\\}/) || [''])[0],
      cssPhone: (text.match(/\\.v2-phone__screen\\s*\\{[^}]*\\}/) || [''])[0],
      scrollables: all,
    }));
}
"""


def main() -> None:
    tmpdir = Path(tempfile.mkdtemp())
    (tmpdir / "trips").mkdir()
    port = _free_port()
    srv = _start_studio_server(tmpdir / "trips", port)
    base = f"http://127.0.0.1:{port}"

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(f"{base}/", wait_until="networkidle")
            page.wait_for_selector("#v2-frame", state="visible", timeout=15000)
            data = page.evaluate(AUDIT_JS)
            print(json.dumps(data, ensure_ascii=False, indent=2))
            browser.close()
    finally:
        srv.shutdown()
        srv.server_close()


if __name__ == "__main__":
    main()
