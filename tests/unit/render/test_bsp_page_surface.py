"""BSP page surface · content rail, viewport-fit, full-frame fit (PRD-页面优化)."""

from __future__ import annotations

import pytest

from travelogue.curation.asset_subject import full_frame_fit_for_asset
from travelogue.layout_engine.mosaic.constants import PATTERN_FULL_FRAME
from travelogue.layout_engine.planner.screen_planner import _fits_for_screen
from travelogue.render.context import (
    _asset_aspect_ratio_float,
    _presentation_tier,
    build_layout_screen,
)


@pytest.mark.unit
def test_full_frame_fits_cover_for_landscape() -> None:
    assets = {"a1": {"id": "a1", "width": 3000, "height": 2000}}
    fits = _fits_for_screen(PATTERN_FULL_FRAME, ["a1"], assets_map=assets)
    assert fits == ["cover"]


@pytest.mark.unit
def test_full_frame_fit_landscape_person_tag_still_cover() -> None:
    asset = {
        "id": "sea1",
        "width": 5769,
        "height": 3245,
        "tags": ["person", "face"],
        "quality": {"faceRatio": 0.1083},
    }
    assert full_frame_fit_for_asset(asset) == "cover"


@pytest.mark.unit
def test_full_frame_fit_portrait_person_contain() -> None:
    asset = {"id": "p1", "width": 1200, "height": 1600, "tags": ["person"]}
    assert full_frame_fit_for_asset(asset) == "contain"


@pytest.mark.unit
def test_full_frame_fits_contain_for_portrait_person() -> None:
    assets = {"p1": {"id": "p1", "width": 2000, "height": 3000, "tags": ["person"]}}
    fits = _fits_for_screen(PATTERN_FULL_FRAME, ["p1"], assets_map=assets)
    assert fits == ["contain"]


@pytest.mark.unit
def test_full_frame_landscape_viewport_fit() -> None:
    assets = {
        "l1": {
            "id": "l1",
            "width": 3000,
            "height": 2000,
            "displayFile": "assets/l1-w800.webp",
        }
    }
    screen = {
        "patternId": PATTERN_FULL_FRAME,
        "slots": [{"assetId": "l1", "slot": 0, "fit": "contain"}],
    }
    ctx = build_layout_screen(screen, assets, meta_title="Test", export_layout="web")
    assert ctx.get("hasViewportFit") is True
    assert "16 / 9" not in ctx["screenStyle"]
    assert "--screen-fit-ar:" in ctx["screenStyle"]
    assert ctx["slots"][0]["fit"] == "cover"
    assert ctx["slots"][0].get("hasBlurFill") is not True


@pytest.mark.unit
def test_full_frame_person_contain_native_stage_no_blur() -> None:
    assets = {
        "p1": {
            "id": "p1",
            "width": 2000,
            "height": 3000,
            "tags": ["person"],
            "displayFile": "assets/p1-w800.webp",
        }
    }
    screen = {
        "patternId": PATTERN_FULL_FRAME,
        "slots": [{"assetId": "p1", "slot": 0, "fit": "cover"}],
    }
    ctx = build_layout_screen(screen, assets, meta_title="Test", export_layout="web")
    assert ctx.get("hasViewportFit") is not True
    assert "2000 / 3000" in ctx["screenStyle"]
    slot = ctx["slots"][0]
    assert slot["fit"] == "contain"
    assert slot.get("hasBlurFill") is not True


@pytest.mark.unit
def test_wide_single_landscape_uses_native_aspect_not_viewport_fit() -> None:
    """Wide tier (2.0–2.8) must not use ultra-wide viewport-fit stage."""
    assets = {
        "w1": {
            "id": "w1",
            "width": 4200,
            "height": 1800,
            "displayFile": "assets/w1-w800.webp",
        }
    }
    screen = {
        "patternId": "screen-landscape-1",
        "slots": [{"assetId": "w1", "slot": 0, "fit": "cover"}],
    }
    ctx = build_layout_screen(screen, assets, meta_title="Test", export_layout="web")
    assert ctx.get("hasViewportFit") is not True
    assert ctx.get("hasTierUltra") is not True
    assert "4200 / 1800" in ctx["screenStyle"]
    assert "--screen-fit-ar:" not in ctx["screenStyle"]


