"""LTN C4 · coarse segments + signature routing."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

from travelogue.config import get_config
from travelogue.layout_engine.mosaic.coarse_segments import (
    CoarseSegment,
    apply_signature_route,
    build_coarse_segments,
    max_window_size_in_segment,
    signature_key,
    window_crosses_segment,
)
from travelogue.layout_engine.mosaic.candidates import generate_window_candidates_with_rejections
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_LANDSCAPE_4,
    PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
)
from travelogue.layout_engine.mosaic.pattern_catalog import patterns_for_window_size
from travelogue.layout_engine.planner.screen_planner_stages import build_chapter_plan_context


def _iso(base: datetime, seconds: float = 0) -> str:
    return (base + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def _asset(
    aid: str,
    *,
    taken_offset_s: float,
    base: datetime,
    city: str | None = "Tokyo",
    orientation: str = "landscape",
) -> dict:
    place = {"city": city} if city else {}
    w, h = (1600, 900) if orientation == "landscape" else (900, 1600)
    return {
        "id": aid,
        "takenAt": _iso(base, taken_offset_s),
        "place": place,
        "width": w,
        "height": h,
        "orientation": orientation,
    }


def test_build_coarse_segments_splits_on_time_gap():
    base = datetime(2025, 6, 1, 10, 0, tzinfo=timezone.utc)
    # tight burst then a long pause then another burst
    ids = [f"a{i}" for i in range(6)]
    assets = {
        "a0": _asset("a0", taken_offset_s=0, base=base),
        "a1": _asset("a1", taken_offset_s=30, base=base),
        "a2": _asset("a2", taken_offset_s=60, base=base),
        "a3": _asset("a3", taken_offset_s=60 + 2000, base=base),
        "a4": _asset("a4", taken_offset_s=60 + 2030, base=base),
        "a5": _asset("a5", taken_offset_s=60 + 2060, base=base),
    }
    segs = build_coarse_segments(ids, assets)
    assert len(segs) == 2
    assert segs[0] == CoarseSegment(0, 3)
    assert segs[1] == CoarseSegment(3, 6)


def test_build_coarse_segments_splits_on_city_change():
    base = datetime(2025, 6, 1, 10, 0, tzinfo=timezone.utc)
    ids = ["a0", "a1", "a2", "a3"]
    assets = {
        "a0": _asset("a0", taken_offset_s=0, base=base, city="Tokyo"),
        "a1": _asset("a1", taken_offset_s=20, base=base, city="Tokyo"),
        "a2": _asset("a2", taken_offset_s=40, base=base, city="Osaka"),
        "a3": _asset("a3", taken_offset_s=60, base=base, city="Osaka"),
    }
    segs = build_coarse_segments(ids, assets)
    assert segs == [CoarseSegment(0, 2), CoarseSegment(2, 4)]


def test_missing_timestamp_sticks_to_previous_segment():
    base = datetime(2025, 6, 1, 10, 0, tzinfo=timezone.utc)
    ids = ["a0", "a1", "a2"]
    assets = {
        "a0": _asset("a0", taken_offset_s=0, base=base),
        "a1": {"id": "a1", "width": 1600, "height": 900, "orientation": "landscape"},
        "a2": _asset("a2", taken_offset_s=5000, base=base),
    }
    segs = build_coarse_segments(ids, assets)
    # a1 has no ts → no split before it; a2 vs a0 has huge gap but a1 sits between —
    # split only when both adjacent have timestamps: a1↔a2 can't, a0↔a1 can't.
    # So one segment (stick rule).
    assert segs == [CoarseSegment(0, 3)]


def test_window_clamp_prevents_cross_segment():
    segs = [CoarseSegment(0, 3), CoarseSegment(3, 8)]
    assert max_window_size_in_segment(segs, 0) == 3
    assert max_window_size_in_segment(segs, 2) == 1
    assert max_window_size_in_segment(segs, 3) == 5
    assert window_crosses_segment(segs, 1, 4) is True
    assert window_crosses_segment(segs, 1, 2) is False


def test_chapter_context_attaches_coarse_segments():
    base = datetime(2025, 6, 1, 10, 0, tzinfo=timezone.utc)
    ids = ["a0", "a1", "a2", "a3"]
    assets = {
        "a0": _asset("a0", taken_offset_s=0, base=base, city="Tokyo"),
        "a1": _asset("a1", taken_offset_s=20, base=base, city="Tokyo"),
        "a2": _asset("a2", taken_offset_s=40, base=base, city="Osaka"),
        "a3": _asset("a3", taken_offset_s=60, base=base, city="Osaka"),
    }
    aspects = {aid: "landscape" for aid in ids}
    ctx = build_chapter_plan_context(ids, aspects, assets=assets, enable_mosaic=True)
    assert len(ctx.coarse_segments) == 2


def test_signature_route_cohesive_four_landscape():
    base = datetime(2025, 6, 1, 10, 0, tzinfo=timezone.utc)
    ids = ["a0", "a1", "a2", "a3"]
    assets = {
        aid: _asset(aid, taken_offset_s=i * 40, base=base) for i, aid in enumerate(ids)
    }
    aspects = {aid: "landscape" for aid in ids}
    assert signature_key(ids, aspects, assets) == (0, 4, True)
    patterns = patterns_for_window_size(4)
    narrowed, source = apply_signature_route(patterns, ids, aspects, assets)
    ids_out = {p.pattern_id for p in narrowed}
    assert source == "signature"
    assert ids_out == {PATTERN_LANDSCAPE_4, "screen-mosaic-4-hero-70-sidebar"}


def test_signature_route_non_cohesive_drops_hero():
    base = datetime(2025, 6, 1, 10, 0, tzinfo=timezone.utc)
    ids = ["a0", "a1", "a2", "a3"]
    assets = {
        aid: _asset(aid, taken_offset_s=i * 200, base=base) for i, aid in enumerate(ids)
    }
    aspects = {aid: "landscape" for aid in ids}
    assert signature_key(ids, aspects, assets) == (0, 4, False)
    patterns = patterns_for_window_size(4)
    narrowed, source = apply_signature_route(patterns, ids, aspects, assets)
    assert source == "signature"
    assert {p.pattern_id for p in narrowed} == {PATTERN_LANDSCAPE_4}


def test_signature_fallback_unknown_mix():
    base = datetime(2025, 6, 1, 10, 0, tzinfo=timezone.utc)
    ids = ["a0", "a1", "a2", "a3"]
    assets = {
        "a0": _asset("a0", taken_offset_s=0, base=base, orientation="portrait"),
        "a1": _asset("a1", taken_offset_s=10, base=base, orientation="portrait"),
        "a2": _asset("a2", taken_offset_s=20, base=base, orientation="portrait"),
        "a3": _asset("a3", taken_offset_s=30, base=base, orientation="landscape"),
    }
    aspects = {
        "a0": "portrait",
        "a1": "portrait",
        "a2": "portrait",
        "a3": "landscape",
    }
    patterns = patterns_for_window_size(4)
    narrowed, source = apply_signature_route(patterns, ids, aspects, assets)
    assert source == "signature_fallback"
    assert len(narrowed) == len(patterns)


def test_candidates_log_signature_source():
    base = datetime(2025, 6, 1, 10, 0, tzinfo=timezone.utc)
    ids = ["a0", "a1", "a2", "a3"]
    assets = {
        aid: _asset(aid, taken_offset_s=i * 40, base=base) for i, aid in enumerate(ids)
    }
    aspects = {aid: "landscape" for aid in ids}
    cfg = replace(get_config().mosaic)
    # Isolate from local template_contract dogfood.
    if getattr(cfg, "template_contract", None) is not None:
        cfg = replace(cfg, template_contract=replace(cfg.template_contract, enabled=False))
    result = generate_window_candidates_with_rejections(
        ids, aspects, assets, cfg=cfg, burst_seconds=12.0
    )
    assert result.contract_shadow is not None
    assert result.contract_shadow.get("candidateSource") == "signature"
    live = set(result.contract_shadow.get("livePatternIds") or [])
    # livePatternIds tracks orderable before/after — at least signature patterns attempted
    assert PATTERN_LANDSCAPE_4 in {c.pattern_id for c in result.candidates} or live


def test_signature_five_slot_main():
    base = datetime(2025, 6, 1, 10, 0, tzinfo=timezone.utc)
    ids = ["a0", "a1", "a2", "a3", "a4"]
    assets = {
        "a0": _asset("a0", taken_offset_s=0, base=base, orientation="portrait"),
        "a1": _asset("a1", taken_offset_s=20, base=base),
        "a2": _asset("a2", taken_offset_s=40, base=base),
        "a3": _asset("a3", taken_offset_s=60, base=base),
        "a4": _asset("a4", taken_offset_s=80, base=base),
    }
    aspects = {
        "a0": "portrait",
        "a1": "landscape",
        "a2": "landscape",
        "a3": "landscape",
        "a4": "landscape",
    }
    patterns = patterns_for_window_size(5)
    narrowed, source = apply_signature_route(patterns, ids, aspects, assets)
    assert source == "signature"
    assert PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND in {p.pattern_id for p in narrowed}
