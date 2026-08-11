"""End-to-end mosaic planning with config enabled."""

from __future__ import annotations

from dataclasses import replace

from tests._golden.helpers import _asset, plan_legacy_screens
from travelogue.config import get_config
from travelogue.curation.chapter_items import summarize_screen_patterns
from travelogue.layout_engine.mosaic.hook import drain_mosaic_logs
from travelogue.layout_engine.mosaic.metrics import mcs_unified_exposure_rate, mosaic5_exposure_rate


def _build_mosaic_eligible_trip():
    """36 assets (6×6), each bucket 2 portraits + 4 landscapes.

    After per-chapter hero extraction a mixed-orientation mosaic window survives
    (mosaic-6-main-hero-plus-5), so mosaic-enabled planning produces real MCS
    windows. Pure-portrait runs no longer route through mosaic (pair-first
    priority), so an all-portrait prefix fixture would yield zero mosaic
    activity.
    """
    assets: list[dict] = []
    aspects: dict[str, str] = {}
    buckets: list[list[str]] = []
    for b in range(6):
        bucket: list[str] = []
        for i in range(6):
            idx = b * 6 + i
            aid = f"m{idx:03d}"
            kind = "portrait" if i < 2 else "landscape"
            assets.append(
                _asset(
                    aid,
                    900 if kind == "portrait" else 2000,
                    1600 if kind == "portrait" else 1200,
                    offset_hours=float(idx) * 0.001,
                    sharpness=0.8,
                )
            )
            aspects[aid] = assets[-1]["aspectKind"]
            bucket.append(aid)
        buckets.append(bucket)
    return buckets, aspects, assets


def test_mosaic_enabled_increases_mosaic5_exposure(monkeypatch, lte_pattern_enabled) -> None:
    """GOLDEN-BUMP-JUSTIFICATION: isolate from local config.yaml dogfood cohort;
    start from AppConfig() product defaults so MCS on/off exposure is comparable.
    """
    from travelogue.config.app import AppConfig
    from travelogue.config.mosaic import mosaic_from_dict

    buckets, aspects, assets = _build_mosaic_eligible_trip()
    # Avoid local dogfood template_experiments / clone gates poisoning the delta.
    base = replace(
        AppConfig(),
        mosaic=replace(
            mosaic_from_dict({}),
            enabled=True,
            enabled_window_sizes=(3, 4, 5, 6),
            min_candidate_score=0.0,
        ),
        layout=get_config().layout,
    )
    off = replace(base.mosaic, enabled=False)
    on = replace(
        base.mosaic,
        enabled=True,
        enabled_window_sizes=(3, 4, 5, 6),
        min_candidate_score=0.0,
    )
    monkeypatch.setattr(
        "travelogue.config.get_config",
        lambda: replace(base, mosaic=off),
    )
    drain_mosaic_logs()
    chapters_off = plan_legacy_screens(buckets, aspects, assets)
    rate_off = mosaic5_exposure_rate(chapters_off)

    monkeypatch.setattr(
        "travelogue.config.get_config",
        lambda: replace(base, mosaic=on),
    )
    drain_mosaic_logs()
    chapters_on = plan_legacy_screens(buckets, aspects, assets)
    logs = drain_mosaic_logs()
    rate_on = mosaic5_exposure_rate(chapters_on)

    assert rate_on >= rate_off
    counts = summarize_screen_patterns(chapters_on)
    assert logs
    assert counts
    assert mcs_unified_exposure_rate(chapters_on) >= mcs_unified_exposure_rate(chapters_off)


def test_mosaic_metrics_from_logs() -> None:
    from travelogue.layout_engine.mosaic.metrics import compute_mosaic_metrics

    chapters = [{"screens": [{"patternId": "screen-mosaic-5-main-hero-plus-4", "slots": []}]}]
    logs = [
        {"fallbackUsed": False, "winnerPatternId": "screen-mosaic-5-main-hero-plus-4"},
        {"fallbackUsed": True, "fallbackReason": "low_score"},
    ]
    m = compute_mosaic_metrics(chapters, mosaic_logs=logs)
    assert m["mosaic5ExposureRate"] == 1.0
    assert m["mosaicFallbackRate"] == 0.5
    assert m["layout.mosaic_v2.low_score_fallback_rate"] == 0.5
