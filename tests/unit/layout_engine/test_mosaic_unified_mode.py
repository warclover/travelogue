"""DESIGN §12.1 · unified_mode limits MCS to 5-slot windows when false."""

from __future__ import annotations

from dataclasses import replace

from tests._golden.helpers import (
    build_mixed_aspects_trip,
    build_mosaic_eligible_trip,
    plan_legacy_screens,
    plan_mosaic_screens,
)
from travelogue.config import get_config
from travelogue.layout_engine.mosaic.hook import drain_mosaic_logs
from travelogue.layout_engine.mosaic.metrics import mcs_unified_exposure_rate
from travelogue.layout_engine.mosaic.runtime import effective_mosaic_window_sizes


def test_effective_sizes_unified_off_is_five_only() -> None:
    cfg = replace(get_config().mosaic, enabled=True, unified_mode=False)
    assert effective_mosaic_window_sizes(cfg) == (5,)


def test_unified_off_skips_four_window_mcs_on_mixed_aspects() -> None:
    buckets, aspects, assets = build_mixed_aspects_trip()
    base = get_config()
    cfg = replace(
        base,
        mosaic=replace(
            base.mosaic,
            enabled=True,
            unified_mode=False,
            enabled_window_sizes=(3, 4, 5, 6),
            min_candidate_score=0.0,
        ),
    )
    import travelogue.config as config_mod

    orig = config_mod.get_config
    config_mod.get_config = lambda: cfg  # type: ignore[assignment]
    try:
        drain_mosaic_logs()
        chapters = plan_legacy_screens(buckets, aspects, assets)
        logs = drain_mosaic_logs()
    finally:
        config_mod.get_config = orig

    patterns = {s.get("patternId") for ch in chapters for s in ch.get("screens") or []}
    assert "screen-portrait-2-landscape-2" not in patterns
    assert logs == []


def test_unified_on_mosaic5_still_works() -> None:
    buckets, aspects, assets = build_mosaic_eligible_trip()
    base = get_config()
    cfg = replace(
        base,
        mosaic=replace(
            base.mosaic,
            enabled=True,
            unified_mode=True,
            min_candidate_score=0.0,
        ),
    )
    import travelogue.config as config_mod

    orig = config_mod.get_config
    config_mod.get_config = lambda: cfg  # type: ignore[assignment]
    try:
        chapters = plan_mosaic_screens(buckets, aspects, assets)
    finally:
        config_mod.get_config = orig

    assert mcs_unified_exposure_rate(chapters) >= 0.3
