"""Placeholder script in draft render (REL-11)."""

from __future__ import annotations

import json

from travelogue.paths import FIXTURES_DIR
from travelogue.render.dual_layout_regression import prepare_trip_web_screens
from travelogue.render.engine import render_html
from travelogue.templating.router import apply_template_selection


def test_draft_html_includes_placeholder_script() -> None:
    raw = json.loads((FIXTURES_DIR / "trip.render_golden.json").read_text(encoding="utf-8"))
    trip = prepare_trip_web_screens(raw)
    apply_template_selection(trip, mode="smart")
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
    )
    assert "TRAVELOGUE_PLACEHOLDERS" in html
    assert "meta.title" in html or "epilogue" in html
