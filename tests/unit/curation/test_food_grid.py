"""Phase 10 · food grid screen planner tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from travelogue.layout_engine.planner.screen_planner import (
    FOOD_GRID_LAYOUT_HINT,
    PATTERN_PORTRAIT_GRID_8,
    plan_screens_for_chapter,
)
from travelogue.layout_engine.planner.screen_planner_stages import (
    build_chapter_plan_context,
    stage_flush_remaining_food,
)


def _assets_and_aspects(ids: list[str], *, food_ids: set[str], clip_only: set[str] | None = None) -> tuple[dict[str, dict], dict[str, str]]:
    clip_only = clip_only or set()
    base = datetime(2025, 6, 1, 10, 0, 0, tzinfo=UTC)
    assets: dict[str, dict] = {}
    aspects: dict[str, str] = {}
    for i, aid in enumerate(ids):
        asset: dict = {
            "id": aid,
            "takenAt": (base + timedelta(seconds=i)).isoformat().replace("+00:00", "Z"),
        }
        if aid in food_ids:
            if aid in clip_only:
                asset["subjectClass"] = "food"
            else:
                asset["tags"] = ["food"]
        assets[aid] = asset
        if aid.startswith("p"):
            aspects[aid] = "portrait"
        elif aid.startswith("l"):
            aspects[aid] = "landscape"
        else:
            aspects[aid] = "square"
    return assets, aspects


def _food_screens(screens: list[dict]) -> list[dict]:
    return [sc for sc in screens if sc.get("layoutHint") == FOOD_GRID_LAYOUT_HINT]


def test_food3_generates_square4_food_grid() -> None:
    ids = ["f1", "f2", "f3"]
    assets, aspects = _assets_and_aspects(ids, food_ids=set(ids))
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        include_chapter_hero=False,
    )
    food = _food_screens(screens)
    assert len(food) == 1
    assert food[0]["patternId"] == "screen-square-4"
    assert len(food[0]["slots"]) == 3
    assert all(slot["fit"] == "cover" for slot in food[0]["slots"])


def test_food2_generates_food_grid() -> None:
    """AC-FRP-08 · ≥2 food → food-grid (square-4 with 2 slots)."""
    ids = ["f1", "f2"]
    assets, aspects = _assets_and_aspects(ids, food_ids=set(ids))
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        include_chapter_hero=False,
    )
    food = _food_screens(screens)
    assert len(food) == 1
    assert food[0]["patternId"] == "screen-square-4"
    assert len(food[0]["slots"]) == 2


def test_food_soft_cluster_across_one_landscape_within_window() -> None:
    """AC-FRP-09 · same meal window + 1 interruption still grids."""
    ids = ["f1", "l1", "f2", "f3"]
    assets, aspects = _assets_and_aspects(ids, food_ids={"f1", "f2", "f3"})
    # Spread within 60 minutes (default FRP window).
    base = datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC)
    for i, aid in enumerate(ids):
        assets[aid]["takenAt"] = (base + timedelta(minutes=i * 10)).isoformat().replace(
            "+00:00", "Z"
        )
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        include_chapter_hero=False,
    )
    food = _food_screens(screens)
    assert len(food) == 1
    assert len(food[0]["slots"]) == 3
    used_ids = {slot["assetId"] for sc in screens for slot in (sc.get("slots") or [])}
    assert "l1" in used_ids


def test_food_with_one_non_mundane_interference_still_triggers() -> None:
    ids = ["f1", "f2", "l1", "f3"]
    assets, aspects = _assets_and_aspects(ids, food_ids={"f1", "f2", "f3"})
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        include_chapter_hero=False,
    )
    food = _food_screens(screens)
    assert len(food) == 1
    assert len(food[0]["slots"]) == 3
    # 干扰图不会丢失，仍会被后续 stage 消费。
    used_ids = {slot["assetId"] for sc in screens for slot in (sc.get("slots") or [])}
    assert "l1" in used_ids


def test_disable_food_grid_falls_back() -> None:
    ids = ["f1", "f2", "f3", "f4"]
    assets, aspects = _assets_and_aspects(ids, food_ids=set(ids))
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        include_chapter_hero=False,
        enable_food_grid=False,
    )
    assert not _food_screens(screens)


def test_portrait_grid8_and_food_grid_can_coexist() -> None:
    from travelogue.layout_engine.mosaic.lte_adapter import mosaic_pattern_disabled

    portrait_ids = [f"p{i}" for i in range(8)]
    food_ids = ["f1", "f2", "f3"]
    ids = portrait_ids + food_ids
    assets, aspects = _assets_and_aspects(ids, food_ids=set(food_ids))
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        burst_seconds=10.0,
        include_chapter_hero=False,
        trip_photo_total=80,
        orientation_summary={"portrait": 50, "landscape": 20},
    )
    patterns = [sc["patternId"] for sc in screens]
    assert _food_screens(screens)
    # Local LTE admission may prune grid-8; when enabled, both grids coexist.
    if not mosaic_pattern_disabled("screen-portrait-grid-8"):
        assert PATTERN_PORTRAIT_GRID_8 in patterns
    else:
        portrait_used = sum(
            1
            for sc in screens
            for slot in (sc.get("slots") or [])
            if str(slot.get("assetId") or "").startswith("p")
        )
        assert portrait_used == 8


def test_food6_generates_square6() -> None:
    ids = [f"f{i}" for i in range(6)]
    assets, aspects = _assets_and_aspects(ids, food_ids=set(ids))
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        include_chapter_hero=False,
    )
    food = _food_screens(screens)
    assert len(food) == 1
    assert food[0]["patternId"] == "screen-square-6"
    assert len(food[0]["slots"]) == 6


def test_food9_plus_splits_multiple_food_grids() -> None:
    ids = [f"f{i}" for i in range(12)]
    assets, aspects = _assets_and_aspects(ids, food_ids=set(ids))
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        include_chapter_hero=False,
    )
    food = _food_screens(screens)
    assert [sc["patternId"] for sc in food] == ["screen-square-9", "screen-square-4"]
    assert len(food[1]["slots"]) == 3


def test_clip_food_without_tags_still_triggers() -> None:
    ids = ["f1", "f2", "f3"]
    assets, aspects = _assets_and_aspects(ids, food_ids=set(ids), clip_only=set(ids))
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        include_chapter_hero=False,
    )
    assert _food_screens(screens)


def test_meal_tag_without_clip_still_triggers() -> None:
    ids = ["f1", "f2", "f3"]
    assets, aspects = _assets_and_aspects(ids, food_ids=set())
    for aid in ids:
        assets[aid]["tags"] = ["meal"]
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        include_chapter_hero=False,
    )
    assert _food_screens(screens)


def test_stage_flush_remaining_food_emits_grid_for_tail_buffer() -> None:
    ids = ["f1", "f2", "f3"]
    assets, aspects = _assets_and_aspects(ids, food_ids=set(ids))
    ctx = build_chapter_plan_context(
        ids,
        aspects,
        assets=assets,
        enable_food_grid=True,
    )
    ctx.i = len(ctx.ids)
    stage_flush_remaining_food(ctx)
    assert len(ctx.screens) == 1
    assert ctx.screens[0]["layoutHint"] == FOOD_GRID_LAYOUT_HINT


def test_sign_bucket_grid_requires_explicit_bucket_enable() -> None:
    ids = ["s1", "s2", "s3"]
    assets, aspects = _assets_and_aspects(ids, food_ids=set())
    for aid in ids:
        assets[aid]["tags"] = ["sign"]
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        include_chapter_hero=False,
    )
    assert all(sc.get("layoutHint") != "sign-grid" for sc in screens)


def test_sign_bucket_grid_when_bucket_enabled() -> None:
    ids = ["s1", "s2", "s3"]
    assets, aspects = _assets_and_aspects(ids, food_ids=set())
    for aid in ids:
        assets[aid]["tags"] = ["sign"]
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        include_chapter_hero=False,
        mundane_grid_buckets=("food", "sign"),
    )
    assert any(sc.get("layoutHint") == "sign-grid" for sc in screens)


def test_ticket_bucket_grid_when_bucket_enabled() -> None:
    ids = ["t1", "t2", "t3"]
    assets, aspects = _assets_and_aspects(ids, food_ids=set())
    for aid in ids:
        assets[aid]["tags"] = ["ticket"]
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        include_chapter_hero=False,
        mundane_grid_buckets=("food", "ticket"),
    )
    assert any(sc.get("layoutHint") == "ticket-grid" for sc in screens)


def test_shop_bucket_grid_when_bucket_enabled() -> None:
    ids = ["h1", "h2", "h3"]
    assets, aspects = _assets_and_aspects(ids, food_ids=set())
    for aid in ids:
        assets[aid]["tags"] = ["shop"]
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        include_chapter_hero=False,
        mundane_grid_buckets=("food", "shop"),
    )
    assert any(sc.get("layoutHint") == "shop-grid" for sc in screens)


def test_mixed_bucket_prefix_still_forms_food_grid() -> None:
    ids = ["s1", "f1", "f2", "f3"]
    assets, aspects = _assets_and_aspects(ids, food_ids={"f1", "f2", "f3"})
    assets["s1"]["tags"] = ["sign"]
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        include_chapter_hero=False,
        mundane_grid_buckets=("food", "sign"),
    )
    assert any(sc.get("layoutHint") == FOOD_GRID_LAYOUT_HINT for sc in screens)


def test_flush_does_not_duplicate_assets_after_generic_screen() -> None:
    ids = ["s1", "f1", "f2", "f3"]
    assets, aspects = _assets_and_aspects(ids, food_ids={"f1", "f2", "f3"})
    assets["s1"]["tags"] = ["sign"]
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        include_chapter_hero=False,
        mundane_grid_buckets=("food", "sign"),
    )
    used_ids = [slot["assetId"] for sc in screens for slot in (sc.get("slots") or [])]
    assert len(used_ids) == len(set(used_ids))
