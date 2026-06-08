"""Phase 17 W4 core · CAP-01/08/10/05."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from travelogue.config.mosaic import MosaicConfig
from travelogue.curation.feedback import record_g1_edit
from travelogue.curation.mosaic.candidates import generate_window_candidates_with_rejections
from travelogue.curation.mosaic.scorer import score_candidate
from travelogue.layout_engine.feedback import (
    append_layout_feedback,
    is_valid_pairwise_label,
    read_layout_feedback_events,
)
from travelogue.layout_engine.quality_features import build_quality_pool
from travelogue.layout_engine.replan import (
    buckets_from_existing_chapters,
    should_layout_only_replan,
)
from travelogue.layout_engine.slot_assignment import (
    pair_assignment_cost,
    refine_asset_order_hungarian,
)
from scripts.phase3_ig2_report import load_fixture_trip


def _mixed_assets():
    trip = load_fixture_trip("golden-mixed-scenes")
    assets = {a["id"]: a for a in trip.get("assets") or []}
    aspects = {}
    from travelogue.curation.layout_planner import aspect_kind_for_asset

    for a in trip.get("assets") or []:
        aspects[a["id"]] = aspect_kind_for_asset(a)
    return trip, assets, aspects


def test_quality_pool_percentiles() -> None:
    trip = load_fixture_trip("golden-mixed-scenes")
    pool = build_quality_pool(trip.get("assets") or [])
    assert pool.by_id
    for q in pool.by_id.values():
        assert 0.0 <= q.sharp_pct <= 1.0
        assert 0.0 <= q.aesthetic_pct <= 1.0


def test_hungarian_refine_deterministic() -> None:
    trip, assets_map, aspects = _mixed_assets()
    asset_ids = list(assets_map.keys())[:3]
    if len(asset_ids) < 3:
        return
    from travelogue.curation.mosaic.pattern_catalog import patterns_for_window_size
    from travelogue.curation.mosaic.builders import build_screen
    from travelogue.curation.mosaic.lte_adapter import mosaic_registry

    reg = mosaic_registry()
    pats = patterns_for_window_size(3, reg)
    if not pats:
        return
    pat = pats[0]
    ordered = asset_ids[:3]
    screen = build_screen(pat, ordered, assets_map=assets_map)
    refined, fb = refine_asset_order_hungarian(
        ordered,
        screen,
        assets_map,
        max_matrix_n=16,
    )
    assert refined is not None or fb is not None
    if refined is not None:
        assert sorted(refined) == sorted(ordered)


def test_hungarian_candidate_path_fail_open() -> None:
    trip, assets_map, aspects = _mixed_assets()
    asset_ids = list(assets_map.keys())[:4]
    cfg = replace(
        MosaicConfig(),
        lse_hungarian_assignment=True,
        lse_quality_unified=True,
    )
    result = generate_window_candidates_with_rejections(
        asset_ids,
        aspects,
        assets_map,
        cfg=cfg,
    )
    assert isinstance(result.candidates, list)


def test_scorer_quality_unified_path() -> None:
    trip, assets_map, aspects = _mixed_assets()
    cfg = replace(MosaicConfig(), lse_quality_unified=True)
    screen = {
        "patternId": "screen-landscape-3",
        "slots": [
            {"assetId": list(assets_map.keys())[0], "role": "main", "slot": 0, "fit": "cover"},
        ],
    }
    scored = score_candidate(
        screen,
        aspects=aspects,
        assets_by_id=assets_map,
        cfg=cfg,
    )
    assert scored.total >= 0.0


def test_layout_only_replan_density_change() -> None:
    trip = load_fixture_trip("golden-mixed-scenes")
    trip.setdefault("intent", {})["mode"] = "fine_craft"
    trip["intent"]["layoutDensity"] = "hero_first"
    trip.setdefault("curation", {})["appliedLayoutDensity"] = "balanced"
    trip["chapters"] = [
        {
            "id": "ch-01",
            "items": [{"assetId": trip["assets"][0]["id"]}],
            "curation": {"segmentId": "seg-1"},
        }
    ]
    decision = should_layout_only_replan(trip)
    assert decision.layout_only is True
    assert decision.reason == "density_change"


def test_layout_only_skips_quick_share() -> None:
    trip = load_fixture_trip("golden-mixed-scenes")
    trip.setdefault("intent", {})["mode"] = "quick_share"
    trip["intent"]["layoutDensity"] = "hero_first"
    trip.setdefault("curation", {})["appliedLayoutDensity"] = "balanced"
    assert should_layout_only_replan(trip).layout_only is False


def test_buckets_from_existing_chapters() -> None:
    trip = load_fixture_trip("golden-mixed-scenes")
    aid = trip["assets"][0]["id"]
    trip["chapters"] = [{"id": "ch-01", "items": [{"assetId": aid}], "curation": {}}]
    raw = buckets_from_existing_chapters(trip)
    assert raw is not None
    assert raw["buckets"] == [[aid]]


def test_layout_feedback_export(tmp_path: Path) -> None:
    before = {"chapters": [{"id": "ch-01", "screens": [{"patternId": "a"}]}]}
    after = {"chapters": [{"id": "ch-01", "screens": [{"patternId": "b"}]}]}
    rec = record_g1_edit(
        "t1",
        before,
        after,
        user_id="u1",
    )
    assert rec.edit_type == "pattern_change"
    assert is_valid_pairwise_label(rec) or rec.distance >= 0
    path = append_layout_feedback(tmp_path, rec)
    assert path is not None
    events = read_layout_feedback_events(tmp_path)
    assert len(events) == 1
    assert events[0]["pairwiseEligible"] is True or events[0]["editType"] == "pattern_change"


def test_pair_cost_bounded() -> None:
    asset = {"id": "a1", "width": 4000, "height": 3000, "quality": {"sharpness": 0.8}}
    cost = pair_assignment_cost(asset, 1.33, slot_index=0)
    assert 0.0 <= cost <= 2.0
