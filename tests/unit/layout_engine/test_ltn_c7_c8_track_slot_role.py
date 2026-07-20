"""LTN C7 track params + C8 slot-role penalties/gates."""

from __future__ import annotations

from dataclasses import replace

from travelogue.config import get_config
from travelogue.layout_contract.mosaic_track import (
    apply_mosaic_track,
    resolve_mosaic_track,
    track_params_for,
)
from travelogue.layout_engine.mosaic.runtime import planner_mosaic_window_sizes
from travelogue.layout_engine.mosaic.slot_role_penalties import (
    main_area_ratio_penalty,
    main_clone_in_sidebar_penalty,
    main_not_window_best_penalty,
)


def test_resolve_track_by_intent_and_kept():
    assert resolve_mosaic_track(kept_count=20, intent_mode="quick_share") == "quick_share"
    assert resolve_mosaic_track(kept_count=40, intent_mode="fine_craft") == "curated"
    assert resolve_mosaic_track(kept_count=120, intent_mode="fine_craft") == "archive"


def test_apply_track_sets_score_beat_and_dense_cap():
    base = get_config().mosaic
    curated = apply_mosaic_track(base, track_params_for("curated"))
    assert curated.track_id == "curated"
    assert curated.track_dense_collage_cap == 2
    assert curated.enable_size3_aux is False
    assert curated.lse_beat_profile == "classic_magazine"

    quick = apply_mosaic_track(base, track_params_for("quick_share"))
    assert quick.min_candidate_score == 0.40
    assert quick.track_dense_collage_cap == 1
    assert quick.lse_beat_profile == "flat"


def test_enable_size3_aux_appends_window_size():
    cfg = replace(get_config().mosaic, enabled=True, unified_mode=True, enable_size3_aux=True)
    sizes = planner_mosaic_window_sizes(cfg, density="balanced")
    assert 3 in sizes
    assert sizes[-1] == 3


def test_main_not_window_best_penalizes_weaker_main():
    screen = {
        "patternId": "screen-mosaic-5-main-hero-plus-4",
        "slots": [
            {"role": "main", "assetId": "weak"},
            {"role": "tile", "assetId": "strong"},
        ],
    }
    assets = {
        "weak": {
            "id": "weak",
            "quality": {"sharpness": 0.1},
            "width": 1600,
            "height": 900,
        },
        "strong": {
            "id": "strong",
            "quality": {"sharpness": 0.95},
            "width": 1600,
            "height": 900,
            "tags": ["person", "face"],
        },
    }
    assert main_not_window_best_penalty(screen, assets_by_id=assets) == 1.0


def test_main_clone_in_sidebar_same_burst():
    screen = {
        "patternId": "screen-mosaic-5-main-hero-plus-4",
        "slots": [
            {"role": "main", "assetId": "a0"},
            {"role": "tile", "assetId": "a1"},
        ],
    }
    assets = {
        "a0": {
            "id": "a0",
            "burstGroupId": "bg1",
            "takenAt": "2025-01-01T12:00:00Z",
            "width": 1600,
            "height": 900,
        },
        "a1": {
            "id": "a1",
            "burstGroupId": "bg1",
            "takenAt": "2025-01-01T12:00:02Z",
            "width": 900,
            "height": 1600,
        },
    }
    assert main_clone_in_sidebar_penalty(screen, assets_by_id=assets) == 1.0


def test_main_area_ratio_soft_for_main_portrait_3land():
    pen = main_area_ratio_penalty("screen-mosaic-5-main-portrait-3land")
    assert pen > 0.0
    assert pen < 1.0
    assert main_area_ratio_penalty("screen-mosaic-4-hero-70-sidebar") == 0.0
