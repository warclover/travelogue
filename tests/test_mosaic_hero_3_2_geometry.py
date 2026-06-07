"""Geometry guard for weighted-track hero-3-2-plus-4 (Plate 63)."""

from __future__ import annotations

from dataclasses import replace

from travelogue.config import MosaicConfig
from travelogue.curation.mosaic.candidates import generate_window_candidates_with_rejections
from travelogue.curation.mosaic.constants import PATTERN_MOSAIC_5_HERO_3_2_PLUS_4
from travelogue.curation.mosaic.runtime import (
    reset_mosaic_config_override,
    set_mosaic_config_override,
)
from travelogue.curation.mosaic.scorer import score_candidate
from travelogue.curation.mosaic.slot_geometry import screen_slots_geometry_ok


def _five_landscapes():
    aspects = {}
    assets_map = {}
    asset_ids = []
    for i in range(5):
        aid = f"a{i}"
        asset_ids.append(aid)
        aspects[aid] = "landscape"
        assets_map[aid] = {
            "id": aid,
            "width": 3000,
            "height": 1687,
            "takenAt": f"2024-06-01T10:0{i}:00Z",
            "quality": {"sharpness": 0.8},
        }
    slots = [
        {"assetId": f"a{i}", "slot": i, "fit": "cover", "role": "main" if i == 0 else "landscape"}
        for i in range(5)
    ]
    screen = {"patternId": PATTERN_MOSAIC_5_HERO_3_2_PLUS_4, "slots": slots}
    return aspects, assets_map, asset_ids, screen


def test_all_landscape_hero_3_2_geometry_rejected_by_default():
    aspects, _, _, screen = _five_landscapes()
    assert screen_slots_geometry_ok(screen, aspects) is False


def test_all_landscape_hero_3_2_scorer_penalized():
    aspects, assets_map, _, screen = _five_landscapes()
    result = score_candidate(
        screen,
        aspects=aspects,
        assets_by_id=assets_map,
        cfg=MosaicConfig(),
        trip_photo_total=50,
    )
    assert result.penalties.get("hero_narrow_tiles", 0.0) > 0.0
    assert result.penalties.get("hero_slot_aspect", 0.0) > 0.0
    assert result.penalties.get("slot_geometry", 0.0) > 0.0


def test_hero_3_2_guard_rollback_restores_geometry_and_penalties():
    aspects, assets_map, asset_ids, screen = _five_landscapes()
    cfg = replace(MosaicConfig(), hero_weighted_geometry_guard=False)
    set_mosaic_config_override(cfg)
    try:
        assert screen_slots_geometry_ok(screen, aspects) is True
        result = score_candidate(
            screen,
            aspects=aspects,
            assets_by_id=assets_map,
            cfg=cfg,
            trip_photo_total=50,
        )
        assert result.penalties.get("hero_narrow_tiles", 0.0) == 0.0
        assert result.penalties.get("hero_slot_aspect", 0.0) == 0.0

        window = generate_window_candidates_with_rejections(
            asset_ids,
            aspects,
            assets_map,
            cfg=cfg,
        )
        hero = next(
            (c for c in window.candidates if c.pattern_id == PATTERN_MOSAIC_5_HERO_3_2_PLUS_4),
            None,
        )
        assert hero is not None
        assert hero.hard_valid is True
    finally:
        reset_mosaic_config_override()


def test_hero_3_2_guard_rejects_pure_landscape_window_candidate():
    aspects, assets_map, asset_ids, _ = _five_landscapes()
    window = generate_window_candidates_with_rejections(
        asset_ids,
        aspects,
        assets_map,
        cfg=MosaicConfig(),
    )
    hero = next(
        (c for c in window.candidates if c.pattern_id == PATTERN_MOSAIC_5_HERO_3_2_PLUS_4),
        None,
    )
    assert hero is not None
    assert hero.hard_valid is False
    assert any(
        r.get("templateId") == PATTERN_MOSAIC_5_HERO_3_2_PLUS_4
        and r.get("reason") == "geometry_invalid"
        for r in window.rejected
    )
