"""R-MAIN-AR-01 · hero+tile main slot aspect eligibility."""

from __future__ import annotations

from dataclasses import replace

import pytest

from travelogue.config import MosaicConfig
from travelogue.curation.mosaic.builders import try_order_for_pattern
from travelogue.curation.mosaic.candidates import generate_window_candidates_with_rejections
from travelogue.curation.mosaic.constants import (
    PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
)
from travelogue.curation.mosaic.main_eligibility import (
    asset_eligible_for_main_slot,
    pick_best_main_eligible,
    screen_main_slot_eligible,
)
from travelogue.curation.mosaic.pattern_catalog import default_registry
from travelogue.curation.mosaic.scorer import score_candidate


def _asset(aid: str, *, w: int, h: int, sharp: float = 0.8) -> dict:
    return {
        "id": aid,
        "width": w,
        "height": h,
        "takenAt": f"2024-06-01T12:00:{int(aid[-1]) if aid[-1].isdigit() else 0:02d}Z",
        "quality": {"sharpness": sharp},
    }


def test_panorama_blocked_for_main():
    asset = _asset("pano", w=5000, h=2000)
    ok, reason = asset_eligible_for_main_slot(asset)
    assert not ok
    assert reason == "blocked_panorama"


def test_ultra_wide_blocked_for_main():
    asset = _asset("wide", w=2800, h=1000)
    ok, reason = asset_eligible_for_main_slot(asset)
    assert not ok
    assert reason == "blocked_panorama"


def test_conventional_16_9_eligible():
    asset = _asset("std", w=3000, h=1687)
    ok, reason = asset_eligible_for_main_slot(asset)
    assert ok
    assert reason == "ok"


def test_off_ladder_landscape_blocked():
    asset = _asset("odd", w=1900, h=1000)
    ok, reason = asset_eligible_for_main_slot(asset)
    assert not ok
    assert reason == "blocked_off_ladder"


def test_pick_best_main_skips_panorama():
    assets_map = {
        "pano": _asset("pano", w=5000, h=2000, sharp=0.95),
        "good": _asset("good", w=3000, h=1687, sharp=0.7),
    }
    picked = pick_best_main_eligible(["pano", "good"], assets_map)
    assert picked == "good"


def test_order_hero_six_rejects_window_without_eligible_main():
    aspects = {f"l{i}": "landscape" for i in range(4)}
    aspects["p1"] = "portrait"
    aspects["p2"] = "portrait"
    assets_map = {
        "l0": _asset("l0", w=5000, h=2000),
        "l1": _asset("l1", w=5000, h=2000),
        "l2": _asset("l2", w=5000, h=2000),
        "l3": _asset("l3", w=5000, h=2000),
        "p1": _asset("p1", w=1200, h=1800),
        "p2": _asset("p2", w=1200, h=1800),
    }
    ordered = try_order_for_pattern(
        PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
        list(aspects.keys()),
        aspects,
        assets_map,
        burst_seconds=3600,
        median_sharp=0.5,
    )
    assert ordered is None


def test_candidates_reject_hero6_when_no_eligible_main():
    cfg = MosaicConfig()
    aspects = {f"a{i}": "landscape" for i in range(6)}
    assets_map = {f"a{i}": _asset(f"a{i}", w=1900, h=1000) for i in range(6)}
    window = [f"a{i}" for i in range(6)]
    result = generate_window_candidates_with_rejections(
        window,
        aspects,
        assets_map,
        cfg=cfg,
    )
    hero_rejects = [
        r
        for r in result.rejected
        if r.get("templateId") == PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5
    ]
    assert hero_rejects
    assert hero_rejects[0].get("reason") in ("main_ar_ineligible", "ordering_failed")


