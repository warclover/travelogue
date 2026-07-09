"""PR-5 · editorial probe baselines + dogfood compare transforms."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from travelogue.layout_engine.editorial.portrait_row import (
    LAYOUT_HINT_PORTRAIT_ROW_EDITORIAL,
    PATTERN_PORTRAIT_3,
    PATTERN_PORTRAIT_3_EDITORIAL,
)
from travelogue.layout_templates.probe_editorial import (
    EDITORIAL_PROBE_IDS,
    build_editorial_probe_html,
    editorial_baseline_path,
    editorial_probe_id,
    run_editorial_screenshot_probe,
)
from travelogue.render.compare_editorial_portrait_row import (
    transform_trip_for_editorial_compare,
)


def test_editorial_probe_ids() -> None:
    assert editorial_probe_id("contain") in EDITORIAL_PROBE_IDS
    assert editorial_probe_id("cover") in EDITORIAL_PROBE_IDS


def test_build_editorial_probe_html_contain_and_cover() -> None:
    contain = build_editorial_probe_html(variant="contain")
    cover = build_editorial_probe_html(variant="cover")
    assert 'data-pattern="screen-portrait-3-editorial"' in contain
    assert "layout-slot__img--contain" in contain
    assert "layout-slot__img--cover" in cover
    assert "--editorial-row-ar:" in cover


def test_transform_trip_legacy_and_editorial() -> None:
    trip = {
        "tripId": "probe-trip",
        "layoutEngine": "screens",
        "assets": [
            {
                "id": "p1",
                "tags": ["person"],
                "nativeWidth": 900,
                "nativeHeight": 1600,
                "layoutEligible": True,
            },
            {
                "id": "p2",
                "tags": ["person"],
                "nativeWidth": 900,
                "nativeHeight": 1600,
                "layoutEligible": True,
            },
            {
                "id": "p3",
                "tags": ["person"],
                "nativeWidth": 900,
                "nativeHeight": 1600,
                "layoutEligible": True,
            },
        ],
        "chapters": [
            {
                "id": "ch-01",
                "screens": [
                    {
                        "patternId": PATTERN_PORTRAIT_3_EDITORIAL,
                        "layoutHint": LAYOUT_HINT_PORTRAIT_ROW_EDITORIAL,
                        "screenId": "ch-01-sc-01",
                        "slots": [
                            {"assetId": "p1", "slot": 0, "fit": "contain"},
                            {"assetId": "p2", "slot": 1, "fit": "contain"},
                            {"assetId": "p3", "slot": 2, "fit": "contain"},
                        ],
                    }
                ],
            }
        ],
    }
    legacy = transform_trip_for_editorial_compare(trip, mode="legacy")
    editorial = transform_trip_for_editorial_compare(trip, mode="editorial")
    sc_l = legacy["chapters"][0]["screens"][0]
    sc_e = editorial["chapters"][0]["screens"][0]
    assert sc_l["patternId"] == PATTERN_PORTRAIT_3
    assert sc_l["layoutHint"] == "person-triple"
    assert sc_e["patternId"] == PATTERN_PORTRAIT_3_EDITORIAL
    assert sc_e["layoutHint"] == LAYOUT_HINT_PORTRAIT_ROW_EDITORIAL


@pytest.mark.unit
def test_run_editorial_screenshot_probe_missing_baseline() -> None:
    pytest.importorskip("playwright")
    for probe_id in EDITORIAL_PROBE_IDS:
        path = editorial_baseline_path(probe_id)
        backup = path.read_bytes() if path.is_file() else None
        if path.is_file():
            path.unlink()
        try:
            out = run_editorial_screenshot_probe(update_baselines=False)
            if out.get("skipped"):
                pytest.skip(out.get("reason", "playwright unavailable"))
            assert out["ok"] is False
            assert any(probe_id in w for w in out.get("warnings") or [])
            break
        finally:
            if backup is not None:
                path.write_bytes(backup)


def _probe_html_with_inlined_css(*, variant: str) -> str:
    """Probe page with inlined CSS so Playwright file:// loads footline rules reliably."""
    from travelogue.layout_templates.probe_editorial import OVERLAYS_CSS
    from travelogue.paths import JOURNAL_SCREENS_CSS

    html = build_editorial_probe_html(variant=variant)  # type: ignore[arg-type]
    css = (
        JOURNAL_SCREENS_CSS.read_text(encoding="utf-8")
        + "\n"
        + OVERLAYS_CSS.read_text(encoding="utf-8")
    )
    stripped = re.sub(r'<link rel="stylesheet" href="[^"]+" />\s*', "", html)
    return stripped.replace("</head>", f"<style>\n{css}\n</style>\n</head>")


_FOOTLINE_BBOX_JS = """
() => {
  const screen = document.querySelector('.layout-screen[data-pattern="screen-portrait-3-editorial"]');
  if (!screen) return null;
  const grid = screen.querySelector('.layout-screen__grid--3col');
  if (!grid) return null;
  const rowBottom = grid.getBoundingClientRect().bottom;
  const imgs = screen.querySelectorAll('img.layout-slot__img--contain');
  if (imgs.length !== 3) return null;
  const deltas = Array.from(imgs).map(
    (img) => Math.abs(rowBottom - img.getBoundingClientRect().bottom)
  );
  const footBottoms = Array.from(imgs).map((img) => img.getBoundingClientRect().bottom);
  return {
    deltas,
    mutual: Math.max(...footBottoms) - Math.min(...footBottoms),
  };
}
"""


@pytest.mark.e2e
def test_ac_ed_04_footline_align_contain_bbox(tmp_path: Path) -> None:
    """AC-ED-04 · 人物 contain 行：三槽 img 底边距 row 底 ≤ 2px（Playwright bbox）。"""
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    html = _probe_html_with_inlined_css(variant="contain")
    probe_file = tmp_path / "editorial-footline-probe.html"
    probe_file.write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 960})
        page.goto(probe_file.as_uri(), wait_until="load")
        result = page.evaluate(_FOOTLINE_BBOX_JS)
        browser.close()
    assert result is not None, "editorial contain probe page missing expected DOM"
    assert all(d <= 2.5 for d in result["deltas"]), f"row footline delta px: {result['deltas']}"
    assert result["mutual"] <= 2.5, f"mutual footline delta px: {result['mutual']}"


@pytest.mark.unit
def test_run_editorial_screenshot_probe_matches_baselines() -> None:
    pytest.importorskip("playwright")
    missing = [pid for pid in EDITORIAL_PROBE_IDS if not editorial_baseline_path(pid).is_file()]
    if missing:
        pytest.skip(f"missing baselines: {', '.join(missing)} (run lte_probe_regress --screenshot --update-baselines)")
    out = run_editorial_screenshot_probe(update_baselines=False)
    if out.get("skipped"):
        pytest.skip(out.get("reason", "playwright unavailable"))
    assert out["ok"] is True
    assert out["compared"] == len(EDITORIAL_PROBE_IDS)
