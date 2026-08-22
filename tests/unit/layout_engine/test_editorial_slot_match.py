"""MSP · portfolio slot admission; journal mosaic stays untouched."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.layout_engine.editorial_series.place import place_groups
from travelogue.layout_engine.editorial_series.slot_match import (
    collect_asset_aspects,
    fit_for_pair,
    take_for_page,
)
from travelogue.layout_engine.planner.beam_scoring import score_aspect_match
from travelogue.paths import ROOT

pytestmark = pytest.mark.unit


def test_1l1p_reorders_portrait_first_pair() -> None:
    kinds = {"p1": "portrait", "l1": "landscape"}
    ratios = {"p1": 0.75, "l1": 1.333}
    taken = take_for_page(
        ["p1", "l1"],
        "page-2-1l1p",
        band=2,
        aspect_kinds=kinds,
        aspect_ratios=ratios,
    )
    assert taken.skip is False
    assert taken.asset_ids == ["l1", "p1"]
    assert taken.roles == ["landscape", "portrait"]


def test_pair_port_refuses_landscape_only_group() -> None:
    taken = take_for_page(
        ["l1", "l2"],
        "page-2-pair-port",
        band=2,
        aspect_kinds={"l1": "landscape", "l2": "landscape"},
        aspect_ratios={"l1": 1.333, "l2": 1.778},
    )
    assert taken.skip is True
    assert taken.asset_ids == []
    assert taken.leftover == ["l1", "l2"]


def test_pair_port_picks_portraits_from_mixed_group() -> None:
    taken = take_for_page(
        ["l1", "p1", "p2"],
        "page-2-pair-port",
        band=2,
        aspect_kinds={"l1": "landscape", "p1": "portrait", "p2": "portrait"},
        aspect_ratios={"l1": 1.5, "p1": 0.75, "p2": 0.75},
    )
    assert taken.asset_ids == ["p1", "p2"]
    assert taken.leftover == ["l1"]
    assert all(r == "portrait" for r in taken.roles)


def test_wide_land_slot_prefers_16x9_over_4x3() -> None:
    taken = take_for_page(
        ["a43", "a169"],
        "page-2-1l1p-wide",
        band=2,
        aspect_kinds={"a43": "landscape", "a169": "landscape", "p1": "portrait"},
        aspect_ratios={"a43": 4 / 3, "a169": 16 / 9},
    )
    # Only one land + missing port → cannot admit 1l1p-wide.
    assert taken.skip is True

    taken = take_for_page(
        ["a43", "a169", "p1"],
        "page-2-1l1p-wide",
        band=2,
        aspect_kinds={
            "a43": "landscape",
            "a169": "landscape",
            "p1": "portrait",
        },
        aspect_ratios={"a43": 4 / 3, "a169": 16 / 9, "p1": 0.75},
    )
    assert taken.skip is False
    assert taken.asset_ids[0] == "a169"
    assert taken.asset_ids[1] == "p1"
    assert taken.leftover == ["a43"]
    assert taken.fits[0] == "cover"
    assert taken.display_aspects[0] == pytest.approx(1.7778, rel=1e-3)


def test_4x3_in_16x9_slot_uses_contain() -> None:
    assert fit_for_pair(4 / 3, 16 / 9) == "contain"
    assert fit_for_pair(16 / 9, 16 / 9) == "cover"
    assert fit_for_pair(0.75, 0.75) == "cover"


def test_place_swaps_land_grid_for_portrait_bookend() -> None:
    groups = [
        {
            "id": "g-port",
            "kind": "scene",
            "asset_ids": ["p1", "p2", "p3", "p4"],
        }
    ]
    sequence = [
        {"role": "grid4", "slotBand": 4, "patternId": "page-4-grid-land"},
        {"role": "pair", "slotBand": 2, "patternId": "page-2-pair-port"},
    ]
    kinds = {f"p{i}": "portrait" for i in range(1, 5)}
    ratios = {f"p{i}": 0.75 for i in range(1, 5)}
    placed = place_groups(groups, sequence, aspect_kinds=kinds, aspect_ratios=ratios)
    assert placed.dropped_roles == []
    assert placed.demoted_pages >= 1
    assert placed.pages[0].pattern_id == "page-4-2p2p"
    assert set(placed.pages[0].asset_ids) == {"p1", "p2", "p3", "p4"}
    screen = placed.pages[0].as_screen()
    assert all(s.get("role") == "portrait" for s in screen["slots"])
    assert screen["layoutGeometry"]["stageAspect"] == "16:9"
    assert len(placed.pages) == 1


def test_place_swaps_land6_for_mixed_2l4p() -> None:
    ids = ["l1", "l2", "p1", "p2", "p3", "p4"]
    groups = [{"id": "g-mix", "kind": "scene", "asset_ids": ids}]
    sequence = [
        {"role": "dense", "slotBand": 6, "patternId": "page-6-grid-land"},
    ]
    kinds = {i: ("landscape" if i.startswith("l") else "portrait") for i in ids}
    ratios = {i: (16 / 9 if i.startswith("l") else 0.75) for i in ids}
    placed = place_groups(groups, sequence, aspect_kinds=kinds, aspect_ratios=ratios)
    assert placed.pages[0].pattern_id in {
        "page-6-2l4p-wide",
        "page-6-2l4p-wide-flip",
        "page-6-2l4p-left",
        "page-6-2l4p-right",
        "page-6-4l2p",
    }
    assert set(placed.pages[0].asset_ids) == set(ids)


def test_square_does_not_fill_land_grid() -> None:
    taken = take_for_page(
        ["l1", "l2", "l3", "s1"],
        "page-4-grid-land",
        band=4,
        aspect_kinds={
            "l1": "landscape",
            "l2": "landscape",
            "l3": "landscape",
            "s1": "square",
        },
        aspect_ratios={"l1": 4 / 3, "l2": 4 / 3, "l3": 4 / 3, "s1": 1.0},
    )
    assert taken.skip is True


def test_mixed_trio_does_not_underfill_planned_face() -> None:
    taken = take_for_page(
        ["l1", "p1"],
        "page-3-2l1p-hero-left",
        band=3,
        aspect_kinds={"l1": "landscape", "p1": "portrait"},
        aspect_ratios={"l1": 4 / 3, "p1": 0.75},
    )
    assert taken.skip is True
    from travelogue.layout_engine.editorial_series.slot_match import fallback_take

    fb = fallback_take(
        ["l1", "p1"],
        "page-3-2l1p-hero-left",
        aspect_kinds={"l1": "landscape", "p1": "portrait"},
        aspect_ratios={"l1": 4 / 3, "p1": 0.75},
    )
    assert fb is not None
    face, taken = fb
    assert face in {"page-2-1l1p", "page-2-1p1l", "page-2-1l1p-wide", "page-2-1p1l-wide"}
    assert set(taken.asset_ids) == {"l1", "p1"}


def test_page_face_render_stays_16x9_one_screen() -> None:
    from travelogue.render.context import build_layout_screen

    ctx = build_layout_screen(
        {
            "screenId": "ch-01-sc-01",
            "patternId": "page-1-hero-port",
            "slots": [{"assetId": "p1", "slot": 0, "fit": "cover"}],
        },
        {
            "p1": {
                "id": "p1",
                "nativeWidth": 1200,
                "nativeHeight": 1600,
                "displayFile": "p1.jpg",
            }
        },
        meta_title="Test",
        export_layout="web",
    )
    assert "--screen-aspect: 16 / 9" in ctx["screenStyle"]
    assert "--slot-aspect:" not in (ctx["slots"][0].get("slotStyle") or "")
    assert ctx.get("hasViewportFit") is not True


def test_journal_single_portrait_still_uses_photo_aspect() -> None:
    from travelogue.render.context import build_layout_screen

    ctx = build_layout_screen(
        {
            "screenId": "ch-01-sc-01",
            "patternId": "screen-portrait-1",
            "slots": [{"assetId": "p1", "slot": 0, "fit": "cover"}],
        },
        {
            "p1": {
                "id": "p1",
                "nativeWidth": 1200,
                "nativeHeight": 1600,
                "displayFile": "p1.jpg",
            }
        },
        meta_title="Test",
        export_layout="web",
    )
    assert "--screen-aspect: 16 / 9" not in ctx["screenStyle"]
    assert "1200 / 1600" in (ctx["screenStyle"] or "")


def test_no_aspect_signal_keeps_fifo() -> None:
    taken = take_for_page(["a", "b"], "page-2-1l1p", band=2)
    assert taken.asset_ids == ["a", "b"]
    assert taken.fits == ["cover", "cover"]


def test_collect_aspects_ignores_assets_without_pixels_or_kind() -> None:
    kinds, ratios = collect_asset_aspects(
        [{"id": "a1"}, {"id": "a2", "nativeWidth": 1600, "nativeHeight": 900}]
    )
    assert "a1" not in kinds
    assert kinds["a2"] == "landscape"
    assert ratios["a2"] == pytest.approx(16 / 9)


def test_journal_score_aspect_match_unchanged() -> None:
    screen = {
        "patternId": "screen-landscape-1-portrait-1",
        "slots": [
            {"assetId": "l1", "slot": 0, "role": "landscape", "fit": "cover"},
            {"assetId": "p1", "slot": 1, "role": "portrait", "fit": "cover"},
        ],
    }
    assert (
        score_aspect_match(screen, {"l1": "landscape", "p1": "portrait"}) == 1.0
    )


@pytest.mark.pipeline_isolation
def test_journal_mosaic_does_not_import_portfolio_slot_match() -> None:
    mosaic = ROOT / "travelogue" / "layout_engine" / "mosaic"
    api = ROOT / "travelogue" / "layout_engine" / "api.py"
    banned = ("editorial_series.slot_match", "take_for_page", "slot_match")
    files = list(mosaic.rglob("*.py")) + [api]
    for path in files:
        text = Path(path).read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{path} imports portfolio slot matcher"
