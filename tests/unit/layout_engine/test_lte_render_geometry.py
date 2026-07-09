"""Render + mosaic log layout geometry integration (P16 P2)."""

from __future__ import annotations

import pytest

from tests._golden.helpers import build_mosaic_five_2p3l_window
from travelogue.config import MosaicConfig
from travelogue.layout_engine.mosaic.compose import pick_best_candidate
from travelogue.layout_engine.mosaic.constants import PATTERN_MOSAIC_5_2P3L_EQUAL
from travelogue.render.context import build_layout_screen


@pytest.mark.unit
def test_build_layout_screen_uses_solidified_grid_class() -> None:
    screen = {
        "patternId": PATTERN_MOSAIC_5_2P3L_EQUAL,
        "layoutGeometry": {
            "gridClass": "layout-screen__grid--mosaic-5-2p3l-equal",
            "stageAspect": "16:9",
            "templateVersion": 2,
        },
        "slots": [{"assetId": "a1", "slot": 0, "fit": "cover"}],
    }
    assets = {"a1": {"id": "a1", "width": 1200, "height": 1600, "displayFile": "a1.webp"}}
    ctx = build_layout_screen(screen, assets, meta_title="t", export_layout="web")
    assert ctx["gridClass"] == "layout-screen__grid--mosaic-5-2p3l-equal"
    assert "16 / 9" in ctx["screenStyle"]


@pytest.mark.unit
def test_mosaic_log_includes_template_metadata(lte_pattern_enabled) -> None:
    ids, aspects, assets_map = build_mosaic_five_2p3l_window()
    cfg = MosaicConfig(
        enabled=True,
        enabled_window_sizes=(5,),
        min_candidate_score=0.0,
        deterministic_strict=True,
    )
    pick = pick_best_candidate(
        ids,
        aspects,
        assets_map,
        cfg=cfg,
        window_size=5,
        trip_photo_total=40,
        burst_seconds=3600.0,
    )
    raw = pick.log.to_dict()
    assert pick.screen is not None
    assert pick.screen.get("layoutGeometry")
    assert raw.get("templateVersion") is not None
    assert raw.get("templateRegistryVersion")
