"""MTSO PR-C2 · experimental portrait-hero SKUs (O-1 contract freeze)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from travelogue.config import get_config
from travelogue.config.mosaic import TemplateExperimentsConfig
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_engine.contract.evaluator import _hero_area_from_template
from travelogue.layout_engine.contract.geometry_features import (
    compute_raw_geometry_features,
)
from travelogue.layout_engine.mosaic.scorer import _wasted_hero_penalty
from travelogue.layout_engine.mosaic.builders import try_order_for_pattern
from travelogue.layout_engine.mosaic.coarse_segments import (
    SIGNATURE_WHITELIST,
    apply_signature_route,
)
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO,
    PATTERN_MOSAIC_5_2P3L_PORTRAIT_HERO_RAIL,
    PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
    MOSAIC_5_PATTERN_IDS,
)
from travelogue.layout_engine.mosaic.lifecycle import lifecycle_admit
from travelogue.layout_engine.mosaic.lte_adapter import mosaic_registry
from travelogue.layout_engine.mosaic.pattern_catalog import MosaicPattern
from travelogue.layout_templates.registry import get_engine, reset_engine_cache_for_tests


@pytest.fixture(autouse=True)
def _reset_engine() -> None:
    reset_engine_cache_for_tests()
    yield
    reset_engine_cache_for_tests()


def _asset(aid: str, *, w: int, h: int, sharp: float, kind: str) -> dict:
    return {
        "id": aid,
        "width": w,
        "height": h,
        "takenAt": "2024-06-01T12:00:00Z",
        "aspectKind": kind,
        "quality": {"sharpness": sharp},
    }


def test_not_in_ga_policy_tuple() -> None:
    assert PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO not in MOSAIC_5_PATTERN_IDS
    assert PATTERN_MOSAIC_5_2P3L_PORTRAIT_HERO_RAIL not in MOSAIC_5_PATTERN_IDS


def test_pattern_has_main_role_via_lte_fallback() -> None:
    """Experimental SKUs must not be treated as equal-weight dense (main-role miss)."""
    for pid in (
        PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO,
        PATTERN_MOSAIC_5_2P3L_PORTRAIT_HERO_RAIL,
    ):
        assert ScreenLayoutPlannerState.pattern_has_main_role(pid)
        # wasted_hero must short-circuit (no 0.35 equal-weight tax)
        screen = {
            "slots": [
                {"assetId": "p0", "role": "main"},
                {"assetId": "l0"},
                {"assetId": "l1"},
                {"assetId": "l2"},
                {"assetId": "l3"},
            ]
        }
        assert (
            _wasted_hero_penalty(
                screen,
                pid,
                aspects={
                    "p0": "portrait",
                    "l0": "landscape",
                    "l1": "landscape",
                    "l2": "landscape",
                    "l3": "landscape",
                },
                assets_by_id={
                    "p0": _asset("p0", w=1200, h=1800, sharp=0.95, kind="portrait"),
                    "l0": _asset("l0", w=3000, h=1687, sharp=0.5, kind="landscape"),
                    "l1": _asset("l1", w=3000, h=1687, sharp=0.5, kind="landscape"),
                    "l2": _asset("l2", w=3000, h=1687, sharp=0.5, kind="landscape"),
                    "l3": _asset("l3", w=3000, h=1687, sharp=0.5, kind="landscape"),
                },
                median_sharp=0.5,
            )
            == 0.0
        )


def test_ac08_area_and_prominence_ratios() -> None:
    for pid in (
        PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO,
        PATTERN_MOSAIC_5_2P3L_PORTRAIT_HERO_RAIL,
    ):
        area = _hero_area_from_template(pid)
        assert area is not None
        assert area + 1e-9 >= 0.55
        feats = compute_raw_geometry_features(pid)
        assert feats["heroCoverageRatio"] is not None
        assert float(feats["heroCoverageRatio"]) + 1e-9 >= 0.55
        assert feats["heroProminenceRatio"] is not None
        assert float(feats["heroProminenceRatio"]) + 1e-9 >= 3.0


def test_order_1p4l_portrait_hero() -> None:
    ids = ["p0"] + [f"l{i}" for i in range(4)]
    aspects = {"p0": "portrait", **{f"l{i}": "landscape" for i in range(4)}}
    assets = {
        "p0": _asset("p0", w=1200, h=1800, sharp=0.9, kind="portrait"),
        **{
            f"l{i}": _asset(f"l{i}", w=3000, h=1687, sharp=0.5, kind="landscape")
            for i in range(4)
        },
    }
    ordered = try_order_for_pattern(
        PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO,
        ids,
        aspects,
        assets,
        burst_seconds=12.0,
        median_sharp=0.5,
    )
    assert ordered is not None
    assert ordered[0] == "p0"
    assert set(ordered[1:]) == {f"l{i}" for i in range(4)}


def test_order_2p3l_strongest_portrait_is_main() -> None:
    ids = ["p_weak", "p_strong", "l0", "l1", "l2"]
    aspects = {
        "p_weak": "portrait",
        "p_strong": "portrait",
        "l0": "landscape",
        "l1": "landscape",
        "l2": "landscape",
    }
    assets = {
        "p_weak": _asset("p_weak", w=1200, h=1800, sharp=0.4, kind="portrait"),
        "p_strong": _asset("p_strong", w=1200, h=1800, sharp=0.95, kind="portrait"),
        "l0": _asset("l0", w=3000, h=1687, sharp=0.5, kind="landscape"),
        "l1": _asset("l1", w=3000, h=1687, sharp=0.5, kind="landscape"),
        "l2": _asset("l2", w=3000, h=1687, sharp=0.5, kind="landscape"),
    }
    ordered = try_order_for_pattern(
        PATTERN_MOSAIC_5_2P3L_PORTRAIT_HERO_RAIL,
        ids,
        aspects,
        assets,
        burst_seconds=12.0,
        median_sharp=0.5,
    )
    assert ordered is not None
    assert ordered[0] == "p_strong"
    assert ordered[1] == "p_weak"


def test_signature_whitelist_includes_new_skus() -> None:
    from travelogue.layout_engine.mosaic.pattern_catalog import AspectProfile

    assert PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO in SIGNATURE_WHITELIST[(1, 4, True)]
    assert PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO in SIGNATURE_WHITELIST[(1, 4, False)]
    assert PATTERN_MOSAIC_5_2P3L_PORTRAIT_HERO_RAIL in SIGNATURE_WHITELIST[(2, 3, True)]
    ap = AspectProfile(
        min_portrait=0, min_landscape=0, max_portrait=9, max_landscape=9
    )
    pats = [
        MosaicPattern(
            pattern_id=PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
            slot_count=5,
            grid_class="x",
            roles=("main", "portrait", "landscape", "landscape", "landscape"),
            accepts=ap,
            css_verified=True,
        ),
        MosaicPattern(
            pattern_id=PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO,
            slot_count=5,
            grid_class="y",
            roles=("main", "landscape", "landscape", "landscape", "landscape"),
            accepts=ap,
            css_verified=True,
        ),
    ]
    ids = ["p0", "l0", "l1", "l2", "l3"]
    aspects = {"p0": "portrait", **{f"l{i}": "landscape" for i in range(4)}}
    assets = {
        aid: _asset(aid, w=1000, h=1000, sharp=0.5, kind=aspects[aid]) for aid in ids
    }
    narrowed, source = apply_signature_route(pats, ids, aspects, assets)
    assert source == "signature"
    assert {p.pattern_id for p in narrowed} == {
        PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
        PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO,
    }


def test_ac09_signature_miss_keeps_prior_set() -> None:
    """Unknown signature or empty intersection → fallback, never silent empty."""
    from travelogue.layout_engine.mosaic.pattern_catalog import AspectProfile

    ap = AspectProfile(
        min_portrait=0, min_landscape=0, max_portrait=9, max_landscape=9
    )
    pats = [
        MosaicPattern(
            pattern_id=PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
            slot_count=5,
            grid_class="x",
            roles=("main", "portrait", "landscape", "landscape", "landscape"),
            accepts=ap,
            css_verified=True,
        ),
        MosaicPattern(
            pattern_id=PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO,
            slot_count=5,
            grid_class="y",
            roles=("main", "landscape", "landscape", "landscape", "landscape"),
            accepts=ap,
            css_verified=True,
        ),
    ]
    # 0P5L is not a whitelist key → miss
    ids = [f"l{i}" for i in range(5)]
    aspects = {aid: "landscape" for aid in ids}
    assets = {
        aid: _asset(aid, w=3000, h=1687, sharp=0.5, kind="landscape") for aid in ids
    }
    kept, source = apply_signature_route(pats, ids, aspects, assets)
    assert source == "signature_fallback"
    assert kept == pats
    assert len(kept) == 2


def test_experimental_gated_without_triple() -> None:
    admit = lifecycle_admit(PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO, app=get_config())
    assert not admit.ok
    assert admit.reason in (
        "lifecycle_experimental_gated",
        "lifecycle_allowlist_miss",
        "lifecycle_cohort_miss",
    )


def test_experimental_triple_admits(monkeypatch) -> None:
    trip_id = "mtso-c2-cohort"
    app = replace(
        get_config(),
        mosaic=replace(
            get_config().mosaic,
            template_experiments=TemplateExperimentsConfig(
                enabled=True,
                allowlist=(
                    PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO,
                    PATTERN_MOSAIC_5_2P3L_PORTRAIT_HERO_RAIL,
                ),
                cohort_trip_ids=(trip_id,),
            ),
        ),
    )
    monkeypatch.setattr("travelogue.config.get_config", lambda: app)
    reset_engine_cache_for_tests()
    keys = set(mosaic_registry(cfg=app, trip_id=trip_id).keys())
    assert PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO in keys
    assert PATTERN_MOSAIC_5_2P3L_PORTRAIT_HERO_RAIL in keys
    assert get_engine().get(PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO).status == "experimental"
