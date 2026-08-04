"""Five- and six-slot layouts off when 5/6 not in enabled_window_sizes.

5/6 windows are enabled by default; these tests force a disabled config to verify
the gating mechanism still blocks them everywhere (MCS, legacy, pattern policy).
"""

from __future__ import annotations

from dataclasses import replace

from travelogue.config import get_config
from travelogue.layout_engine.mosaic.constants import (
    MOSAIC_5_PATTERN_IDS,
    PATTERN_MOSAIC_5_2P_3L_BALANCED,
    PATTERN_MOSAIC_5_MAIN_LAND_2P_2L,
)
from travelogue.layout_engine.mosaic.runtime import (
    reset_mosaic_config_override,
    set_mosaic_config_override,
)
from travelogue.layout_engine.planner.screen_planner import plan_screens_for_chapter

# Active 6-slot hero SKUs (LTN C3 pruned flat landscape/portrait-6 from MOSAIC_6 IDs).
_FORBIDDEN_SIX = frozenset(
    {
        "screen-mosaic-6-main-hero-plus-5",
        "screen-mosaic-5-main-hero-plus-4",
    }
)

_DISABLED_5_6 = (3, 4, 8, 9)


def test_legacy_landscape_run_skips_six_grid_when_disabled():
    off = replace(get_config().mosaic, enabled_window_sizes=_DISABLED_5_6)
    set_mosaic_config_override(off)
    try:
        ids = [f"l{i}" for i in range(6)]
        aspects = {aid: "landscape" for aid in ids}
        assets = {
            aid: {
                "id": aid,
                "aspectKind": "landscape",
                "width": 3000,
                "height": 1687,
                "takenAt": f"2025-06-01T10:0{i}:00+00:00",
            }
            for i, aid in enumerate(ids)
        }
        screens = plan_screens_for_chapter(
            ids,
            aspects,
            assets=assets,
            burst_seconds=60.0,
            chapter_id="ch-six-off",
            trip_photo_total=40,
        )
    finally:
        reset_mosaic_config_override()
    assert screens
    for sc in screens:
        assert sc["patternId"] not in _FORBIDDEN_SIX
        assert len(sc.get("slots") or []) != 6


def test_mosaic_pattern_policy_blocks_five_and_six_ids(lte_pattern_enabled):
    from travelogue.layout_engine.mosaic.lte_adapter import mosaic_pattern_disabled

    off = replace(get_config().mosaic, enabled_window_sizes=_DISABLED_5_6)
    for pid in MOSAIC_5_PATTERN_IDS:
        assert mosaic_pattern_disabled(pid, cfg=off)
    for pid in _FORBIDDEN_SIX:
        assert mosaic_pattern_disabled(pid, cfg=off)
    assert not mosaic_pattern_disabled("screen-landscape-4", cfg=off)

    # Restored default (5/6 enabled) must allow active hero SKUs again.
    on = replace(get_config().mosaic, enabled_window_sizes=(3, 4, 5, 6, 8, 9))
    for pid in _FORBIDDEN_SIX:
        assert not mosaic_pattern_disabled(pid, cfg=on)
    for pid in MOSAIC_5_PATTERN_IDS:
        assert not mosaic_pattern_disabled(pid, cfg=on)
    # LTN C3 · portrait-6 / non-EGA pruned flats stay disabled.
    # EGA PR-B · screen-landscape-6 is admitted when equal-grid admission is on.
    ega_off = replace(
        on,
        equal_grid_admission=replace(on.equal_grid_admission, enabled=False),
    )
    assert mosaic_pattern_disabled("screen-portrait-6", cfg=on)
    assert mosaic_pattern_disabled("screen-landscape-6", cfg=ega_off)
    assert not mosaic_pattern_disabled("screen-landscape-6", cfg=on)
    for pid in (PATTERN_MOSAIC_5_2P_3L_BALANCED, PATTERN_MOSAIC_5_MAIN_LAND_2P_2L):
        assert mosaic_pattern_disabled(pid, cfg=on)
