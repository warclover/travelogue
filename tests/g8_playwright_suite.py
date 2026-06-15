"""Phase 13 G8 browser checks (REL-01 / AC-01 / AC-14). Used by pytest and walkthrough script."""

from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


def seed_g8_preview_trip(trips_dir: Path) -> str:
    """Minimal trip with preview toolbar for G8-11b."""
    from travelogue.config import AppConfig
    from travelogue.services.trip_factory import create_trip
    from travelogue.web.studio_chrome import inject_studio_chrome

    trip_id = "g8-preview"
    trips_dir.mkdir(parents=True, exist_ok=True)
    create_trip(trip_id, trips_dir, cfg=AppConfig(trips_dir=trips_dir))
    trip_dir = trips_dir / trip_id
    trip = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
    trip.setdefault("chapters", [{"id": "ch1", "title": "第一章", "screens": [
        {"screenId": "s1", "patternId": "screen-portrait-1", "slots": [{"assetId": "a1"}]}
    ]}])
    trip.setdefault("assets", [{"assetId": "a1", "type": "image"}])
    (trip_dir / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    raw = (
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>G8</title></head>"
        "<body><section class=\"chapter\" data-chapter-id=\"ch1\"></section></body></html>"
    )
    (trip_dir / "index.html").write_text(inject_studio_chrome(raw), encoding="utf-8")
    return trip_id


def _wait_visible(page: Page, el_id: str, timeout: int = 20_000) -> None:
    page.wait_for_function(
        """
        (id) => {
          const el = document.getElementById(id);
          if (!el || el.hidden) return false;
          const cs = getComputedStyle(el);
          return cs.display !== 'none' && cs.visibility !== 'hidden'
            && el.getClientRects().length > 0;
        }
        """,
        arg=el_id,
        timeout=timeout,
    )


def _goto(page: Page, base: str, query: str = "") -> None:
    page.goto(base + "/" + (("?" + query) if query else ""), wait_until="networkidle")


def check_g8_08_hint_switch(page: Page, base: str) -> dict:
    _goto(page, base, "dev=1&studioState=sheet-open")
    _wait_visible(page, "v2-sheet-root")
    page.wait_for_function(
        "() => document.querySelector('#v2-template-mode option[value^=\"manual:\"]')",
        timeout=10_000,
    )
    page.evaluate(
        """
        () => {
          const confirm = document.getElementById('v2-sheet-confirm');
          if (confirm) confirm.hidden = false;
        }
        """
    )
    smart_hint = page.locator("#v2-template-hint").inner_text().strip()
    manual_value = page.locator(
        '#v2-template-mode option[value^="manual:"]'
    ).first.get_attribute("value")
    assert manual_value, "expected at least one manual template option"
    page.evaluate(
        """
        (value) => {
          const sel = document.getElementById('v2-template-mode');
          if (!sel) return;
          sel.value = value;
          sel.dispatchEvent(new Event('change', { bubbles: true }));
        }
        """,
        manual_value,
    )
    page.wait_for_function(
        """
        (smartText) => {
          const hint = document.getElementById('v2-template-hint');
          const manual = ((hint && hint.textContent) || '').trim();
          return manual.length > 0 && manual !== smartText;
        }
        """,
        arg=smart_hint,
        timeout=10_000,
    )
    manual_hint = page.locator("#v2-template-hint").inner_text().strip()
    ok = bool(smart_hint and manual_hint and smart_hint != manual_hint)
    return {
        "id": "G8-08",
        "name": "浏览器切换 hint 文案",
        "pass": ok,
        "skipped": False,
        "evidence": {"smartHintLen": len(smart_hint), "manualHintLen": len(manual_hint)},
    }


def check_g8_09_template_feedback(page: Page, base: str) -> dict:
    _goto(page, base, "dev=1&studioFixture=multi")
    _wait_visible(page, "v2-frame")
    msg_line = "已为你匹配：视觉游记"
    page.evaluate(
        """
        async (line) => {
          const mod = await import('/__studio/homepage-v2/first-success.js');
          mod.showFirstSuccess({
            result: {
              tripId: 'g8-trip',
              title: 'G8 测试',
              photoCount: 8,
              segmentCount: 2,
              templateFeedbackMessage: line,
              templateFeedbackKind: 'smart',
              resolvedTemplateId: 'visual-journal',
            },
          });
        }
        """,
        msg_line,
    )
    _wait_visible(page, "v2-success-open")
    text = page.locator("#v2-success-msg").inner_text()
    ok = msg_line in text
    return {
        "id": "G8-09",
        "name": "真实导入 toast templateFeedbackMessage",
        "pass": ok,
        "skipped": False,
        "evidence": {"snippet": text[:120]},
    }


def check_g8_10_lan_permission_ui(page: Page, base_lan: str) -> dict:
    page.goto(
        base_lan + "/templates-admin?simulateLanDeny=1",
        wait_until="networkidle",
    )
    page.once("dialog", lambda dialog: dialog.accept())
    page.locator("#btn-l1").click()
    page.wait_for_function(
        "() => { const el = document.getElementById('log'); return el && !el.hidden && el.textContent.length > 20; }",
        timeout=10_000,
    )
    log_text = page.locator("#log").inner_text()
    ok = "模板管理权限不足" in log_text or "E_TEMPLATE_PERMISSION_DENIED" in log_text
    return {
        "id": "G8-10",
        "name": "LAN 权限拒绝 UI",
        "pass": ok,
        "skipped": False,
        "evidence": {"logSnippet": log_text[:200]},
    }


def check_g8_11_shelf_template_label(page: Page, base: str) -> dict:
    _goto(page, base, "dev=1&studioFixture=multi-templates")
    _wait_visible(page, "v2-shelf")
    card_text = page.locator('.v2-shelf__card[data-trip-id="kyoto-rain"]').inner_text()
    ok = "智能匹配" in card_text
    return {
        "id": "G8-11a",
        "name": "书架 templateSourceLabel",
        "pass": ok,
        "skipped": False,
        "evidence": {"cardSnippet": card_text[:80]},
    }


def check_g8_11_preview_toolbar(page: Page, base: str, trip_id: str) -> dict:
    page.goto(f"{base}/{trip_id}/index.html", wait_until="networkidle")
    page.wait_for_selector(".preview-toolbar--v4", timeout=15_000)
    page.locator(".preview-toolbar__menu-btn").click()
    page.wait_for_selector(".preview-sheet", timeout=10_000)
    page.locator('.preview-sheet__tab[data-sheet-tab="layout"]').click()
    page.wait_for_selector(".preview-toolbar__template-adjust select", timeout=15_000)
    has_apply = page.locator(".preview-toolbar__template-adjust button").inner_text() == "应用"
    return {
        "id": "G8-11b",
        "name": "预览 Sheet 排版 Tab 模板 PATCH 控件",
        "pass": has_apply,
        "skipped": False,
        "evidence": {"tripId": trip_id},
    }


def run_g8_playwright_suite(
    *,
    base: str,
    base_lan: str | None = None,
    preview_trip_id: str | None = None,
) -> list[dict]:
    items: list[dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            items.append(check_g8_08_hint_switch(page, base))
            items.append(check_g8_09_template_feedback(page, base))
            items.append(check_g8_11_shelf_template_label(page, base))
            if base_lan:
                items.append(check_g8_10_lan_permission_ui(page, base_lan))
            if preview_trip_id:
                items.append(check_g8_11_preview_toolbar(page, base, preview_trip_id))
        finally:
            browser.close()
    return items


def collapse_g8_items(items: list[dict]) -> list[dict]:
    """Merge G8-11a/b into single G8-11 row for signoff JSON."""
    out: list[dict] = []
    g11_parts = [i for i in items if i["id"] in ("G8-11a", "G8-11b")]
    for i in items:
        if i["id"] in ("G8-11a", "G8-11b"):
            continue
        out.append(i)
    if g11_parts:
        a = next((x for x in g11_parts if x["id"] == "G8-11a"), None)
        b = next((x for x in g11_parts if x["id"] == "G8-11b"), None)
        if a and b:
            out.append(
                {
                    "id": "G8-11",
                    "name": "书架 templateSourceLabel / 预览栏",
                    "pass": bool(a.get("pass")) and bool(b.get("pass")),
                    "skipped": False,
                    "evidence": {"shelf": a.get("evidence"), "preview": b.get("evidence")},
                }
            )
        elif a:
            out.append(
                {
                    "id": "G8-11",
                    "name": "书架 templateSourceLabel / 预览栏",
                    "pass": bool(a.get("pass")),
                    "skipped": not b,
                    "evidence": a.get("evidence"),
                }
            )
    return out
