"""Deterministic compose signatures (AC-P15-04)."""

from __future__ import annotations

from travelogue.config import MosaicConfig
from travelogue.curation.layout_search import _screens_signature
from travelogue.curation.mosaic.compose import pick_best_five_window

from tests._golden.helpers import build_mosaic_eligible_trip, plan_mosaic_screens


def test_pick_best_five_stable_signature():
    buckets, aspects, assets = build_mosaic_eligible_trip()
    assets_map = {a["id"]: a for a in assets}
    cfg = MosaicConfig(
        enabled=True,
        enabled_window_sizes=(5,),
        deterministic_strict=True,
        min_candidate_score=0.0,
    )
    ids = buckets[0]
    r1 = pick_best_five_window(ids, aspects, assets_map, cfg=cfg, trip_photo_total=40)
    r2 = pick_best_five_window(ids, aspects, assets_map, cfg=cfg, trip_photo_total=40)
    assert r1.log.winner_pattern_id == r2.log.winner_pattern_id
    assert r1.screen and r2.screen
    assert r1.screen["patternId"] == r2.screen["patternId"]


def test_plan_mosaic_chapter_signature_stable():
    buckets, aspects, assets = build_mosaic_eligible_trip()
    ch1 = plan_mosaic_screens([buckets[0]], aspects, assets)
    ch2 = plan_mosaic_screens([buckets[0]], aspects, assets)
    assert _screens_signature(ch1) == _screens_signature(ch2)
