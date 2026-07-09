"""Blurred letterbox fill — decision matrix and render integration."""

from __future__ import annotations

import pytest

from travelogue.layout_engine.mosaic.constants import PATTERN_FULL_FRAME
from travelogue.render.blur_fill import (
    letterbox_expected,
    resolve_stage_aspect_ratio,
    should_blur_fill_slot,
    uses_intrinsic_contain_layout,
)
from travelogue.render.context import build_layout_screen


@pytest.mark.unit
def test_letterbox_expected_when_aspect_mismatch() -> None:
    assert letterbox_expected(16 / 9, 1.0) is True
    assert letterbox_expected(1.0, 1.0) is False
    assert letterbox_expected(1.0, 0.98) is False


@pytest.mark.unit
def test_intrinsic_contain_portrait_one_web_off() -> None:
    assert not uses_intrinsic_contain_layout(
        pattern_id="screen-portrait-1",
        layout_hint=None,
        n_slots=1,
        export_layout="web",
        is_plate=False,
    )


@pytest.mark.unit
def test_intrinsic_contain_portrait_one_mobile_off() -> None:
    assert not uses_intrinsic_contain_layout(
        pattern_id="screen-portrait-1",
        layout_hint=None,
        n_slots=1,
        export_layout="mobile",
        is_plate=False,
    )


@pytest.mark.unit
def test_person_grid_eight_not_intrinsic() -> None:
    assert not uses_intrinsic_contain_layout(
        pattern_id="screen-portrait-grid-8",
        layout_hint="person-grid-8",
        n_slots=8,
        export_layout="web",
        is_plate=False,
    )


@pytest.mark.unit
def test_full_frame_person_contain_native_stage_no_blur() -> None:
    """Portrait stage matches asset — contain fills edge-to-edge, no bands."""
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
    slot = ctx["slots"][0]
    assert slot["fit"] == "contain"
    assert "2000 / 3000" in ctx["screenStyle"]
    assert slot.get("hasBlurFill") is not True


@pytest.mark.unit
def test_full_frame_person_contain_wide_stage_blur() -> None:
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
        "layoutGeometry": {"stageAspect": "16:9"},
        "slots": [{"assetId": "p1", "slot": 0, "fit": "contain"}],
    }
    ctx = build_layout_screen(screen, assets, meta_title="Test", export_layout="web")
    assert ctx["slots"][0].get("hasBlurFill") is True


@pytest.mark.unit
def test_full_frame_landscape_cover_no_blur() -> None:
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
    assert ctx["slots"][0]["fit"] == "cover"
    assert ctx["slots"][0].get("hasBlurFill") is not True


@pytest.mark.unit
def test_square_one_wide_stage_blur() -> None:
    """Square image in fixed 16:9 stage (user screenshot case)."""
    assets = {
        "sq": {
            "id": "sq",
            "width": 1200,
            "height": 1200,
            "displayFile": "assets/sq-w800.webp",
        }
    }
    screen = {
        "patternId": "screen-square-1",
        "layoutGeometry": {"stageAspect": "16:9", "gridClass": "layout-screen__grid--1col"},
        "slots": [{"assetId": "sq", "slot": 0, "fit": "contain"}],
    }
    ctx = build_layout_screen(screen, assets, meta_title="Test", export_layout="web")
    assert ctx["slots"][0].get("hasBlurFill") is True


@pytest.mark.unit
def test_square_one_native_stage_no_blur() -> None:
    assets = {
        "sq": {
            "id": "sq",
            "width": 1200,
            "height": 1200,
            "displayFile": "assets/sq-w800.webp",
        }
    }
    screen = {
        "patternId": "screen-square-1",
        "slots": [{"assetId": "sq", "slot": 0, "fit": "contain"}],
    }
    ctx = build_layout_screen(screen, assets, meta_title="Test", export_layout="web")
    assert ctx["slots"][0].get("hasBlurFill") is not True


@pytest.mark.unit
def test_portrait_one_contain_web_blur_for_vh_cap_bands() -> None:
    assets = {
        "p1": {
            "id": "p1",
            "width": 2858,
            "height": 4000,
            "tags": ["person"],
            "displayFile": "assets/p1-w800.webp",
        }
    }
    screen = {
        "patternId": "screen-portrait-1",
        "slots": [{"assetId": "p1", "slot": 0, "fit": "contain"}],
    }
    ctx = build_layout_screen(screen, assets, meta_title="Test", export_layout="web")
    assert ctx["slots"][0].get("hasBlurFill") is True


@pytest.mark.unit
def test_portrait_one_contain_mobile_native_stage_no_blur() -> None:
    assets = {
        "p1": {
            "id": "p1",
            "width": 800,
            "height": 1200,
            "tags": ["person"],
            "displayFile": "assets/p1-w800.webp",
        }
    }
    screen = {
        "patternId": "screen-portrait-1",
        "slots": [{"assetId": "p1", "slot": 0, "fit": "contain"}],
    }
    ctx = build_layout_screen(screen, assets, meta_title="Test", export_layout="mobile")
    assert ctx["slots"][0].get("hasBlurFill") is not True


