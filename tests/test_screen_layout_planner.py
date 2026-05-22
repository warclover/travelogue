"""Web screens layout engine (layoutEngine=screens)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from travelogue.curation.screen_planner import (
    PATTERN_PORTRAIT_1_LANDSCAPE_2,
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


def test_plan_mixed_requires_time_proximity_when_exif_present():
    base = datetime(2025, 5, 1, 12, 0, 0, tzinfo=timezone.utc)
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
    base = datetime(2025, 5, 1, 12, 0, 0, tzinfo=timezone.utc)
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
    base = datetime(2025, 5, 1, 12, 0, 0, tzinfo=timezone.utc)
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
    base = datetime(2025, 5, 1, 12, 0, 0, tzinfo=timezone.utc)
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