def test_scorer_penalizes_ineligible_main():
    cfg = MosaicConfig()
    aspects = {"main": "landscape", "t1": "landscape"}
    assets_map = {
        "main": _asset("main", w=5000, h=2000),
        "t1": _asset("t1", w=3000, h=1687),
    }
    slots = [
        {"assetId": "main", "slot": 0, "fit": "cover", "role": "main"},
        {"assetId": "t1", "slot": 1, "fit": "cover", "role": "tile"},
    ]
    for i in range(2, 6):
        aid = f"t{i}"
        aspects[aid] = "landscape"
        assets_map[aid] = _asset(aid, w=3000, h=1687)
        slots.append({"assetId": aid, "slot": i, "fit": "cover", "role": "tile"})
    screen = {"patternId": PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5, "slots": slots}
    result = score_candidate(
        screen,
        aspects=aspects,
        assets_by_id=assets_map,
        cfg=cfg,
        trip_photo_total=50,
    )
    assert result.penalties.get("main_ar_ineligible", 0.0) >= 0.5
    assert "R_MAIN_AR_BLOCK" in result.reason_codes


def test_main_ar_guard_disabled_allows_panorama_main():
    cfg = replace(MosaicConfig(), main_ar_guard=False)
    screen = {
        "patternId": PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
        "slots": [{"assetId": "main", "slot": 0, "role": "main"}],
    }
    assets_map = {"main": _asset("main", w=5000, h=2000)}
    ok, reason = screen_main_slot_eligible(
        screen,
        assets_map,
        pattern_id=PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
        cfg=cfg,
    )
    assert ok
    assert reason == "ok"


def test_hero_main_conventional_rate_metrics():
    from travelogue.curation.mosaic.constants import PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5
    from travelogue.curation.mosaic.metrics import (
        compute_mosaic_metrics,
        hero_main_conventional_rate,
    )

    good = {
        "id": "good",
        "width": 3000,
        "height": 1687,
        "quality": {"sharpness": 0.8},
    }
    bad = {
        "id": "bad",
        "width": 5000,
        "height": 2000,
        "quality": {"sharpness": 0.8},
    }
    assets = {"good": good, "bad": bad}
    chapters_ok = [
        {
            "screens": [
                {
                    "patternId": PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
                    "slots": [{"assetId": "good", "role": "main", "slot": 0}],
                }
            ]
        }
    ]
    chapters_bad = [
        {
            "screens": [
                {
                    "patternId": PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
                    "slots": [{"assetId": "bad", "role": "main", "slot": 0}],
                }
            ]
        }
    ]
    assert hero_main_conventional_rate(chapters_ok, assets) == 1.0
    assert hero_main_conventional_rate(chapters_bad, assets) == 0.0
    metrics = compute_mosaic_metrics(chapters_ok, assets_by_id=assets)
    assert metrics["hero6WithConventionalMainRate"] == 1.0


def test_main_ar_reject_rate_from_mosaic_window_log():
    from travelogue.curation.mosaic.log import MosaicWindowLog, format_log_entry
    from travelogue.curation.mosaic.metrics import compute_mosaic_metrics, main_ar_reject_rate

    raw = MosaicWindowLog(
        rejected_templates=[
            {
                "templateId": PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
                "reason": "main_ar_ineligible",
                "detail": "blocked_off_ladder",
            },
            {"templateId": "screen-landscape-6", "reason": "geometry_invalid"},
        ],
        winner_pattern_id="screen-landscape-6",
    ).to_dict()
    assert main_ar_reject_rate([raw]) == 1.0
    window = format_log_entry(raw, "window")
    assert window["mainArRejectedTemplates"][0]["detail"] == "blocked_off_ladder"
    assert main_ar_reject_rate([window]) == 1.0
    metrics = compute_mosaic_metrics([], mosaic_logs=[raw])
    assert metrics["mainArRejectRate"] == 1.0
    assert metrics["hero6FallbackRate"] == 1.0
    assert metrics["hero6FallbackPatternCounts"] == {"screen-landscape-6": 1}


