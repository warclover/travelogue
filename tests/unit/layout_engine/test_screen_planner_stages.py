"""Chapter screen planner stages (Phase 7.5)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from travelogue.layout_engine.mosaic.compose import WindowPickResult
from travelogue.layout_engine.mosaic.hook import chapter_should_skip_hero_for_mosaic
from travelogue.layout_engine.mosaic.log import MosaicWindowLog
from travelogue.layout_engine.planner.screen_planner_stages import (
    ChapterScreenPlanner,
    build_chapter_plan_context,
    stage_chapter_hero,
)


def _assets(ids: list[str], *, portrait: bool = False) -> dict[str, dict]:
    base = datetime(2025, 6, 1, 10, 0, 0, tzinfo=UTC)
    out: dict[str, dict] = {}
    for i, aid in enumerate(ids):
        out[aid] = {
            "id": aid,
            "takenAt": (base + timedelta(seconds=i * 5)).isoformat().replace("+00:00", "Z"),
            "aspectKind": "portrait" if portrait else "landscape",
            "width": 900 if portrait else 1600,
            "height": 1600 if portrait else 900,
        }
    return out


def test_build_chapter_plan_context_sorts_by_taken_at() -> None:
    ids = ["b", "a", "c"]
    aspects = {"a": "landscape", "b": "landscape", "c": "landscape"}
    assets = _assets(ids)
    ctx = build_chapter_plan_context(ids, aspects, assets=assets, chapter_id="ch-01")
    taken_order = sorted(ids, key=lambda x: assets[x]["takenAt"])
    assert ctx.ids == taken_order


def test_chapter_hero_not_skipped_when_mosaic_winner_lacks_main_role() -> None:
    ids = [f"a{i}" for i in range(1, 7)]
    aspects = {aid: "landscape" for aid in ids}
    assets = _assets(ids)
    ctx = build_chapter_plan_context(
        ids,
        aspects,
        assets=assets,
        chapter_id="ch-hero",
        include_chapter_hero=True,
        trip_photo_total=20,
    )
    assert chapter_should_skip_hero_for_mosaic(ctx) is False


def test_chapter_hero_skipped_when_mosaic_winner_has_main_role(monkeypatch) -> None:
    ids = [f"a{i}" for i in range(1, 7)]
    aspects = {aid: "landscape" for aid in ids}
    assets = _assets(ids)
    ctx = build_chapter_plan_context(
        ids,
        aspects,
        assets=assets,
        chapter_id="ch-hero",
        include_chapter_hero=True,
        trip_photo_total=20,
    )
    hero_screen = {
        "patternId": "screen-mosaic-6-main-hero-plus-5",
        "slots": [
            {"assetId": "a1", "slot": 0, "fit": "cover", "role": "main"},
            {"assetId": "a2", "slot": 1, "fit": "cover", "role": "tile"},
        ],
    }

    def _fake_pick(*_args, **_kwargs):
        return WindowPickResult(
            screen=hero_screen,
            log=MosaicWindowLog(segment_id="ch-hero", window_size=6, window_start=0),
            used_legacy=False,
        )

    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.hook.pick_best_window",
        _fake_pick,
    )
    assert chapter_should_skip_hero_for_mosaic(ctx) is True
    stage_chapter_hero(ctx)
    assert ctx.hero_preface == []
    assert len(ctx.ids) == 6


def test_stage_chapter_hero_prepends_hero_screen() -> None:
    ids = [f"a{i}" for i in range(1, 7)]
    aspects = {aid: "landscape" for aid in ids}
    assets = _assets(ids)
    ctx = build_chapter_plan_context(
        ids,
        aspects,
        assets=assets,
        chapter_id="ch-hero",
        include_chapter_hero=True,
    )
    stage_chapter_hero(ctx)
    assert len(ctx.hero_preface) == 1
    assert ctx.hero_preface[0]["patternId"]
    assert len(ctx.ids) == 5


def test_chapter_screen_planner_returns_numbered_screens() -> None:
    ids = [f"a{i}" for i in range(6)]
    aspects = {aid: "landscape" for aid in ids}
    assets = _assets(ids)
    screens = ChapterScreenPlanner.create(
        ids,
        aspects,
        assets=assets,
        chapter_id="ch-plan",
        include_chapter_hero=False,
    ).plan()
    assert screens
    assert all(sc.get("screenId", "").startswith("ch-plan-sc-") for sc in screens)
