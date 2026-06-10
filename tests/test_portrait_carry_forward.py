"""Cross-day-bucket carry-forward for lone portraits (web/screens, day scope).

A lone portrait left at the end of a day bucket is deferred forward (up to
``_PORTRAIT_CARRY_MAX_HOPS`` buckets) so it can pair with a later portrait,
minimising the number of single-portrait screens across the whole trip.
"""

from __future__ import annotations

from travelogue.curation.screen_planner import (
    _collect_asset_ids_from_chapter,
    attach_screens_to_chapters,
)


def _chapter(ch_id: str, asset_ids: list[str], **curation: object) -> dict:
    ch: dict = {
        "id": ch_id,
        "items": [{"type": "media-card", "assetId": aid} for aid in asset_ids],
    }
    if curation:
        ch["curation"] = dict(curation)
    return ch


def _all_screens(out: list[dict]) -> list[dict]:
    screens: list[dict] = []
    for ch in out:
        screens.extend(ch.get("screens") or [])
    return screens


def _patterns(out: list[dict]) -> list[str]:
    return [str(sc.get("patternId") or "") for sc in _all_screens(out)]


def _covered_assets(out: list[dict]) -> set[str]:
    ids: set[str] = set()
    for sc in _all_screens(out):
        for slot in sc.get("slots") or []:
            if slot.get("assetId"):
                ids.add(slot["assetId"])
    return ids


def test_two_lone_portraits_pair_across_day_buckets() -> None:
    chapters = [_chapter("ch-a", ["pa"]), _chapter("ch-b", ["pb"])]
    aspects = {"pa": "portrait", "pb": "portrait"}

    out = attach_screens_to_chapters(
        chapters,
        aspects,
        plan_scope="day",
        day_buckets=[["pa"], ["pb"]],
    )

    patterns = _patterns(out)
    assert "screen-portrait-1" not in patterns
    assert "screen-portrait-2" in patterns
    assert _covered_assets(out) == {"pa", "pb"}


def test_odd_lone_portraits_reduce_to_single_tail() -> None:
    chapters = [
        _chapter("ch-a", ["pa"]),
        _chapter("ch-b", ["pb"]),
        _chapter("ch-c", ["pc"]),
    ]
    aspects = {"pa": "portrait", "pb": "portrait", "pc": "portrait"}

    out = attach_screens_to_chapters(
        chapters,
        aspects,
        plan_scope="day",
        day_buckets=[["pa"], ["pb"], ["pc"]],
    )

    patterns = _patterns(out)
    # Three lone portraits collapse to one pair + at most one trailing single.
    assert patterns.count("screen-portrait-2") >= 1
    assert patterns.count("screen-portrait-1") <= 1
    assert _covered_assets(out) == {"pa", "pb", "pc"}


def test_single_lone_portrait_still_rendered() -> None:
    chapters = [_chapter("ch-a", ["pa"])]
    aspects = {"pa": "portrait"}

    out = attach_screens_to_chapters(
        chapters,
        aspects,
        plan_scope="day",
        day_buckets=[["pa"]],
    )

    # Nothing to pair with: the carried portrait must still be emitted, not lost.
    assert _patterns(out) == ["screen-portrait-1"]
    assert _covered_assets(out) == {"pa"}
    assert set(_collect_asset_ids_from_chapter(out[0])) == {"pa"}


def test_featured_lone_portrait_is_not_carried() -> None:
    chapters = [_chapter("ch-a", ["pa"]), _chapter("ch-b", ["pb"])]
    aspects = {"pa": "portrait", "pb": "portrait"}
    assets = [
        {"id": "pa", "userTier": "featured"},
        {"id": "pb"},
    ]

    out = attach_screens_to_chapters(
        chapters,
        aspects,
        assets=assets,
        plan_scope="day",
        day_buckets=[["pa"], ["pb"]],
    )

    patterns = _patterns(out)
    # Featured pa stays a deliberate single in ch-a; pb has no partner -> single.
    assert patterns.count("screen-portrait-1") == 2
    pa_screen = next(
        sc for sc in _all_screens(out) if sc["slots"][0]["assetId"] == "pa"
    )
    assert pa_screen["patternId"] == "screen-portrait-1"
    assert _covered_assets(out) == {"pa", "pb"}
