"""Replan must keep items[] aligned with screens[]."""

from __future__ import annotations

from tests._golden.helpers import build_portrait_heavy_trip, plan_legacy_screens
from travelogue.curation.chapter_items import collect_screen_asset_ids, item_asset_ids
from travelogue.curation.degradation import assess_degradation
from travelogue.curation.layout_scoring import PHASE2_WEIGHTS
from travelogue.curation.layout_search import maybe_replan_chapters


def test_replan_then_compact_items_match_screens(monkeypatch) -> None:
    buckets, aspects, assets = build_portrait_heavy_trip()
    legacy = plan_legacy_screens(buckets, aspects, assets)
    alt_screens = [
        {
            "patternId": "screen-portrait-2",
            "slots": [{"assetId": "a1"}, {"assetId": "a2"}],
        }
    ]

    def _fake_candidates(*_args, **_kwargs):
        return [("legacy", legacy[0].get("screens") or []), ("alt", alt_screens)]

    monkeypatch.setattr(
        "travelogue.curation.layout_search.generate_day_bucket_candidates",
        _fake_candidates,
    )
    replanned, meta = maybe_replan_chapters(
        legacy,
        buckets=buckets,
        aspects=aspects,  # type: ignore[arg-type]
        assets=assets,
        scoring_enabled=True,
        weights=PHASE2_WEIGHTS,
        beam_width=3,
        degradation=assess_degradation(assets, aspects, min_layout_eligible=3),
        orientation_summary={"portrait": 6, "landscape": 0},
        trip_photo_total=len(assets),
        max_consecutive_same_pattern=0,
    )
    assert meta.get("replanApplied")
    from travelogue.curation.chapter_items import compact_chapter_items_for_screens

    compact_chapter_items_for_screens(replanned)
    for ch in replanned:
        if not ch.get("screens"):
            continue
        screen_ids = collect_screen_asset_ids(ch)
        item_ids: list[str] = []
        for it in ch.get("items") or []:
            item_ids.extend(item_asset_ids(it))
        assert set(screen_ids).issubset(set(item_ids))