@pytest.mark.unit
def test_portrait_one_contain_mobile_forced_wide_stage_blur() -> None:
    assets = {
        "p1": {
            "id": "p1",
            "width": 800,
            "height": 1200,
            "tags": ["person"],
            "displayFile": "assets/p1-w800.webp",
        }
    }
    screen = {
        "patternId": "screen-portrait-1",
        "layoutGeometry": {"stageAspect": "16:9"},
        "slots": [{"assetId": "p1", "slot": 0, "fit": "contain"}],
    }
    ctx = build_layout_screen(screen, assets, meta_title="Test", export_layout="mobile")
    assert ctx["slots"][0].get("hasBlurFill") is True


@pytest.mark.unit
def test_folio_plate_contain_web_blur() -> None:
    assets = {
        "p1": {
            "id": "p1",
            "nativeWidth": 2848,
            "nativeHeight": 4256,
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
    )
    assert ctx["slots"][0].get("hasBlurFill") is True


@pytest.mark.unit
def test_person_grid_eight_contain_blur_per_slot() -> None:
    assets = {
        f"p{i}": {
            "id": f"p{i}",
            "width": 800,
            "height": 1200,
            "tags": ["person"],
            "displayFile": f"assets/p{i}-w800.webp",
        }
        for i in range(8)
    }
    screen = {
        "patternId": "screen-portrait-grid-8",
        "layoutHint": "person-grid-8",
        "slots": [{"assetId": f"p{i}", "slot": i, "fit": "contain"} for i in range(8)],
    }
    ctx = build_layout_screen(screen, assets, meta_title="Test", export_layout="web")
    assert all(s.get("hasBlurFill") is True for s in ctx["slots"])


@pytest.mark.unit
def test_portrait_pair_contain_no_blur() -> None:
    assets = {
        "p1": {"id": "p1", "width": 800, "height": 1200, "tags": ["person"]},
        "p2": {"id": "p2", "width": 800, "height": 1200, "tags": ["person"]},
    }
    screen = {
        "patternId": "screen-portrait-2",
        "layoutHint": "person-pair",
        "slots": [
            {"assetId": "p1", "slot": 0, "fit": "contain"},
            {"assetId": "p2", "slot": 1, "fit": "contain"},
        ],
    }
    ctx = build_layout_screen(screen, assets, meta_title="Test", export_layout="web")
    assert ctx["slots"][0].get("hasBlurFill") is not True
    assert ctx["slots"][1].get("hasBlurFill") is not True


@pytest.mark.unit
def test_intrinsic_contain_portrait_row_editorial_hint() -> None:
    assert uses_intrinsic_contain_layout(
        pattern_id="screen-portrait-3-editorial",
        layout_hint="portrait-row-editorial",
        n_slots=3,
        export_layout="web",
        is_plate=False,
    )


@pytest.mark.unit
def test_portrait_row_editorial_contain_no_blur() -> None:
    assets = {
        f"p{i}": {"id": f"p{i}", "width": 800, "height": 1200, "tags": ["person"]}
        for i in range(3)
    }
    screen = {
        "patternId": "screen-portrait-3-editorial",
        "layoutHint": "portrait-row-editorial",
        "slots": [
            {"assetId": f"p{i}", "slot": i, "fit": "contain"} for i in range(3)
        ],
    }
    ctx = build_layout_screen(screen, assets, meta_title="Test", export_layout="web")
    assert ctx["layoutHint"] == "portrait-row-editorial"
    assert ctx["patternId"] == "screen-portrait-3-editorial"
    assert "aspect-ratio" not in (ctx.get("screenStyle") or "")
    assert all(s.get("hasBlurFill") is not True for s in ctx["slots"])


@pytest.mark.unit
def test_full_frame_mobile_blurred_fill_preserved() -> None:
    assets = {
        "c1": {
            "id": "c1",
            "tags": ["person"],
            "width": 800,
            "height": 1200,
            "nativeWidth": 800,
            "nativeHeight": 1200,
            "displayFile": "assets/c1-w800.webp",
        }
    }
    screen = {
        "patternId": PATTERN_FULL_FRAME,
        "layoutGeometry": {"stageAspect": "16:9", "gridClass": "layout-screen__grid--1col"},
        "slots": [{"assetId": "c1", "slot": 0, "fit": "contain"}],
    }
    ctx = build_layout_screen(screen, assets, meta_title="Test", export_layout="mobile")
    assert ctx["slots"][0].get("hasBlurFill") is True


@pytest.mark.unit
def test_resolve_stage_aspect_from_geometry() -> None:
    ar = resolve_stage_aspect_ratio(
        layout_geo={"stageAspect": "16:9"},
        viewport_fit=False,
        screen_aspect_css=None,
        skip_stage_aspect=False,
    )
    assert ar == pytest.approx(16 / 9)


@pytest.mark.unit
def test_should_blur_fill_unit_square_in_wide() -> None:
    assert should_blur_fill_slot(
        fit="contain",
        asset={"width": 1000, "height": 1000},
        pattern_id="screen-square-1",
        layout_hint=None,
        n_slots=1,
        export_layout="web",
        grid_class="layout-screen__grid--1col",
        stage_ar=16 / 9,
        is_plate=False,
        asset_aspect=1.0,
    )