@pytest.mark.unit
def test_ultra_wide_single_landscape_tier() -> None:
    assets = {
        "u1": {
            "id": "u1",
            "width": 3000,
            "height": 680,
            "displayFile": "assets/u1-w800.webp",
        }
    }
    screen = {
        "patternId": "screen-landscape-1",
        "slots": [{"assetId": "u1", "slot": 0, "fit": "cover"}],
    }
    ctx = build_layout_screen(screen, assets, meta_title="Test", export_layout="web")
    assert ctx.get("hasTierUltra") is True
    assert ctx.get("hasViewportFit") is True
    assert _presentation_tier(_asset_aspect_ratio_float(assets["u1"])) == "ultra"


@pytest.mark.unit
def test_viewport_fit_css_shrinks_width_when_vh_caps() -> None:
    from travelogue.paths import JOURNAL_SCREENS_CSS

    css = JOURNAL_SCREENS_CSS.read_text(encoding="utf-8")
    assert "width: min(" in css
    assert "100dvh * var(--screen-weight" in css
    assert "var(--screen-fit-ar" in css


@pytest.mark.unit
def test_standard_full_frame_viewport_fit_preserves_native_ar() -> None:
    assets = {
        "s1": {
            "id": "s1",
            "nativeWidth": 3000,
            "nativeHeight": 2000,
            "width": 1600,
            "height": 1068,
            "displayFile": "assets/s1-w800.webp",
        }
    }
    screen = {
        "patternId": PATTERN_FULL_FRAME,
        "slots": [{"assetId": "s1", "slot": 0, "fit": "cover"}],
    }
    ctx = build_layout_screen(screen, assets, meta_title="Test", export_layout="web")
    assert ctx.get("hasViewportFit") is True
    assert ctx.get("hasTierUltra") is not True
    assert "--screen-fit-ar: 1.500000" in ctx["screenStyle"]


@pytest.mark.unit
def test_folio_plate_portrait_person_renders_contain() -> None:
    """Chapter opener plate keeps slot contain fit from portrait-1 planning."""
    assets = {
        "p1": {
            "id": "p1",
            "nativeWidth": 2848,
            "nativeHeight": 4256,
            "width": 2400,
            "height": 3587,
            "tags": ["person", "face"],
            "displayFile": "assets/p1-w800.webp",
        }
    }
    screen = {
        "patternId": "screen-portrait-1",
        "slots": [{"assetId": "p1", "slot": 0, "fit": "contain"}],
    }
    ctx = build_layout_screen(
        screen,
        assets,
        meta_title="Test",
        export_layout="web",
        folio_lite=True,
        is_plate=True,
        screen_index=1,
        chapter_index="04",
        featured_asset_ids=frozenset({"p1"}),
    )
    assert ctx["patternId"] == "screen-plate"
    assert ctx.get("isPlate") is True
    assert ctx["slots"][0]["fit"] == "contain"
    assert "2848 / 4256" in ctx["screenStyle"]
    assert ctx.get("isFeatured") is True


@pytest.mark.unit
def test_journal_screens_css_has_bsp_tokens() -> None:
    from travelogue.paths import JOURNAL_SCREENS_CSS

    css = JOURNAL_SCREENS_CSS.read_text(encoding="utf-8")
    assert "--content-rail" in css
    assert "layout-screen--viewport-fit" in css
    assert "layout-screen--tier-ultra" in css
    assert "layout-screen--plate" in css
    assert '[data-featured="true"]' in css
