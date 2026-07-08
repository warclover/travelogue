"""Golden-trip render step for template admission (render layer)."""

from __future__ import annotations

from typing import Any

from travelogue.domain.admission_hooks import register_golden_render_step
from travelogue.render.dual_layout_regression import prepare_trip_web_screens
from travelogue.render.engine import render_html


def golden_render_admission_step(template_id: str, trip: dict[str, Any]) -> dict[str, Any]:
    trip_render = prepare_trip_web_screens(dict(trip))
    sel = trip_render.setdefault("templateSelection", {})
    sel["resolvedTemplateId"] = template_id
    trip_render["templateId"] = template_id
    html = render_html(
        trip_render,
        template_id=template_id,
        layout_engine_override="screens",
        export_layout_override="web",
    )
    return {
        "name": "golden_render",
        "pass": isinstance(html, str) and len(html) > 200,
        "htmlBytes": len(html) if isinstance(html, str) else 0,
    }


register_golden_render_step(golden_render_admission_step)
