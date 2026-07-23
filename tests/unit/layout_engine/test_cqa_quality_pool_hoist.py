"""CQA AC-20 · build_quality_pool once per window (not per pattern)."""

from __future__ import annotations

from unittest.mock import patch

from travelogue.config.mosaic import MosaicConfig
from travelogue.layout_engine.mosaic.candidates import (
    generate_window_candidates_with_rejections,
)
from travelogue.layout_engine.quality_features import build_quality_pool


def test_quality_pool_built_once_per_window() -> None:
    cfg = MosaicConfig(
        enabled=True,
        lse_hungarian_assignment=True,
        lse_quality_unified=True,
    )
    # 4-up window with diverse aspects so multiple patterns remain orderable
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
