"""AC-P15-07 · mosaicDecisionLog field contract."""

from __future__ import annotations

from tests._golden.helpers import build_mosaic_five_2p3l_window
from travelogue.config import MosaicConfig
from travelogue.curation.mosaic.candidates import generate_five_candidates
from travelogue.curation.mosaic.compose import pick_best_candidate
from travelogue.curation.mosaic.runtime import MOSAIC_ROUTER_VERSION


def test_pick_best_logs_top3_reason_codes_router_version(lte_pattern_enabled) -> None:
    ids, aspects, assets_map = build_mosaic_five_2p3l_window()
    cfg = MosaicConfig(
        enabled=True,
        enabled_window_sizes=(5,),
        min_candidate_score=0.0,
        deterministic_strict=True,
    )
    cands = generate_five_candidates(
        ids, aspects, assets_map, cfg=cfg, burst_seconds=3600.0
    )
    assert len(cands) >= 1
    assert all(c.hard_valid for c in cands)
    assert all(c.feature_summary.get("windowSize") == 5 for c in cands)

    pick = pick_best_candidate(
        ids,
        aspects,
        assets_map,
        cfg=cfg,
        window_size=5,
        trip_photo_total=40,
        burst_seconds=3600.0,
    )
    raw = pick.log.to_dict()
    assert raw["routerVersion"] == MOSAIC_ROUTER_VERSION
    assert raw["scorerVersion"]
    assert raw["winnerPatternId"]
    assert raw["winnerReasonCodes"]
    assert len(raw.get("top3Patterns") or []) >= 1
    assert raw["candidatesCount"] >= 1
    assert pick.screen is not None