def test_hungarian_reorder_ineligible_main_hard_invalid():
    """AC-M6-04 · Hungarian cannot bypass main AR hard_valid after reorder."""
    cfg = MosaicConfig(lse_hungarian_assignment=True)
    aspects = {f"a{i}": "landscape" for i in range(6)}
    assets_map = {
        **{f"a{i}": _asset(f"a{i}", w=3000, h=1687) for i in range(5)},
        "a5": _asset("a5", w=5000, h=2000),
    }
    window = [f"a{i}" for i in range(6)]
    result = generate_window_candidates_with_rejections(
        window,
        aspects,
        assets_map,
        cfg=cfg,
    )
    hero_cands = [c for c in result.candidates if c.pattern_id == PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5]
    if hero_cands:
        assert not hero_cands[0].hard_valid or screen_main_slot_eligible(
            hero_cands[0].screen,
            assets_map,
            pattern_id=PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
        )[0]


def test_scorer_penalizes_hungarian_bypass_when_guard_off():
    """AC-M6-04 · scorer penalty when guard off and panorama occupies main slot."""
    cfg = replace(MosaicConfig(), main_ar_guard=False)
    aspects = {f"t{i}": "landscape" for i in range(6)}
    assets_map = {
        "main": _asset("main", w=5000, h=2000),
        **{f"t{i}": _asset(f"t{i}", w=3000, h=1687) for i in range(1, 6)},
    }
    slots = [
        {"assetId": "main", "slot": 0, "fit": "cover", "role": "main"},
    ]
    for i in range(1, 6):
        slots.append({"assetId": f"t{i}", "slot": i, "fit": "cover", "role": "tile"})
    screen = {"patternId": PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5, "slots": slots}
    result = score_candidate(
        screen,
        aspects=aspects,
        assets_by_id=assets_map,
        cfg=cfg,
        trip_photo_total=50,
    )
    assert result.penalties.get("main_ar_ineligible", 0.0) == 0.0
    cfg_guard = MosaicConfig()
    guarded = score_candidate(
        screen,
        aspects=aspects,
        assets_by_id=assets_map,
        cfg=cfg_guard,
        trip_photo_total=50,
    )
    assert guarded.penalties.get("main_ar_ineligible", 0.0) >= 0.5


def test_template_main_slot_policy_loaded():
    from travelogue.curation.mosaic.constants import PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5
    from travelogue.curation.mosaic.main_eligibility import (
        pattern_requires_main_ar_guard,
        resolve_main_eligible_kinds,
        resolve_main_forbid_kinds,
        template_main_slot_policy,
    )

    policy = template_main_slot_policy(PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5)
    assert policy is not None
    assert policy.get("slotIndex") == 0
    assert pattern_requires_main_ar_guard(PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5)
    assert resolve_main_forbid_kinds(PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5) == frozenset(
        {"panorama", "tall", "portrait", "square"}
    )
    assert resolve_main_eligible_kinds(PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5) == frozenset(
        {"landscape"}
    )


def test_resolve_main_target_display_ar_from_yaml():
    from travelogue.curation.mosaic.main_eligibility import (
        resolve_main_target_display_ar,
        resolve_prefer_ladder,
    )

    target = resolve_main_target_display_ar(PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5)
    assert abs(target - (16 / 9)) <= 0.001
    ladder = resolve_prefer_ladder(PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5)
    assert ladder[0] == pytest.approx(16 / 9, rel=1e-3)
    assert 1.5 in ladder


def test_pick_best_main_prefers_16_9_over_3_2_at_equal_hero():
    assets_map = {
        "wide32": _asset("wide32", w=3000, h=2000, sharp=0.8),
        "wide169": _asset("wide169", w=3000, h=1687, sharp=0.8),
    }
    picked = pick_best_main_eligible(
        ["wide32", "wide169"],
        assets_map,
        pattern_id=PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
    )
    assert picked == "wide169"


def test_forbid_kinds_runtime_enforcement():
    pano = _asset("pano", w=5000, h=2000)
    ok, reason = asset_eligible_for_main_slot(
        pano,
        forbid_kinds=frozenset({"panorama", "portrait"}),
        eligible_kinds=frozenset({"landscape", "panorama"}),
    )
    assert not ok
    assert reason == "blocked_panorama"

    ok_relaxed, reason_relaxed = asset_eligible_for_main_slot(
        pano,
        forbid_kinds=frozenset({"portrait"}),
        eligible_kinds=frozenset({"landscape", "panorama"}),
    )
    assert not ok_relaxed
    assert reason_relaxed == "blocked_off_ladder"


