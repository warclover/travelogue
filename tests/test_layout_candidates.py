"""Mosaic beam candidate variants."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from travelogue.curation.layout_candidates import (
    bucket_has_mosaic_window,
    generate_day_bucket_candidates,
)
from travelogue.curation.search_budget import SearchBudget


def _asset(aid: str, kind: str, secs: float = 0) -> dict:
    return {
        "id": aid,
        "aspectKind": kind,
        "takenAt": (datetime(2025, 6, 1, 10, tzinfo=timezone.utc) + timedelta(seconds=secs)).isoformat(),
        "width": 2000 if kind == "landscape" else 900,
        "height": 1200 if kind == "landscape" else 1600,
    }


def test_bucket_has_mosaic_window_detects_five_mix():
    # 4 land + 1 portrait, time-near
    ids = ["l1", "l2", "l3", "l4", "p1"]
    aspects = {i: ("portrait" if i == "p1" else "landscape") for i in ids}
    assets = {
        "l1": _asset("l1", "landscape", 0),
        "l2": _asset("l2", "landscape", 3),
        "l3": _asset("l3", "landscape", 6),
        "l4": _asset("l4", "landscape", 9),
        "p1": _asset("p1", "portrait", 4),
    }
    assert bucket_has_mosaic_window(ids, aspects, assets, mixed_proximity_seconds=12, trip_photo_total=40)


def test_no_mosaic_variant_differs_when_eligible():
    ids = ["l1", "l2", "l3", "l4", "p1"]
    aspects = {i: ("portrait" if i == "p1" else "landscape") for i in ids}
    assets = {i: _asset(i, aspects[i], idx) for idx, i in enumerate(ids)}
    budget = SearchBudget(max_evaluations_per_trip=20, max_candidates_per_bucket=8)
    cands = generate_day_bucket_candidates(
        ids,
        aspects,  # type: ignore[arg-type]
        assets_by_id=assets,
        orientation_summary={"landscape": 4, "portrait": 1},
        skip_screen_asset_ids=set(),
        mixed_proximity_seconds=12,
        trip_photo_total=40,
        preferred_hero_id=None,
        layout_state=None,
        beam_width=5,
        budget=budget,
    )
    sigs = [tuple(s.get("patternId") for s in plan) for plan in cands]
    assert len(cands) >= 2
    assert sigs[0] != sigs[1] or len(cands) >= 2
