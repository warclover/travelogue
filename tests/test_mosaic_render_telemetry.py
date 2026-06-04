"""layout.render.error_rate offline validation."""

from __future__ import annotations

from travelogue.curation.mosaic.metrics import compute_mosaic_metrics
from travelogue.curation.mosaic.render_check import (
    compute_layout_render_error_rate,
    screen_pattern_render_ok,
)
from travelogue.curation.mosaic.runtime import MOSAIC_ROUTER_VERSION

from tests._golden.helpers import build_mixed_aspects_trip, plan_mosaic_screens


def test_mcs_patterns_render_chain_ok() -> None:
    buckets, aspects, assets = build_mixed_aspects_trip()
    chapters = plan_mosaic_screens(buckets, aspects, assets)
    m = compute_layout_render_error_rate(chapters, scope="mcs_unified")
    assert m["layoutRenderChecked"] >= 2
    assert m["layout.render.error_rate"] == 0.0


def test_mosaic_metrics_include_render_error_rate() -> None:
    buckets, aspects, assets = build_mixed_aspects_trip()
    chapters = plan_mosaic_screens(buckets, aspects, assets)
    metrics = compute_mosaic_metrics(chapters, mosaic_logs=[])
    assert metrics["layout.render.error_rate"] == 0.0


def test_portrait_2_landscape_2_has_css_binding() -> None:
    assert screen_pattern_render_ok("screen-portrait-2-landscape-2")


def test_mosaic_window_log_has_router_version() -> None:
    from travelogue.curation.mosaic.log import MosaicWindowLog

    raw = MosaicWindowLog(winner_pattern_id="screen-portrait-3").to_dict()
    assert raw["routerVersion"] == MOSAIC_ROUTER_VERSION
