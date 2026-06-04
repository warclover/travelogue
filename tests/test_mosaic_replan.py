"""replan_screen · alt_topk / legacy (P15 benchmark P1)."""

from __future__ import annotations

import copy

import pytest

from travelogue.curation.layout_planner import aspect_kind_for_asset
from travelogue.curation.longshot_filter import BREATH_PATTERN
from travelogue.curation.mosaic.replan import ReplanError, replan_screen
from travelogue.config import get_config

from tests._golden.helpers import (
    build_mosaic_eligible_trip,
    build_mosaic_portrait4_trip,
    plan_mosaic_screens,
)


def _chapters_with_aspects():
    buckets, aspects_map, assets = build_mosaic_eligible_trip()
    aspects = {aid: aspects_map[aid] for aid in buckets[0]}
    assets_map = {a["id"]: a for a in assets}
    chapters = plan_mosaic_screens(buckets[:1], aspects_map, assets)
    return chapters, aspects, assets_map


def test_replan_screen_alt_topk_changes_pattern() -> None:
    chapters, aspects, assets_map = _chapters_with_aspects()
    screen = chapters[0]["screens"][0]
    sid = screen["screenId"]
    before_pid = screen["patternId"]

    result = replan_screen(
        chapters,
        sid,
        strategy="alt_topk",
        top_k=3,
        aspects=aspects,
        assets_map=assets_map,
        cfg=get_config().mosaic,
    )
    assert result["applied"] is True
    assert result["screenId"] == sid
    assert chapters[0]["screens"][0]["screenId"] == sid
    if result["reason"] == "alt_topk":
        assert result["newPatternId"] != before_pid


def test_replan_screen_legacy_builds_screen() -> None:
    buckets, aspects_map, assets = build_mosaic_portrait4_trip()
    aspects = {aid: aspects_map[aid] for aid in buckets[0]}
    assets_map = {a["id"]: a for a in assets}
    chapters = plan_mosaic_screens(buckets, aspects_map, assets)
    screen = chapters[0]["screens"][0]
    sid = screen["screenId"]
    result = replan_screen(
        chapters,
        sid,
        strategy="legacy",
        aspects=aspects,
        assets_map=assets_map,
    )
    assert result["applied"] is True
    assert result["reason"] == "legacy"
    assert chapters[0]["screens"][0].get("slots")


def test_replan_screen_missing_context_raises() -> None:
    chapters, _, _ = _chapters_with_aspects()
    sid = chapters[0]["screens"][0]["screenId"]
    with pytest.raises(ReplanError, match="aspects"):
        replan_screen(chapters, sid)


def test_replan_screen_breath_pause_raises() -> None:
    chapters, aspects, assets_map = _chapters_with_aspects()
    breath = {
        "screenId": "breath-test",
        "patternId": BREATH_PATTERN,
        "slots": [],
    }
    chapters[0]["screens"].append(breath)
    with pytest.raises(ReplanError, match="no replannable"):
        replan_screen(
            chapters,
            "breath-test",
            aspects=aspects,
            assets_map=assets_map,
        )


def test_replan_screen_unknown_id_raises() -> None:
    chapters, aspects, assets_map = _chapters_with_aspects()
    with pytest.raises(ReplanError, match="not found"):
        replan_screen(chapters, "missing-screen", aspects=aspects, assets_map=assets_map)


def test_build_legacy_screen_portrait_four() -> None:
    from travelogue.curation.mosaic.legacy import build_legacy_screen

    buckets, aspects_map, assets = build_mosaic_portrait4_trip()
    window = buckets[0]
    aspects = {aid: aspects_map[aid] for aid in window}
    assets_map = {a["id"]: a for a in assets}
    screen = build_legacy_screen(window, 4, aspects, assets_map, trip_total=4)
    assert screen is not None
    assert screen["patternId"] == "screen-portrait-4"
    assert len(screen.get("slots") or []) == 4
