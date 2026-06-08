"""P17 W3b CAP-02/03/04 unit tests."""

from __future__ import annotations

from dataclasses import replace

import travelogue.curation.screen_planner  # noqa: F401

from travelogue.config import AppConfig, MosaicConfig
from travelogue.config.layout import LayoutConfig, LayoutStrategyCapabilitiesConfig, LayoutStrategyEngineConfig
from travelogue.curation.mosaic.scorer import score_candidate
from travelogue.layout_engine.adapter import mosaic_config_from_pack
from travelogue.layout_engine.beat import beat_score_multiplier
from travelogue.layout_engine.features import cover_focal_retention, salient_crop_penalty
from travelogue.layout_engine.registry import get_strategy_pack
from travelogue.layout_engine.render_binding import cover_rules_use_focal_variables
from travelogue.layout_engine.tone_adjacency import adjacent_tone_penalty


def test_salient_retention_prefers_visible_focal() -> None:
    assert cover_focal_retention(1.0, 0.75, focal_x=0.5, focal_y=0.5) == 1.0
    assert cover_focal_retention(0.5, 2.0, focal_x=0.9, focal_y=0.5) < 0.5


def test_salient_crop_penalty_high_when_focal_clipped() -> None:
    screen = {
        "slots": [
            {
                "assetId": "a1",
                "fit": "cover",
                "displayAspect": 0.5,
            }
        ]
    }
    assets = {
        "a1": {
            "width": 2000,
            "height": 1000,
            "focalPoint": {"x": 0.95, "y": 0.5},
            "tags": ["person"],
        }
    }
    assert salient_crop_penalty(screen, assets) > 0.4


def test_beat_classic_magazine_boosts_opening_hero() -> None:
    mul = beat_score_multiplier(
        "screen-mosaic-5-main-hero-plus-4",
        screen_index=0,
        chapter_screen_count=8,
        beat_profile="classic_magazine",
    )
    assert mul > 1.0


def test_adjacent_tone_penalty_on_large_delta_e() -> None:
    prev = {"slots": [{"assetId": "a1"}]}
    cand = {"slots": [{"assetId": "a2"}]}
    assets = {
        "a1": {"dominantTone": "#101010", "meanLuma": 0.5},
        "a2": {"dominantTone": "#f0f0f0", "meanLuma": 0.5},
    }
    assert adjacent_tone_penalty(prev, cand, assets) >= 0.45


def test_mosaic_config_injects_lse_capability_flags() -> None:
    cfg = AppConfig(
        layout=LayoutConfig(
            strategy_engine=LayoutStrategyEngineConfig(
                enabled=True,
                capabilities=LayoutStrategyCapabilitiesConfig(
                    saliency_scoring=True,
                    tone_harmony=True,
                    beat_profile="classic_magazine",
                ),
            )
        )
    )
    pack = get_strategy_pack("lse-default-2026-06")
    mc = mosaic_config_from_pack(cfg, pack)
    assert mc.lse_saliency_scoring is True
    assert mc.lse_tone_harmony is True
    assert mc.lse_beat_profile == "classic_magazine"
    assert mc.penalties.get("salient_crop", 0) > 0


def test_score_candidate_applies_beat_when_configured() -> None:
    cfg = replace(
        MosaicConfig(),
        lse_beat_profile="classic_magazine",
    )
    screen = {
        "patternId": "screen-mosaic-5-main-hero-plus-4",
        "slots": [{"assetId": "a1", "role": "main", "slot": 0}],
    }
    aspects = {"a1": "landscape"}
    assets = {
        "a1": {
            "width": 2400,
            "height": 1600,
            "quality": {"sharpness": 0.8},
            "focalPoint": {"x": 0.5, "y": 0.5},
        }
    }
    flat = score_candidate(
        screen,
        aspects=aspects,
        assets_by_id=assets,
        cfg=replace(cfg, lse_beat_profile="flat"),
        chapter_screen_index=0,
    )
    boosted = score_candidate(
        screen,
        aspects=aspects,
        assets_by_id=assets,
        cfg=cfg,
        chapter_screen_index=0,
    )
    assert boosted.total >= flat.total


def test_journal_screens_cover_rules_bind_focal_vars() -> None:
    violations = cover_rules_use_focal_variables()
    assert violations == []
