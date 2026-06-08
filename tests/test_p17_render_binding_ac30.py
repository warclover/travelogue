"""AC-P17-30 · focal CSS binding via build_render_context."""

from __future__ import annotations

from travelogue.layout_engine.render_binding import (
    cover_rules_use_focal_variables,
    focal_object_position_css,
    slot_style_includes_focal,
)
from travelogue.render.context import build_layout_screen


def test_focal_object_position_css_formula() -> None:
    assert focal_object_position_css(focal_x=0.5, focal_y=0.45) == "calc(0.5 * 100%) calc(0.45 * 100%)"
    assert focal_object_position_css(focal_x=0.0, focal_y=1.0) == "calc(0.0 * 100%) calc(1.0 * 100%)"


def test_slot_style_includes_focal() -> None:
    assert slot_style_includes_focal({"focalPoint": {"x": 0.62, "y": 0.38}})
    assert slot_style_includes_focal({"focalPoint": {}})
    assert not slot_style_includes_focal({"focalPoint": {"x": "bad"}})


def test_cover_rules_bind_focal_variables() -> None:
    violations = cover_rules_use_focal_variables()
    assert violations == []


def test_build_layout_screen_injects_focal_css_vars() -> None:
    asset = {
        "id": "a1",
        "path": "assets/a1.jpg",
        "width": 1200,
        "height": 1600,
        "focalPoint": {"x": 0.62, "y": 0.38},
    }
    screen = build_layout_screen(
        {
            "patternId": "screen-portrait-1",
            "slots": [{"assetId": "a1", "fit": "cover", "displayAspect": 0.75}],
        },
        {"a1": asset},
        meta_title="Test",
        export_layout="web",
    )
    style = str(screen["slots"][0].get("slotStyle") or "")
    assert "--focal-x: 0.62" in style
    assert "--focal-y: 0.38" in style
    assert focal_object_position_css(focal_x=0.62, focal_y=0.38) == "calc(0.62 * 100%) calc(0.38 * 100%)"
