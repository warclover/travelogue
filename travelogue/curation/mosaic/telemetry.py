"""Online mosaic/layout metrics (PRD §7.1 → template-metrics.jsonl)."""

from __future__ import annotations

from typing import Any


def record_mosaic_layout_metrics(
    *,
    trip_id: str | None,
    layout_metrics: dict[str, Any],
    mosaic_enabled: bool,
) -> None:
    """Append curate-time layout KPIs; never raises."""
    try:
        from travelogue.templating.metrics import record_template_metric
    except ImportError:
        return

    labels = {"tripId": trip_id, "mosaicEnabled": mosaic_enabled}
    mapping = (
        ("layout.mosaic5.exposure_rate", "layout.mosaic5.exposure_rate"),
        ("layout.mosaic_v2.unified_exposure_rate", "layout.mosaic_v2.unified_exposure_rate"),
        ("layout.mosaic_v2.fallback_rate", "layout.mosaic_v2.fallback_rate"),
        ("layout.mosaic_v2.low_score_fallback_rate", "layout.mosaic_v2.low_score_fallback_rate"),
        ("layout.render.error_rate", "layout.render.error_rate"),
        ("layout.pattern.repeat_rate", "layout.pattern.repeat_rate"),
        ("layout.eligible_to_screen_coverage", "layout.eligible_to_screen_coverage"),
        ("layout.mosaic_v2.drop_rate", "layout.mosaic_v2.drop_rate"),
    )
    for key, metric_name in mapping:
        val = layout_metrics.get(key)
        if val is None:
            continue
        record_template_metric(metric_name, value=val, **labels)

    render_err = layout_metrics.get("layout.render.error_rate")
    if render_err is not None and mosaic_enabled:
        ok = float(render_err) == 0.0
        record_template_metric(
            "layout.mosaic_v2.render_check",
            tripId=trip_id,
            ok=ok,
            errorRate=render_err,
        )
