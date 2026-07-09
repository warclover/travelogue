"""Mixed-aspect MCS planning must never place portraits in wide grid cells."""

from __future__ import annotations

from dataclasses import replace

from tests._golden.helpers import build_mixed_aspects_trip, plan_mosaic_screens
from travelogue.config import get_config
from travelogue.layout_engine.mosaic.hook import drain_mosaic_logs
from travelogue.layout_engine.mosaic.slot_geometry import screen_slots_geometry_ok


def test_mixed_aspects_no_portrait_in_wide_cells() -> None:
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
        drain_mosaic_logs()
    finally:
        config_mod.get_config = orig

    screens = [s for ch in chapters for s in ch.get("screens") or []]
    patterns = {s.get("patternId") for s in screens}
    # 2×2 wide-grid patterns crop portraits — must not be emitted for mixed input.
    assert "screen-portrait-2-landscape-2" not in patterns
    assert "screen-portrait-4" not in patterns
    # Every emitted screen must pass the slot geometry guard (no portrait-in-wide).
    for s in screens:
        assert screen_slots_geometry_ok(s, aspects), s.get("patternId")
