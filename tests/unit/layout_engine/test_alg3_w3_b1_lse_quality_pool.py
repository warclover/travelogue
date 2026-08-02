"""ALG-V3 W3-B1 · quality_pool hoist gated only on lse_quality_unified."""

from __future__ import annotations

from unittest.mock import patch

from travelogue.config.mosaic import MosaicConfig
from travelogue.layout_engine.mosaic.candidates import (
    generate_window_candidates_with_rejections,
)
from travelogue.layout_engine.mosaic.scorer import score_candidate
from travelogue.layout_engine.quality_features import build_quality_pool


def _four_up() -> tuple[list[str], dict[str, str], dict[str, dict]]:
    asset_ids = ["a1", "a2", "a3", "a4"]
    aspects = {
        "a1": "landscape",
        "a2": "landscape",
        "a3": "portrait",
        "a4": "landscape",
    }
    assets_map = {
        aid: {
            "id": aid,
            "aspect": aspects[aid],
            "width": 1200 if aspects[aid] == "landscape" else 800,
            "height": 800 if aspects[aid] == "landscape" else 1200,
            "sharpness": 0.8,
        }
        for aid in asset_ids
    }
    return asset_ids, aspects, assets_map


def test_b1_candidates_hoist_without_hungarian() -> None:
    """Hole fix: unified=True ∧ hungarian=False still builds window pool once."""
    cfg = MosaicConfig(
        enabled=True,
        lse_hungarian_assignment=False,
        lse_quality_unified=True,
    )
    asset_ids, aspects, assets_map = _four_up()
    with patch(
        "travelogue.layout_engine.quality_features.build_quality_pool",
        wraps=build_quality_pool,
    ) as mocked:
        generate_window_candidates_with_rejections(
            asset_ids,
            aspects,  # type: ignore[arg-type]
            assets_map,
            cfg=cfg,
        )
        assert mocked.call_count == 1


def test_b1_both_flags_off_builds_zero() -> None:
    cfg = MosaicConfig(
        enabled=True,
        lse_hungarian_assignment=False,
        lse_quality_unified=False,
    )
    asset_ids, aspects, assets_map = _four_up()
    with patch(
        "travelogue.layout_engine.quality_features.build_quality_pool",
        wraps=build_quality_pool,
    ) as mocked:
        generate_window_candidates_with_rejections(
            asset_ids,
            aspects,  # type: ignore[arg-type]
            assets_map,
            cfg=cfg,
        )
        assert mocked.call_count == 0


def test_b1_score_candidate_reuses_passed_pool() -> None:
    cfg = MosaicConfig(enabled=True, lse_quality_unified=True)
    screen = {
        "patternId": "screen-mosaic-4-2x2",
        "slots": [
            {"assetId": "a1", "role": "main"},
            {"assetId": "a2"},
            {"assetId": "a3"},
            {"assetId": "a4"},
        ],
    }
    _ids, aspects, assets_map = _four_up()
    pool = build_quality_pool(list(assets_map.values()))
    with patch(
        "travelogue.layout_engine.quality_features.build_quality_pool",
        wraps=build_quality_pool,
    ) as mocked:
        for _ in range(3):
            score_candidate(
                screen,
                aspects=aspects,  # type: ignore[arg-type]
                assets_by_id=assets_map,
                cfg=cfg,
                quality_pool=pool,
            )
        assert mocked.call_count == 0


def test_b1_defaults_remain_off() -> None:
    cfg = MosaicConfig()
    assert cfg.lse_quality_unified is False
    assert cfg.lse_hungarian_assignment is False
