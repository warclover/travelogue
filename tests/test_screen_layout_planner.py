"""Web screens layout engine (layoutEngine=screens)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from travelogue.config import get_config


@pytest.fixture(autouse=True)
def _planner_tests_disable_mosaic(monkeypatch, request):
    """Legacy planner unit tests expect pre-MCS behavior."""
    if request.node.get_closest_marker("mosaic"):
        return
    cfg = get_config()
    monkeypatch.setattr(
        "travelogue.config.get_config",
        lambda: replace(cfg, mosaic=replace(cfg.mosaic, enabled=False)),
    )

from travelogue.curation.screen_layout_state import portrait_grid8_max_for_trip
from travelogue.curation.screen_planner import (
    MIN_TRIP_PHOTOS_FOR_MOSAIC,
    PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
    PATTERN_PORTRAIT_1_LANDSCAPE_2,
    PATTERN_PORTRAIT_GRID_8,
    PERSON_LAYOUT_GRID_8,
    NineGridPlannerState,
    ScreenLayoutPlannerState,
    attach_screens_day_buckets,
    attach_screens_to_chapters,
    burst_group_map,
    grid_class_for_pattern,
    is_nine_grid_pattern,
    is_portrait_single_pattern,
    is_six_grid_pattern,
    is_triple_row_pattern,
    layout_kind_from_pattern,
    nine_grid_limits_for_trip,
    plan_screens_for_chapter,
    screens_layout_active,
)
from travelogue.media.image_ops import classify_aspect


def _aspects(ids: list[str], kinds: dict[str, str]) -> dict:
    return {i: kinds[i] for i in ids}


def test_plan_three_portraits_one_screen():
    ids = ["p1", "p2", "p3"]
    aspects = _aspects(ids, {x: "portrait" for x in ids})
    screens = plan_screens_for_chapter(ids, aspects, chapter_id="ch-01")
    assert len(screens) == 1
    assert screens[0]["patternId"] == "screen-portrait-3"
    assert len(screens[0]["slots"]) == 3
    assert all(s["fit"] == "cover" for s in screens[0]["slots"])
    assert grid_class_for_pattern("screen-portrait-3") == "layout-screen__grid--3col"


def test_plan_single_portrait_cover_fallback():
    screens = plan_screens_for_chapter(
        ["p1"],
        {"p1": "portrait"},
        chapter_id="ch-01",
    )
    assert screens[0]["patternId"] == "screen-portrait-1"
    assert screens[0]["slots"][0]["fit"] == "cover"


def test_plan_mixed_portrait_then_two_landscapes():
    ids = ["p1", "l1", "l2"]
    aspects = {"p1": "portrait", "l1": "landscape", "l2": "landscape"}
    screens = plan_screens_for_chapter(ids, aspects, chapter_id="ch-mix")
    assert len(screens) == 1
    assert screens[0]["patternId"] == PATTERN_PORTRAIT_1_LANDSCAPE_2
    assert screens[0]["slots"][0]["role"] == "portrait"
    assert screens[0]["slots"][1]["role"] == "landscape"
    assert all(s["fit"] == "cover" for s in screens[0]["slots"])
    assert (
        grid_class_for_pattern(PATTERN_PORTRAIT_1_LANDSCAPE_2)
        == "layout-screen__grid--portrait-left-2landscape"
    )


def test_plan_mixed_two_landscapes_then_portrait():
    ids = ["l1", "l2", "p1"]
    aspects = {"p1": "portrait", "l1": "landscape", "l2": "landscape"}
    screens = plan_screens_for_chapter(ids, aspects, chapter_id="ch-mix2")
    assert len(screens) == 1
    assert screens[0]["patternId"] == PATTERN_PORTRAIT_1_LANDSCAPE_2
    assert screens[0]["slots"][0]["assetId"] == "p1"


@pytest.mark.mosaic
def test_plan_mosaic_5_main_portrait_3land():
    ids = ["l-main", "p1", "b1", "b2", "b3"]
    aspects = {
        "l-main": "landscape",
        "p1": "portrait",
        "b1": "landscape",
        "b2": "landscape",
        "b3": "landscape",
    }
    base = datetime(2025, 6, 1, 10, 0, 0, tzinfo=UTC)
    assets = {
        aid: {
            "id": aid,
            "takenAt": (base + timedelta(seconds=i)).isoformat().replace("+00:00", "Z"),
        }
        for i, aid in enumerate(ids)
    }
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        burst_seconds=30.0,
        chapter_id="ch-m5",
        trip_photo_total=MIN_TRIP_PHOTOS_FOR_MOSAIC,
    )
    assert len(screens) == 1
    assert screens[0]["patternId"] == PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND
    assert [s["assetId"] for s in screens[0]["slots"]] == ids
    assert screens[0]["slots"][0]["role"] == "main"
    assert screens[0]["slots"][1]["role"] == "portrait"
    assert grid_class_for_pattern(PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND) == (
        "layout-screen__grid--mosaic-5-main-portrait-3land"
    )
    assert layout_kind_from_pattern(PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND) == "other"


@pytest.mark.mosaic
def test_plan_mosaic_5_prefers_cover_score_for_main():
    ids = ["l-low", "p1", "l-high", "b2", "b3"]
    aspects = {aid: ("portrait" if aid == "p1" else "landscape") for aid in ids}
    base = datetime(2025, 6, 1, 10, 0, 0, tzinfo=UTC)
    assets = {
        aid: {
            "id": aid,
            "takenAt": (base + timedelta(seconds=i)).isoformat().replace("+00:00", "Z"),
            "aspectKind": "landscape" if aid != "p1" else "portrait",
            "width": 1600 if aid == "l-high" else 800,
            "height": 900 if aid == "l-high" else 800,
        }
        for i, aid in enumerate(ids)
    }
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        burst_seconds=60.0,
        chapter_id="ch-m5-main",
        trip_photo_total=MIN_TRIP_PHOTOS_FOR_MOSAIC,
    )
    assert screens[0]["patternId"] == PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND
    assert screens[0]["slots"][0]["assetId"] == "l-high"


@pytest.mark.mosaic
def test_plan_mosaic_5_requires_time_proximity():
    base = datetime(2025, 6, 1, 10, 0, 0, tzinfo=UTC)
    assets = {
        "l1": {"id": "l1", "takenAt": base.isoformat().replace("+00:00", "Z")},
        "p1": {
            "id": "p1",
            "takenAt": (base + timedelta(seconds=1)).isoformat().replace("+00:00", "Z"),
        },
        "l2": {
            "id": "l2",
            "takenAt": (base + timedelta(seconds=2)).isoformat().replace("+00:00", "Z"),
        },
        "l3": {
            "id": "l3",
            "takenAt": (base + timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
        },
        "l4": {
            "id": "l4",
            "takenAt": (base + timedelta(minutes=6)).isoformat().replace("+00:00", "Z"),
        },
    }
    ids = ["l1", "p1", "l2", "l3", "l4"]
    aspects = {aid: ("portrait" if aid == "p1" else "landscape") for aid in ids}
    screens = plan_screens_for_chapter(
        ids, aspects, assets=assets, burst_seconds=3.0, chapter_id="ch-m5-far"
    )
    assert all(sc["patternId"] != PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND for sc in screens)


@pytest.mark.mosaic
def test_plan_mosaic_5_skips_chapter_hero_when_chapter_is_exactly_five():
    """章首 Hero 与五图拼版互斥：整章恰好 5 张且符合拼版时不拆出 landscape-1。"""
    ids = ["l-low", "p1", "l-high", "b2", "b3"]
    aspects = {aid: ("portrait" if aid == "p1" else "landscape") for aid in ids}
    base = datetime(2025, 6, 1, 10, 0, 0, tzinfo=UTC)
    assets = {
        aid: {
            "id": aid,
            "takenAt": (base + timedelta(seconds=i)).isoformat().replace("+00:00", "Z"),
            "aspectKind": "landscape" if aid != "p1" else "portrait",
            "width": 1600 if aid == "l-high" else 800,
            "height": 900 if aid == "l-high" else 800,
        }
        for i, aid in enumerate(ids)
    }
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        burst_seconds=60.0,
        chapter_id="ch-m5-no-hero",
        trip_photo_total=MIN_TRIP_PHOTOS_FOR_MOSAIC,
    )
    assert len(screens) == 1
    assert screens[0]["patternId"] == PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND
    assert screens[0]["slots"][0]["assetId"] == "l-high"


def test_portrait_grid8_limits_by_trip_size():
    assert portrait_grid8_max_for_trip(50) == 0
    assert portrait_grid8_max_for_trip(51) == 2
    assert portrait_grid8_max_for_trip(150) == 4
    assert portrait_grid8_max_for_trip(250) == 6


def test_plan_portrait_grid8_when_trip_over_50_and_portrait_heavy():
    ids = [f"p{i}" for i in range(8)]
    aspects = {x: "portrait" for x in ids}
    base = datetime(2025, 9, 1, 10, 0, 0, tzinfo=UTC)
    assets = {
        aid: {
            "id": aid,
            "takenAt": (base + timedelta(seconds=i)).isoformat().replace("+00:00", "Z"),
        }
        for i, aid in enumerate(ids)
    }
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        burst_seconds=10.0,
        chapter_id="ch-p8",
        trip_photo_total=60,
        orientation_summary={"portrait": 40, "landscape": 20},
    )
    assert len(screens) == 1
    assert screens[0]["patternId"] == PATTERN_PORTRAIT_GRID_8
    assert len(screens[0]["slots"]) == 8
    assert layout_kind_from_pattern(PATTERN_PORTRAIT_GRID_8) == "other"
    assert (
        grid_class_for_pattern(PATTERN_PORTRAIT_GRID_8)
        == "layout-screen__grid--portrait-2x4"
    )


def test_plan_portrait_grid8_person_hint():
    ids = [f"p{i}" for i in range(8)]
    aspects = {x: "portrait" for x in ids}
    base = datetime(2025, 9, 1, 10, 0, 0, tzinfo=UTC)
    assets = {
        aid: {
            "id": aid,
            "takenAt": (base + timedelta(seconds=i)).isoformat().replace("+00:00", "Z"),
            "tags": ["person"],
        }
        for i, aid in enumerate(ids)
    }
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        burst_seconds=10.0,
        chapter_id="ch-p8p",
        trip_photo_total=60,
        orientation_summary={"portrait": 35, "landscape": 25},
    )
    assert screens[0]["layoutHint"] == PERSON_LAYOUT_GRID_8
    assert all(s["fit"] == "contain" for s in screens[0]["slots"])


def test_plan_no_portrait_grid8_when_trip_at_most_50():
    ids = [f"p{i}" for i in range(8)]
    aspects = {x: "portrait" for x in ids}
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        chapter_id="ch-no8",
        trip_photo_total=50,
        orientation_summary={"portrait": 30, "landscape": 20},
    )
    assert all(sc["patternId"] != PATTERN_PORTRAIT_GRID_8 for sc in screens)


def test_plan_no_portrait_grid8_when_not_portrait_heavy():
    ids = [f"p{i}" for i in range(8)]
    aspects = {x: "portrait" for x in ids}
    base = datetime(2025, 9, 1, 10, 0, 0, tzinfo=UTC)
    assets = {
        aid: {
            "id": aid,
            "takenAt": (base + timedelta(seconds=i)).isoformat().replace("+00:00", "Z"),
        }
        for i, aid in enumerate(ids)
    }
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        burst_seconds=10.0,
        chapter_id="ch-lheavy",
        trip_photo_total=80,
        orientation_summary={"portrait": 20, "landscape": 60},
    )
    assert all(sc["patternId"] != PATTERN_PORTRAIT_GRID_8 for sc in screens)


def test_plan_portrait_grid8_ten_yields_grid_plus_remainder():
    ids = [f"p{i}" for i in range(10)]
    aspects = {x: "portrait" for x in ids}
    base = datetime(2025, 9, 1, 10, 0, 0, tzinfo=UTC)
    assets = {
        aid: {
            "id": aid,
            "takenAt": (base + timedelta(seconds=i)).isoformat().replace("+00:00", "Z"),
        }
        for i, aid in enumerate(ids)
    }
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        burst_seconds=10.0,
        chapter_id="ch-p10",
        trip_photo_total=60,
        orientation_summary={"portrait": 40, "landscape": 20},
    )
    assert screens[0]["patternId"] == PATTERN_PORTRAIT_GRID_8
    assert sum(1 for sc in screens if sc["patternId"] == PATTERN_PORTRAIT_GRID_8) == 1
    assert sum(len(sc.get("slots") or []) for sc in screens) == 10


@pytest.mark.mosaic
def test_plan_mosaic_5_beats_mixed_p1_l2_when_five_fit():
    ids = ["p1", "l1", "l2", "l3", "l4"]
    aspects = {aid: ("portrait" if aid == "p1" else "landscape") for aid in ids}
    base = datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC)
    assets = {
        aid: {
            "id": aid,
            "takenAt": (base + timedelta(seconds=i)).isoformat().replace("+00:00", "Z"),
        }
        for i, aid in enumerate(ids)
    }
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        burst_seconds=10.0,
        chapter_id="ch-m5-over",
        trip_photo_total=MIN_TRIP_PHOTOS_FOR_MOSAIC,
    )
    assert len(screens) == 1
    assert screens[0]["patternId"] == PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND


def test_plan_mixed_requires_time_proximity_when_exif_present():
    base = datetime(2025, 5, 1, 12, 0, 0, tzinfo=UTC)
    assets = {
        "p1": {
            "id": "p1",
            "takenAt": base.isoformat().replace("+00:00", "Z"),
        },
        "l1": {
            "id": "l1",
            "takenAt": (base + timedelta(seconds=2)).isoformat().replace("+00:00", "Z"),
        },
        "l2": {
            "id": "l2",
            "takenAt": (base + timedelta(minutes=10)).isoformat().replace("+00:00", "Z"),
        },
    }
    ids = ["p1", "l1", "l2"]
    aspects = {"p1": "portrait", "l1": "landscape", "l2": "landscape"}
    screens = plan_screens_for_chapter(
        ids, aspects, assets=assets, burst_seconds=3.0, chapter_id="ch-far"
    )
    assert len(screens) >= 2
    assert screens[0]["patternId"] == "screen-portrait-1"
    assert any(
        sc["patternId"] in ("screen-landscape-1", "screen-landscape-2")
        for sc in screens[1:]
    )


def test_plan_landscape_four_is_2x2():
    ids = [f"l{i}" for i in range(4)]
    aspects = _aspects(ids, {x: "landscape" for x in ids})
    screens = plan_screens_for_chapter(ids, aspects, chapter_id="ch-02")
    assert len(screens) == 1
    assert screens[0]["patternId"] == "screen-landscape-4"
    assert len(screens[0]["slots"]) == 4
    assert grid_class_for_pattern("screen-landscape-4") == "layout-screen__grid--2x2"


def test_plan_landscape_nine_is_3x3():
    ids = [f"l{i}" for i in range(9)]
    aspects = _aspects(ids, {x: "landscape" for x in ids})
    screens = plan_screens_for_chapter(ids, aspects, chapter_id="ch-03")
    assert len(screens) == 1
    assert screens[0]["patternId"] == "screen-landscape-9"
    assert len(screens[0]["slots"]) == 9


def test_nine_grid_limits_by_trip_size():
    assert nine_grid_limits_for_trip(50) == (0, 1)
    assert nine_grid_limits_for_trip(51) == (2, 5)
    assert nine_grid_limits_for_trip(100) == (2, 5)
    assert nine_grid_limits_for_trip(101) == (4, 8)
    assert nine_grid_limits_for_trip(231) == (6, 10)


def _nine_patterns(screens: list[dict]) -> list[str]:
    return [sc["patternId"] for sc in screens if is_nine_grid_pattern(sc["patternId"])]


def test_trip_under_50_allows_at_most_one_nine_grid():
    ids = [f"l{i}" for i in range(18)]
    aspects = _aspects(ids, {x: "landscape" for x in ids})
    state = NineGridPlannerState.from_trip_total(40)
    screens = plan_screens_for_chapter(
        ids, aspects, chapter_id="ch-cap", layout_state=state
    )
    assert len(_nine_patterns(screens)) <= 1
    assert state.used <= 1


def _assert_no_consecutive_pattern_pairs(
    screens: list[dict],
    *,
    pred_a,
    pred_b=None,
) -> None:
    if pred_b is None:
        pred_b = pred_a
    for i in range(len(screens) - 1):
        a, b = screens[i]["patternId"], screens[i + 1]["patternId"]
        assert not (pred_a(a) and pred_b(b))


def test_no_consecutive_triple_six_or_portrait_single():
    base = datetime(2025, 5, 1, 12, 0, 0, tzinfo=UTC)
    ids = [f"p{i}" for i in range(24)]
    assets = {
        aid: {
            "id": aid,
            "takenAt": (base + timedelta(seconds=i % 2)).isoformat().replace("+00:00", "Z"),
        }
        for i, aid in enumerate(ids)
    }
    aspects = _aspects(ids, {x: "portrait" for x in ids})
    state = ScreenLayoutPlannerState.from_trip_total(220)
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        chapter_id="ch-rhythm",
        assets=assets,
        burst_seconds=3.0,
        layout_state=state,
    )
    _assert_no_consecutive_pattern_pairs(screens, pred_a=is_triple_row_pattern)
    _assert_no_consecutive_pattern_pairs(screens, pred_a=is_six_grid_pattern)
    _assert_no_consecutive_pattern_pairs(
        screens, pred_a=is_triple_row_pattern, pred_b=is_six_grid_pattern
    )
    _assert_no_consecutive_pattern_pairs(
        screens, pred_a=is_six_grid_pattern, pred_b=is_triple_row_pattern
    )
    _assert_no_consecutive_pattern_pairs(screens, pred_a=is_portrait_single_pattern)


def test_trip_200_plus_caps_nine_and_no_consecutive():
    base = datetime(2025, 5, 1, 12, 0, 0, tzinfo=UTC)
    ids = [f"l{i}" for i in range(72)]
    assets = {
        aid: {
            "id": aid,
            "takenAt": (base + timedelta(seconds=i % 3)).isoformat().replace("+00:00", "Z"),
        }
        for i, aid in enumerate(ids)
    }
    aspects = _aspects(ids, {x: "landscape" for x in ids})
    state = NineGridPlannerState.from_trip_total(220)
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        chapter_id="ch-big",
        assets=assets,
        burst_seconds=3.0,
        layout_state=state,
    )
    nines = _nine_patterns(screens)
    assert 1 <= len(nines) <= 10
    assert state.used == len(nines)
    for i in range(len(screens) - 1):
        if is_nine_grid_pattern(screens[i]["patternId"]):
            assert not is_nine_grid_pattern(screens[i + 1]["patternId"])


def test_plan_landscape_triple_then_single_portrait():
    ids = ["l1", "l2", "l3", "p1"]
    aspects = {
        "l1": "landscape",
        "l2": "landscape",
        "l3": "landscape",
        "p1": "portrait",
    }
    screens = plan_screens_for_chapter(ids, aspects, chapter_id="ch-02")
    assert len(screens) == 4
    assert all(sc["patternId"] == "screen-landscape-1" for sc in screens[:3])
    assert screens[3]["patternId"] == "screen-portrait-1"
    assert screens[3]["slots"][0]["fit"] == "cover"


def test_panorama_single_uses_landscape_screen_with_cover():
    screens = plan_screens_for_chapter(
        ["p1"],
        {"p1": "panorama"},
        chapter_id="ch-pano",
        assets={"p1": {"id": "p1", "width": 2400, "height": 900, "takenAt": "2025-05-01T12:00:00Z"}},
    )
    assert screens[0]["patternId"] == "screen-landscape-1"
    assert screens[0]["slots"][0]["fit"] == "cover"


def test_skip_web_cover_skips_chapter_hero_screen():
    ids = ["cover", "l2", "l3", "l4", "l5"]
    aspects = {**{x: "landscape" for x in ids}, "cover": "panorama"}
    assets = {
        i: {"id": i, "width": 2400, "height": 900, "takenAt": f"2025-05-01T12:0{x}:00Z"}
        for x, i in enumerate(ids)
    }
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        chapter_id="ch-skip",
        assets=assets,
        skip_screen_asset_ids={"cover"},
    )
    assert screens[0]["slots"][0]["assetId"] != "cover"


def test_chapter_opens_with_landscape_hero_when_enough_assets():
    ids = ["l1", "l2", "l3", "l4", "p1"]
    aspects = {**{x: "landscape" for x in ("l1", "l2", "l3", "l4")}, "p1": "portrait"}
    assets = {i: {"id": i, "width": 1920, "height": 1080, "takenAt": f"2025-05-01T12:0{x}:00Z"} for x, i in enumerate(ids, 1)}
    assets["p1"]["width"] = 900
    assets["p1"]["height"] = 1600
    screens = plan_screens_for_chapter(ids, aspects, chapter_id="ch-hero", assets=assets)
    assert screens[0]["patternId"] in ("screen-landscape-1", "screen-panorama-1")
    assert len(screens[0]["slots"]) == 1


def test_plan_four_landscapes_one_2x2_screen():
    ids = ["l1", "l2", "l3", "l4"]
    aspects = _aspects(ids, {x: "landscape" for x in ids})
    screens = plan_screens_for_chapter(ids, aspects, chapter_id="ch-02b")
    assert len(screens) == 1
    assert screens[0]["patternId"] == "screen-landscape-4"


def test_burst_group_prefers_four_grid():
    base = datetime(2025, 5, 1, 12, 0, 0, tzinfo=UTC)
    assets = {}
    ids = [f"l{i}" for i in range(4)]
    for i, aid in enumerate(ids):
        assets[aid] = {
            "id": aid,
            "takenAt": (base + timedelta(seconds=i)).isoformat().replace("+00:00", "Z"),
        }
    aspects = _aspects(ids, {x: "landscape" for x in ids})
    groups = burst_group_map(ids, assets, aspects, burst_seconds=3.0)
    assert len(set(groups.values())) == 1
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        burst_seconds=3.0,
    )
    assert screens[0]["patternId"] == "screen-landscape-4"


def test_attach_screens_from_chapter_items():
    chapters = [
        {
            "id": "ch-01",
            "items": [
                {
                    "type": "media-row",
                    "assetIds": ["p1", "p2", "p3"],
                    "rowLayout": "portrait-triple",
                },
                {"type": "media-card", "assetId": "l1"},
            ],
        }
    ]
    aspects = {"p1": "portrait", "p2": "portrait", "p3": "portrait", "l1": "landscape"}
    out = attach_screens_to_chapters(chapters, aspects)
    assert len(out[0]["screens"]) == 2
    assert out[0]["screens"][0]["patternId"] == "screen-portrait-3"
    assert out[0]["screens"][1]["patternId"] == "screen-landscape-1"


def test_screens_layout_active_requires_web():
    trip = {"exportLayout": "mobile", "layoutEngine": "screens"}
    assert screens_layout_active(trip) is False
    trip["exportLayout"] = "web"
    assert screens_layout_active(trip) is True
    assert screens_layout_active(trip, override="legacy") is False


def test_portrait_heavy_summary():
    ids = [f"p{i}" for i in range(6)]
    aspects = _aspects(ids, {x: "portrait" for x in ids})
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        orientation_summary={"portrait": 10, "landscape": 2},
    )
    assert len(screens) == 2
    assert screens[0]["patternId"] == "screen-portrait-3"
    assert screens[1]["patternId"] == "screen-portrait-3"


def test_landscape_pair_splits_into_two_single_screens():
    ids = ["l1", "l2"]
    aspects = _aspects(ids, {x: "landscape" for x in ids})
    screens = plan_screens_for_chapter(ids, aspects, chapter_id="ch-stack2")
    assert len(screens) == 2
    assert screens[0]["patternId"] == "screen-landscape-1"
    assert screens[1]["patternId"] == "screen-landscape-1"
    assert all(s["fit"] == "cover" for sc in screens for s in sc["slots"])


def test_portrait_pattern_rejects_landscape_asset():
    ids = ["p1", "l1", "p2"]
    aspects = {"p1": "portrait", "l1": "landscape", "p2": "portrait"}
    screens = plan_screens_for_chapter(ids, aspects, chapter_id="ch-no-mix-portrait")
    for sc in screens:
        if sc["patternId"].startswith("screen-portrait-3"):
            for slot in sc["slots"]:
                assert aspects[slot["assetId"]] == "portrait"


def test_classify_in_planner_chain():
    assert classify_aspect(1920, 1080) == "landscape"


def test_day_bucket_groups_portraits_across_chapters():
    """Day scope: three portraits split across two chapters → one portrait-3 screen."""
    chapters = [
        {
            "id": "ch-01",
            "items": [{"type": "media-card", "assetId": "p1"}],
        },
        {
            "id": "ch-02",
            "items": [
                {
                    "type": "media-row",
                    "assetIds": ["p2", "p3"],
                    "rowLayout": "portrait-pair",
                },
            ],
        },
    ]
    aspects = {"p1": "portrait", "p2": "portrait", "p3": "portrait"}
    out = attach_screens_day_buckets(
        chapters,
        [["p1", "p2", "p3"]],
        aspects,
    )
    assert len(out[0]["screens"]) == 1
    assert out[0]["screens"][0]["patternId"] == "screen-portrait-3"
    assert len(out[1]["screens"]) == 0


def test_attach_screens_day_scope_via_buckets_param():
    chapters = [
        {"id": "ch-01", "items": [{"type": "media-card", "assetId": "p1"}]},
        {
            "id": "ch-02",
            "items": [{"type": "media-card", "assetId": "p2"}],
        },
    ]
    aspects = {"p1": "portrait", "p2": "portrait"}
    out = attach_screens_to_chapters(
        chapters,
        aspects,
        plan_scope="day",
        day_buckets=[["p1", "p2"]],
    )
    assert sum(len(ch["screens"]) for ch in out) == 1
    assert out[0]["screens"][0]["patternId"] == "screen-portrait-2"
    assert len(out[0]["screens"][0]["slots"]) == 2
    assert len(out[1]["screens"]) == 0


def test_landscape_nine_across_mixed_aspect_buckets():
    """Nine-grid must not be blocked by prefix_same_bucket (classic vs standard)."""
    from travelogue.curation.screen_planner import _plan_one_screen

    ids = [f"l{i}" for i in range(12)]
    aspects = {aid: "landscape" for aid in ids}
    assets = {}
    for i, aid in enumerate(ids):
        # Alternate buckets: classic (4:3) vs standard (16:9)
        if i % 2 == 0:
            w, h = 4000, 3000
        else:
            w, h = 4000, 2250
        assets[aid] = {
            "id": aid,
            "nativeWidth": w,
            "nativeHeight": h,
            "width": w,
            "height": h,
        }
    state = ScreenLayoutPlannerState.from_trip_total(120)
    screen, consumed = _plan_one_screen(
        ids,
        aspects,
        assets_map=assets,
        layout_state=state,
    )
    assert consumed == 9
    assert screen is not None
    assert screen["patternId"] == "screen-landscape-9"
