"""W3: collage routing + full-frame blurred fill (AC-P16-18)."""

from __future__ import annotations

import pytest

from travelogue.config import AppConfig
from travelogue.config.layout import LayoutConfig, LayoutTemplateEngineConfig
from travelogue.curation.collage_routing import collage_routing_enabled, single_asset_screen_pattern
from travelogue.curation.mosaic.constants import PATTERN_FULL_FRAME
from travelogue.curation.screen_planner import _fits_for_screen, _make_screen
from travelogue.render.context import build_layout_screen


@pytest.mark.unit
def test_collage_routes_to_full_frame() -> None:
    cfg = AppConfig(
        layout=LayoutConfig(
            template_engine=LayoutTemplateEngineConfig(exclude_collage_from_mosaic=True)
        )
    )
    assert collage_routing_enabled() or cfg.layout.template_engine.exclude_collage_from_mosaic
    assets = {"c1": {"id": "c1", "mediaClass": "collage"}}
    out = single_asset_screen_pattern("screen-landscape-1", "c1", assets)
    assert out == PATTERN_FULL_FRAME


@pytest.mark.unit
def test_collage_routing_respects_disable_flag(monkeypatch) -> None:
    monkeypatch.setattr(
        "travelogue.curation.collage_routing.get_config",
        lambda: AppConfig(
            layout=LayoutConfig(
                template_engine=LayoutTemplateEngineConfig(exclude_collage_from_mosaic=False)
            )
        ),
    )
    assets = {"c1": {"id": "c1", "mediaClass": "collage"}}
    assert single_asset_screen_pattern("screen-portrait-1", "c1", assets) == "screen-portrait-1"


@pytest.mark.unit
def test_make_screen_collage_single_uses_full_frame(monkeypatch) -> None:
    monkeypatch.setattr(
        "travelogue.curation.collage_routing.get_config",
        lambda: AppConfig(
            layout=LayoutConfig(
                template_engine=LayoutTemplateEngineConfig(exclude_collage_from_mosaic=True)
            )
        ),
    )
    assets = {"c1": {"id": "c1", "mediaClass": "collage", "width": 1200, "height": 800}}
    screen = _make_screen(
        "screen-landscape-1",
        ["c1"],
        screen_id="s1",
        assets_map=assets,
    )
    assert screen["patternId"] == PATTERN_FULL_FRAME
    assert screen["slots"][0]["fit"] == "contain"


@pytest.mark.unit
def test_full_frame_render_blurred_fill() -> None:
    assets = {
        "c1": {
            "id": "c1",
            "mediaClass": "collage",
            "width": 1200,
            "height": 800,
            "displayFile": "assets/c1-w800.webp",
        }
    }
    screen = {
        "patternId": PATTERN_FULL_FRAME,
        "slots": [{"assetId": "c1", "slot": 0, "fit": "contain"}],
    }
    ctx = build_layout_screen(
        screen,
        assets,
        meta_title="Test",
        export_layout="web",
    )
    assert ctx["layoutHint"] == "full-frame"
    assert ctx["hasLayoutHint"] is True
    assert "16 / 9" in ctx["screenStyle"]
    slot = ctx["slots"][0]
    assert slot.get("hasBlurFill") is True
    assert slot.get("blurSrc") == "assets/c1-w800.webp"


@pytest.mark.unit
def test_full_frame_fits_contain() -> None:
    fits = _fits_for_screen(PATTERN_FULL_FRAME, ["a1"])
    assert fits == ["contain"]


@pytest.mark.unit
def test_collage_never_groups_with_photo_in_planner(monkeypatch) -> None:
    monkeypatch.setattr(
        "travelogue.curation.collage_routing.get_config",
        lambda: AppConfig(
            layout=LayoutConfig(
                template_engine=LayoutTemplateEngineConfig(exclude_collage_from_mosaic=True)
            )
        ),
    )
    from travelogue.curation.screen_planner import plan_screens_for_chapter

    assets_map = {
        "p1": {"id": "p1", "mediaClass": "photo", "width": 1200, "height": 1600},
        "c1": {"id": "c1", "mediaClass": "collage", "width": 1600, "height": 800},
    }
    aspects = {"p1": "portrait", "c1": "landscape"}
    screens = plan_screens_for_chapter(
        ["c1", "p1"],
        aspects,
        assets=assets_map,
        trip_photo_total=2,
        chapter_id="ch-01",
        enable_mosaic=False,
    )
    collage_screens = [s for s in screens if any(sl.get("assetId") == "c1" for sl in s.get("slots") or [])]
    assert len(collage_screens) == 1
    assert collage_screens[0]["patternId"] == PATTERN_FULL_FRAME
    assert len(collage_screens[0]["slots"]) == 1
