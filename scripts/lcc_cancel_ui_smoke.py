"""UI smoke: Dock shows 取消导出 during exporting state."""

from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8768"
TRIP = "demo-815dc906d3"
ROOT = Path(__file__).resolve().parents[1]
DOCK = ROOT / "templates" / "studio" / "preview-toolbar-v3-task-dock.js"


def main() -> None:
    dock = DOCK.read_text(encoding="utf-8")
    assert "取消导出" in dock and "无法取消" not in dock, "dock source missing CTA"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(f"{BASE}/{TRIP}/index.html", wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(2500)

        shown = page.evaluate(
            """() => {
              const root = document.querySelector('.preview-toolbar') || document.body;
              if (root && root._taskDock && root._taskDock.showExporting) {
                root._taskDock.showExporting({title: '正在导出长图', subtitle: '狗粮', pct: 20});
                return true;
              }
              return false;
            }"""
        )
        assert shown, "task dock showExporting unavailable"
        page.wait_for_timeout(400)
        cancel_n = page.get_by_text("取消导出").count()
        bad_n = page.get_by_text("导出开始后无法取消").count()
        print(json.dumps({"showExporting": shown, "cancel_btn": cancel_n, "bad_vocab": bad_n}))
        assert cancel_n >= 1 and bad_n == 0
        browser.close()
    print("UI PASS")


if __name__ == "__main__":
    main()
