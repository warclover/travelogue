"""MCS hook skips window sizes with no candidates (no spurious fallback logs)."""

from __future__ import annotations

from dataclasses import replace

from travelogue.config import get_config
from travelogue.curation.mosaic.hook import drain_mosaic_logs
from travelogue.curation.mosaic.metrics import (
    compute_mosaic_metrics,
    mcs_unified_exposure_rate,
)

from tests._golden.helpers import build_mixed_aspects_trip, plan_mosaic_screens


def test_mixed_aspects_no_spurious_size4_fallback() -> None:
    buckets, aspects, assets = build_mixed_aspects_trip()
    cfg = get_config()
    on = replace(
        cfg.mosaic,
        enabled=True,
        enabled_window_sizes=(3, 4, 5, 6),
        min_candidate_score=0.0,
    )
    import travelogue.config as config_mod

    orig = config_mod.get_config
    config_mod.get_config = lambda: replace(cfg, mosaic=on)  # type: ignore[assignment]
    try:
        drain_mosaic_logs()
        chapters = plan_mosaic_screens(buckets, aspects, assets)
        logs = drain_mosaic_logs()
    finally:
        config_mod.get_config = orig

    m = compute_mosaic_metrics(chapters, mosaic_logs=logs)
    assert m["mosaicFallbackRate"] == 0.0
    assert not any(lg.get("fallbackReason") == "no_candidates" for lg in logs)
    assert mcs_unified_exposure_rate(chapters) == 1.0
    patterns = {s.get("patternId") for ch in chapters for s in ch.get("screens") or []}
    assert "screen-portrait-2-landscape-2" in patterns
