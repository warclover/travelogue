"""Curate exports mosaic layout metrics to template telemetry."""

from __future__ import annotations

from unittest.mock import patch

from travelogue.curation.mosaic.telemetry import record_mosaic_layout_metrics


def test_record_mosaic_layout_metrics_emits_prd_keys() -> None:
    calls: list[tuple[str, dict]] = []

    def _capture(name: str, **kwargs):
        calls.append((name, kwargs))

    with patch(
        "travelogue.templating.metrics.record_template_metric",
        side_effect=_capture,
    ):
        record_mosaic_layout_metrics(
            trip_id="trip-a",
            layout_metrics={
                "layout.mosaic5.exposure_rate": 0.6,
                "layout.mosaic_v2.fallback_rate": 0.0,
                "layout.eligible_to_screen_coverage": 1.0,
                "layout.render.error_rate": 0.0,
            },
            mosaic_enabled=True,
        )

    names = {n for n, _ in calls}
    assert "layout.mosaic5.exposure_rate" in names
    assert "layout.eligible_to_screen_coverage" in names
    assert "layout.mosaic_v2.render_check" in names
