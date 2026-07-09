"""T-04: exportLayout=auto · 768px / 48rem breakpoint contract."""

from __future__ import annotations

import json

from travelogue.paths import JOURNAL_CSS, MANIFEST_PATH
from travelogue.render.engine import render_html
from travelogue.render.golden_regression import load_golden_trip


def test_manifest_breakpoint_768() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    page = manifest["page"]
    assert page["breakpointWebPx"] == 768
    assert page["breakpointWeb"] == "48rem"


def test_journal_css_bp_web_48rem() -> None:
    css = JOURNAL_CSS.read_text(encoding="utf-8")
    assert "--bp-web: 48rem" in css
    assert "@media (min-width: 48rem)" in css
    assert 'html[data-layout="auto"]' in css


def test_auto_render_pins_auto_layout_attr() -> None:
    trip = load_golden_trip()
    trip["exportLayout"] = "auto"
    html = render_html(trip, export_mode="draft")
    assert 'data-layout="auto"' in html
    assert 'data-layout="web"' not in html
    assert 'data-layout="mobile"' not in html


def test_mobile_render_overlay_and_layout_attr() -> None:
    trip = load_golden_trip()
    html = render_html(
        trip,
        export_mode="draft",
        export_layout_override="mobile",
        layout_engine_override="legacy",
    )
    assert 'data-layout="mobile"' in html
    assert "media-card--overlay" in html
