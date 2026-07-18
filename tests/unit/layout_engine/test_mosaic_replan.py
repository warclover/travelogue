"""replan_screen · alt_topk / legacy (P15 benchmark P1)."""

from __future__ import annotations

import pytest

from tests._golden.helpers import (
    _mosaic_cfg_for_golden,
    build_mosaic_portrait3_trip,
    build_mosaic_portrait4_trip,
    build_mosaic_replan_chapter,
    plan_mosaic_screens,
)
from travelogue.curation.chapter_items import collect_screen_asset_ids
from travelogue.curation.longshot_filter import BREATH_PATTERN
from travelogue.layout_engine.mosaic.candidates import ScreenCandidate
from travelogue.layout_engine.mosaic.replan import ReplanError, replan_screen

pytestmark = pytest.mark.usefixtures("lte_pattern_enabled")


def _chapters_with_aspects():
    chapters, aspects, assets_map, _mosaic_cfg = build_mosaic_replan_chapter()
    return chapters, aspects, assets_map, _mosaic_cfg


def test_replan_screen_alt_topk_changes_pattern() -> None:
    chapters, aspects, assets_map, mosaic_cfg = _chapters_with_aspects()
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
        cfg=mosaic_cfg,
    )
    assert result["applied"] is True
    assert result["itemsSynced"] is True
    assert result["screenId"] == sid
    assert chapters[0]["screens"][0]["screenId"] == sid
    if result["reason"] == "alt_topk":
        assert result["newPatternId"] != before_pid


def test_replan_alt_topk_picks_second_rank_when_best_matches_current(monkeypatch) -> None:
    chapters, aspects, assets_map, mosaic_cfg = _chapters_with_aspects()
    screen = chapters[0]["screens"][0]
    sid = screen["screenId"]
    asset_ids = [sl["assetId"] for sl in screen["slots"]]
    current = str(screen["patternId"])

    def _fake_scored(*_args, **_kwargs):
        slots = [{"assetId": aid, "role": "main", "fit": "cover"} for aid in asset_ids]
        return [
            (
                ScreenCandidate(
                    current,
                    asset_ids,
                    {"patternId": current, "slots": slots},
                ),
                10.0,
                [],
                {},
            ),
            (
                ScreenCandidate(
                    "screen-mosaic-5-main-portrait-3land",
                    asset_ids,
                    {
                        "patternId": "screen-mosaic-5-main-portrait-3land",
                        "slots": slots,
                    },
                ),
                9.0,
                [],
                {},
            ),
        ]

    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.replan.score_window_candidates",
        _fake_scored,
    )
    result = replan_screen(
        chapters,
        sid,
        strategy="alt_topk",
        top_k=3,
        aspects=aspects,
        assets_map=assets_map,
        cfg=mosaic_cfg,
    )
    assert result["applied"] is True
    assert result["reason"] == "alt_topk"
    assert result["newPatternId"] == "screen-mosaic-5-main-portrait-3land"
    assert result["rank"] == 2


def test_replan_screen_syncs_chapter_items() -> None:
    from travelogue.curation.chapter_items import items_from_screens

    chapters, aspects, assets_map, mosaic_cfg = _chapters_with_aspects()
    sid = chapters[0]["screens"][0]["screenId"]
    replan_screen(
        chapters,
        sid,
        strategy="alt_topk",
        top_k=3,
        aspects=aspects,
        assets_map=assets_map,
        cfg=mosaic_cfg,
    )
    expected_items = items_from_screens(chapters[0])
    assert chapters[0].get("items") == expected_items
    assert collect_screen_asset_ids(chapters[0])


def test_replan_screen_legacy_builds_screen() -> None:
    # Pair-first tiling makes a 4-portrait run two portrait-2 pairs (2 slots
    # each), below the 3-slot replan window; use a 3-portrait run (portrait-3).
    buckets, aspects_map, assets = build_mosaic_portrait3_trip()
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
        cfg=_mosaic_cfg_for_golden().mosaic,
    )
    assert result["applied"] is True
    assert result["reason"] == "legacy"
    assert chapters[0]["screens"][0].get("slots")


def test_replan_legacy_blocked_when_usage_reject(monkeypatch) -> None:
    """BLK-10 / AC-TPC-05: replan(legacy) must not emit usage-rejected patterns."""
    chapters, aspects, assets_map, mosaic_cfg = _chapters_with_aspects()
    screen = chapters[0]["screens"][0]
    sid = screen["screenId"]
    previous = dict(screen)
    legacy_screen = {
        "patternId": "screen-mosaic-5-main-portrait-3land",
        "slots": list(screen.get("slots") or []),
    }

    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.replan.build_legacy_screen",
        lambda *_a, **_k: legacy_screen,
    )
    monkeypatch.setattr(
        "travelogue.layout_engine.usage_rules.evaluator.evaluate_reject",
        lambda *_a, **_k: (True, "UR-04", "portrait_hero_is_max"),
    )

    result = replan_screen(
        chapters,
        sid,
        strategy="legacy",
        aspects=aspects,
        assets_map=assets_map,
        cfg=mosaic_cfg,
    )
    assert result["applied"] is False
    assert result["reason"] == "legacy_usage_rejected"
    assert chapters[0]["screens"][0] == previous


def test_replan_screen_missing_context_raises() -> None:
    chapters, _, _, _ = _chapters_with_aspects()
    sid = chapters[0]["screens"][0]["screenId"]
    with pytest.raises(ReplanError, match="aspects"):
        replan_screen(chapters, sid)


def test_replan_screen_breath_pause_raises() -> None:
    chapters, aspects, assets_map, _ = _chapters_with_aspects()
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
    chapters, aspects, assets_map, _ = _chapters_with_aspects()
    with pytest.raises(ReplanError, match="not found"):
        replan_screen(chapters, "missing-screen", aspects=aspects, assets_map=assets_map)


def test_build_legacy_screen_portrait_four() -> None:
    from travelogue.layout_engine.mosaic.legacy import build_legacy_screen

    buckets, aspects_map, assets = build_mosaic_portrait4_trip()
    window = buckets[0]
    aspects = {aid: aspects_map[aid] for aid in window}
    assets_map = {a["id"]: a for a in assets}
    screen = build_legacy_screen(window, 4, aspects, assets_map, trip_total=4)
    assert screen is not None
    assert screen["patternId"] == "screen-portrait-4"
    assert len(screen.get("slots") or []) == 4


def test_legacy_append_rejects_retired_pattern(monkeypatch) -> None:
    """append_legacy_window must not append screens blocked by pattern_policy."""
    from travelogue.layout_engine.mosaic.constants import PATTERN_MOSAIC_5_2P_3L_BALANCED
    from travelogue.layout_engine.mosaic.legacy import append_legacy_window
    from travelogue.layout_engine.mosaic.lte_adapter import mosaic_pattern_disabled

    assert mosaic_pattern_disabled(PATTERN_MOSAIC_5_2P_3L_BALANCED)

    retired_screen = {
        "patternId": PATTERN_MOSAIC_5_2P_3L_BALANCED,
        "slots": [{"assetId": "a", "role": "main", "fit": "cover"}],
    }

    class _Ctx:
        aspects = {}
        assets_map = {}
        mix_gap = 12.0
        med_sharp = None
        trip_total = 40
        layout_state = None
        featured_weight = 1.0

    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.legacy.build_legacy_screen",
        lambda *a, **k: retired_screen,
    )
    assert append_legacy_window(_Ctx(), ["a", "b", "c", "d", "e"], 5) is False
