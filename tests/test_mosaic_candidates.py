"""Phase 15 mosaic candidate generation."""

from __future__ import annotations

from travelogue.config import MosaicConfig
from travelogue.curation.layout_planner import aspect_kind_for_asset
from travelogue.curation.mosaic.candidates import generate_window_candidates
from travelogue.curation.mosaic.constants import PATTERN_PORTRAIT_2_LANDSCAPE_2

from tests._golden.helpers import build_mixed_aspects_trip


def _five_assets():
    kinds = ["portrait", "portrait", "landscape", "landscape", "landscape"]
    aspects = {}
    assets_map = {}
    for i, kind in enumerate(kinds):
        aid = f"a{i}"
        aspects[aid] = kind
        assets_map[aid] = {
            "id": aid,
            "width": 1600 if kind == "landscape" else 900,
            "height": 900 if kind == "landscape" else 1600,
            "takenAt": "2024-06-01T10:00:00Z",
            "layoutEligible": True,
        }
    return aspects, assets_map


def test_generate_window_candidates_multiple_patterns():
    aspects, assets_map = _five_assets()
    cfg = MosaicConfig(enabled=True, enabled_window_sizes=(5,))
    cands = generate_window_candidates(
        list(aspects.keys()),
        aspects,
        assets_map,
        cfg=cfg,
        burst_seconds=3600.0,
    )
    assert len(cands) >= 2
    pids = {c.pattern_id for c in cands}
    assert all(p.startswith("screen-mosaic-5-") for p in pids)


def test_time_gap_still_yields_candidates_lower_score():
    """Soft time: far-apart assets still get candidates (scored lower in planner)."""
    aspects, assets_map = _five_assets()
    assets_map["a3"]["takenAt"] = "2024-06-01T12:00:00Z"
    assets_map["a4"]["takenAt"] = "2024-06-01T13:00:00Z"
    cfg = MosaicConfig(enabled=True, enabled_window_sizes=(5,), min_candidate_score=0.0)
    cands = generate_window_candidates(
        list(aspects.keys()),
        aspects,
        assets_map,
        cfg=cfg,
        burst_seconds=3.0,
    )
    assert cands


def test_generate_mixed_four_window_includes_p2_l2():
    buckets, aspects, assets = build_mixed_aspects_trip()
    assets_map = {a["id"]: a for a in assets}
    cfg = MosaicConfig(enabled=True, enabled_window_sizes=(4,))
    cands = generate_window_candidates(
        buckets[0],
        aspects,
        assets_map,
        cfg=cfg,
        burst_seconds=3600.0,
    )
    pids = {c.pattern_id for c in cands}
    assert PATTERN_PORTRAIT_2_LANDSCAPE_2 in pids
