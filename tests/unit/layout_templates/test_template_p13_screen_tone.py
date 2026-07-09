"""AC-P13-06: screen_tone with templateSelection (REL-06)."""

from __future__ import annotations

import json

from travelogue.paths import FIXTURES_DIR
from travelogue.render.dual_layout_regression import prepare_trip_web_screens
from travelogue.render.engine import render_html
from travelogue.render.screen_tone import chapter_separator_style
from travelogue.templating.resolver import resolve_effective_template
from travelogue.templating.router import apply_template_selection


def test_screen_tone_helper_still_valid() -> None:
    style = chapter_separator_style({"r": 34, "g": 40, "b": 50})
    assert "--chapter-separator-ink" in style


def test_p13_render_includes_separator_styles_with_template_selection() -> None:
    raw = json.loads((FIXTURES_DIR / "trip.render_golden.json").read_text(encoding="utf-8"))
    trip = prepare_trip_web_screens(raw)
    apply_template_selection(trip, mode="smart")
    assert resolve_effective_template(trip) == "visual-journal"
    html = render_html(
        trip,
        template_id=resolve_effective_template(trip),
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
    )
    assert "chapter-separator" in html or "--chapter-separator-ink" in html
