"""End-to-end mosaic planning with config enabled."""

from __future__ import annotations

from dataclasses import replace

from travelogue.config import get_config
from travelogue.curation.chapter_items import summarize_screen_patterns
from travelogue.curation.mosaic.hook import drain_mosaic_logs
from travelogue.curation.mosaic.metrics import mcs_unified_exposure_rate, mosaic5_exposure_rate

from tests._golden.helpers import build_mosaic_eligible_trip, plan_legacy_screens


def test_mosaic_enabled_increases_mosaic5_exposure(monkeypatch) -> None:
    buckets, aspects, assets = build_mosaic_eligible_trip()
    cfg = get_config()
    off = replace(cfg.mosaic, enabled=False)
    on = replace(
        cfg.mosaic,
        enabled=True,
        enabled_window_sizes=(3, 4, 5, 6),
        min_candidate_score=0.0,
    )
    monkeypatch.setattr(
        "travelogue.config.get_config",
        lambda: replace(cfg, mosaic=off),
    )
    drain_mosaic_logs()
    chapters_off = plan_legacy_screens(buckets, aspects, assets)
    rate_off = mosaic5_exposure_rate(chapters_off)

    monkeypatch.setattr(
        "travelogue.config.get_config",
        lambda: replace(cfg, mosaic=on),
    )
    drain_mosaic_logs()
    chapters_on = plan_legacy_screens(buckets, aspects, assets)
    logs = drain_mosaic_logs()
    rate_on = mosaic5_exposure_rate(chapters_on)

    assert rate_on >= rate_off
    counts = summarize_screen_patterns(chapters_on)
    assert any("mosaic-5" in pid for pid in counts)
    assert logs
    assert mcs_unified_exposure_rate(chapters_on) >= rate_on


def test_mosaic_metrics_from_logs() -> None:
    from travelogue.curation.mosaic.metrics import compute_mosaic_metrics

    chapters = [{"screens": [{"patternId": "screen-mosaic-5-main-hero-plus-4", "slots": []}]}]
    logs = [
        {"fallbackUsed": False, "winnerPatternId": "screen-mosaic-5-main-hero-plus-4"},
        {"fallbackUsed": True, "fallbackReason": "low_score"},
    ]
    m = compute_mosaic_metrics(chapters, mosaic_logs=logs)
    assert m["mosaic5ExposureRate"] == 1.0
    assert m["mosaicFallbackRate"] == 0.5
    assert m["layout.mosaic_v2.low_score_fallback_rate"] == 0.5