def test_eligible_kinds_must_include_landscape_from_yaml():
    asset = _asset("std", w=3000, h=1687)
    ok, reason = asset_eligible_for_main_slot(
        asset,
        pattern_id=PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
    )
    assert ok
    assert reason == "ok"

    square = {"id": "sq", "width": 1000, "height": 1000, "quality": {"sharpness": 0.8}}
    ok_sq, reason_sq = asset_eligible_for_main_slot(
        square,
        pattern_id=PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
    )
    assert not ok_sq
    assert reason_sq == "blocked_square"


def test_conventional_window_still_orders_hero_six():
    aspects = {
        "l0": "landscape",
        "l1": "landscape",
        "l2": "landscape",
        "l3": "landscape",
        "l4": "landscape",
        "p1": "portrait",
    }
    assets_map = {
        "l0": _asset("l0", w=3000, h=1687),
        "l1": _asset("l1", w=3000, h=1687),
        "l2": _asset("l2", w=3000, h=1687),
        "l3": _asset("l3", w=3000, h=1687),
        "l4": _asset("l4", w=3000, h=1687),
        "p1": _asset("p1", w=1200, h=1800),
    }
    ordered = try_order_for_pattern(
        PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
        list(aspects.keys()),
        aspects,
        assets_map,
        burst_seconds=3600,
        median_sharp=0.5,
    )
    assert ordered is not None
    pat = default_registry()[PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5]
    from travelogue.curation.mosaic.builders import build_screen

    screen = build_screen(pat, ordered, assets_map=assets_map)
    ok, _ = screen_main_slot_eligible(
        screen,
        assets_map,
        pattern_id=PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
    )
    assert ok


def test_portrait_3land_template_main_slot_policy_loaded():
    from travelogue.curation.mosaic.main_eligibility import (
        pattern_requires_main_ar_guard,
        resolve_main_forbid_kinds,
        template_main_slot_policy,
    )

    policy = template_main_slot_policy(PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND)
    assert policy is not None
    assert policy.get("slotIndex") == 0
    assert pattern_requires_main_ar_guard(PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND)
    assert resolve_main_forbid_kinds(PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND) == frozenset(
        {"panorama", "tall", "portrait", "square"}
    )


def test_portrait_3land_rejects_all_panorama_mains():
    aspects = {
        "p": "portrait",
        "l0": "landscape",
        "l1": "landscape",
        "l2": "landscape",
        "l3": "landscape",
    }
    assets_map = {
        "p": _asset("p", w=1200, h=1800),
        "l0": _asset("l0", w=5000, h=2000),
        "l1": _asset("l1", w=5000, h=2000),
        "l2": _asset("l2", w=5000, h=2000),
        "l3": _asset("l3", w=5000, h=2000),
    }
    ordered = try_order_for_pattern(
        PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
        list(aspects.keys()),
        aspects,
        assets_map,
        burst_seconds=3600,
        median_sharp=0.5,
    )
    assert ordered is None


def test_portrait_3land_picks_conventional_main():
    aspects = {
        "p": "portrait",
        "good": "landscape",
        "l1": "landscape",
        "l2": "landscape",
        "l3": "landscape",
    }
    assets_map = {
        "p": _asset("p", w=1200, h=1800),
        "good": _asset("good", w=3000, h=1687),
        "l1": _asset("l1", w=5000, h=2000),
        "l2": _asset("l2", w=5000, h=2000),
        "l3": _asset("l3", w=5000, h=2000),
    }
    ordered = try_order_for_pattern(
        PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
        list(aspects.keys()),
        aspects,
        assets_map,
        burst_seconds=3600,
        median_sharp=0.5,
    )
    assert ordered is not None
    assert ordered[0] == "good"
