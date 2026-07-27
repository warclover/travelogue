"""3P2L left-portrait-hero family · quad / lp-stack soft pick."""

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
from travelogue.layout_engine.mosaic.builders import try_order_for_pattern
from travelogue.layout_engine.mosaic.coarse_segments import SIGNATURE_WHITELIST
from travelogue.layout_engine.mosaic.constants import (
    MOSAIC_5_PATTERN_IDS,
    PATTERN_MOSAIC_5_2P3L_PORTRAIT_HERO_RAIL,
    PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK,
    PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD,
)
from travelogue.layout_engine.mosaic.lte_adapter import mosaic_registry
from travelogue.layout_engine.mosaic.mosaic_5_3p2l import (
    prefer_3p2l_pattern_id,
    soft_pick_3p2l_patterns,
)
from travelogue.layout_engine.mosaic.pattern_catalog import AspectProfile, MosaicPattern
from travelogue.layout_engine.planner.screen_planner import grid_class_for_pattern
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


def _pat(pid: str) -> MosaicPattern:
    ap = AspectProfile(
        min_portrait=3, min_landscape=2, max_portrait=3, max_landscape=2
    )
    return MosaicPattern(
        pattern_id=pid,
        slot_count=5,
        grid_class="x",
        roles=("main", "portrait", "portrait", "landscape", "landscape"),
        accepts=ap,
        css_verified=True,
    )


def test_not_in_ga_policy_tuple() -> None:
    assert PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD not in MOSAIC_5_PATTERN_IDS
    assert PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK not in MOSAIC_5_PATTERN_IDS


def test_pattern_has_main_role() -> None:
    for pid in (
        PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD,
        PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK,
    ):
        assert ScreenLayoutPlannerState.pattern_has_main_role(pid)


def test_hero_area_and_prominence() -> None:
    for pid in (
        PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD,
        PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK,
    ):
        area = _hero_area_from_template(pid)
        assert area is not None
        assert area + 1e-9 >= 0.55
        feats = compute_raw_geometry_features(pid)
        assert float(feats["heroCoverageRatio"]) + 1e-9 >= 0.55
        assert float(feats["heroProminenceRatio"]) + 1e-9 >= 3.0


def test_main_slot_is_portrait_readable() -> None:
    """Align O-1 / 2p3l-portrait-hero-rail: left full-height main AR < 1."""
    from travelogue.layout_templates.geometry import slot_display_aspect

    for pid in (
        PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD,
        PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK,
    ):
        tpl = get_engine().get(pid)
        main = next(s for s in tpl.slots if int(s.index) == 0)
        ar = float(slot_display_aspect(main.rect, tpl.stage))
        assert ar < 1.0, f"{pid} main displayAspect={ar} not portrait-readable"


def test_lp_stack_tip_slots_are_portrait_readable() -> None:
    from travelogue.layout_templates.geometry import slot_display_aspect

    tpl = get_engine().get(PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK)
    for idx in (2, 4):
        tip = next(s for s in tpl.slots if int(s.index) == idx)
        assert str(tip.role) == "portrait"
        ar = float(slot_display_aspect(tip.rect, tpl.stage))
        assert ar < 1.0, f"tip slot{idx} displayAspect={ar}"


def test_order_quad_strongest_portrait_is_main() -> None:
    ids = ["p_weak", "p_mid", "p_strong", "l0", "l1"]
    aspects = {
        "p_weak": "portrait",
        "p_mid": "portrait",
        "p_strong": "portrait",
        "l0": "landscape",
        "l1": "landscape",
    }
    assets = {
        "p_weak": _asset("p_weak", w=1200, h=1800, sharp=0.3, kind="portrait"),
        "p_mid": _asset("p_mid", w=1200, h=1800, sharp=0.5, kind="portrait"),
        "p_strong": _asset("p_strong", w=1200, h=1800, sharp=0.95, kind="portrait"),
        "l0": _asset("l0", w=3000, h=1687, sharp=0.5, kind="landscape"),
        "l1": _asset("l1", w=3000, h=1687, sharp=0.5, kind="landscape"),
    }
    ordered = try_order_for_pattern(
        PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD,
        ids,
        aspects,
        assets,
        burst_seconds=12.0,
        median_sharp=0.5,
    )
    assert ordered is not None
    assert ordered[0] == "p_strong"
    assert set(ordered[1:3]) == {"p_weak", "p_mid"}
    assert set(ordered[3:]) == {"l0", "l1"}


def test_order_lp_stack_interleaves_land_portrait() -> None:
    ids = ["p0", "p1", "p2", "l0", "l1"]
    aspects = {aid: "portrait" for aid in ("p0", "p1", "p2")}
    aspects.update({aid: "landscape" for aid in ("l0", "l1")})
    assets = {
        "p0": _asset("p0", w=1200, h=1800, sharp=0.95, kind="portrait"),
        "p1": _asset("p1", w=1200, h=1800, sharp=0.5, kind="portrait"),
        "p2": _asset("p2", w=1200, h=1800, sharp=0.5, kind="portrait"),
        "l0": _asset("l0", w=3000, h=1687, sharp=0.5, kind="landscape"),
        "l1": _asset("l1", w=3000, h=1687, sharp=0.5, kind="landscape"),
    }
    ordered = try_order_for_pattern(
        PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK,
        ids,
        aspects,
        assets,
        burst_seconds=12.0,
        median_sharp=0.5,
    )
    assert ordered is not None
    assert ordered[0] == "p0"
    assert aspects[ordered[1]] == "landscape"
    assert aspects[ordered[2]] == "portrait"
    assert aspects[ordered[3]] == "landscape"
    assert aspects[ordered[4]] == "portrait"


def test_signature_whitelist_3p2l() -> None:
    assert PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD in SIGNATURE_WHITELIST[(3, 2, True)]
    assert PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK in SIGNATURE_WHITELIST[(3, 2, False)]
    assert PATTERN_MOSAIC_5_2P3L_PORTRAIT_HERO_RAIL not in SIGNATURE_WHITELIST[(3, 2, True)]


def test_soft_pick_prefers_quad_when_aux_portraits_sharper() -> None:
    ids = ["p_main", "p_a", "p_b", "l0", "l1"]
    aspects = {
        "p_main": "portrait",
        "p_a": "portrait",
        "p_b": "portrait",
        "l0": "landscape",
        "l1": "landscape",
    }
    assets = {
        "p_main": _asset("p_main", w=1200, h=1800, sharp=0.9, kind="portrait"),
        "p_a": _asset("p_a", w=1200, h=1800, sharp=0.85, kind="portrait"),
        "p_b": _asset("p_b", w=1200, h=1800, sharp=0.8, kind="portrait"),
        "l0": _asset("l0", w=3000, h=1687, sharp=0.4, kind="landscape"),
        "l1": _asset("l1", w=3000, h=1687, sharp=0.4, kind="landscape"),
    }
    assert prefer_3p2l_pattern_id(ids, aspects, assets) == (
        PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD
    )
    picked = soft_pick_3p2l_patterns(
        [
            _pat(PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD),
            _pat(PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK),
        ],
        ids,
        aspects,
        assets,
    )
    assert [p.pattern_id for p in picked] == [PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD]


def test_soft_pick_prefers_lp_stack_when_landscapes_sharper() -> None:
    ids = ["p_main", "p_a", "p_b", "l0", "l1"]
    aspects = {
        "p_main": "portrait",
        "p_a": "portrait",
        "p_b": "portrait",
        "l0": "landscape",
        "l1": "landscape",
    }
    assets = {
        "p_main": _asset("p_main", w=1200, h=1800, sharp=0.9, kind="portrait"),
        "p_a": _asset("p_a", w=1200, h=1800, sharp=0.35, kind="portrait"),
        "p_b": _asset("p_b", w=1200, h=1800, sharp=0.35, kind="portrait"),
        "l0": _asset("l0", w=3000, h=1687, sharp=0.9, kind="landscape"),
        "l1": _asset("l1", w=3000, h=1687, sharp=0.85, kind="landscape"),
    }
    assert prefer_3p2l_pattern_id(ids, aspects, assets) == (
        PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK
    )


def test_default_experiments_admit_3p2l(monkeypatch) -> None:
    from travelogue.config import MosaicConfig

    app = replace(get_config(), mosaic=MosaicConfig())
    assert PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD in (
        app.mosaic.template_experiments.allowlist
    )
    assert PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK in (
        app.mosaic.template_experiments.allowlist
    )
    monkeypatch.setattr("travelogue.config.get_config", lambda: app)
    keys = set(mosaic_registry(cfg=app, trip_id="any-trip").keys())
    assert PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD in keys
    assert PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK in keys
    assert get_engine().get(PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD).status == (
        "experimental"
    )


def test_candidates_admit_typical_23_portrait(monkeypatch) -> None:
    """targetDisplayAspect=0.75 must admit 2:3 natives (main_ar_mismatch ≤1.4)."""
    from travelogue.config import MosaicConfig
    from travelogue.layout_engine.mosaic.candidates import (
        generate_window_candidates_with_rejections,
    )
    from travelogue.layout_engine.mosaic.lte_adapter import mosaic_registry

    app = replace(get_config(), mosaic=MosaicConfig())
    monkeypatch.setattr("travelogue.config.get_config", lambda: app)
    reset_engine_cache_for_tests()
    reg = mosaic_registry(cfg=app, trip_id="any-trip")
    ids = ["p0", "p1", "p2", "l0", "l1"]
    aspects = {a: "portrait" for a in ids[:3]}
    aspects.update({a: "landscape" for a in ids[3:]})
    assets = {
        "p0": _asset("p0", w=1200, h=1800, sharp=0.95, kind="portrait"),
        "p1": _asset("p1", w=1200, h=1800, sharp=0.8, kind="portrait"),
        "p2": _asset("p2", w=1200, h=1800, sharp=0.75, kind="portrait"),
        "l0": _asset("l0", w=3000, h=1687, sharp=0.4, kind="landscape"),
        "l1": _asset("l1", w=3000, h=1687, sharp=0.4, kind="landscape"),
    }
    result = generate_window_candidates_with_rejections(
        ids,
        aspects,
        assets,
        cfg=app.mosaic,
        registry=reg,
        trip_id="any-trip",
        trip_photo_total=40,
    )
    pids = {c.pattern_id for c in result.candidates}
    assert PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD in pids
    assert PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK not in pids


def test_gated_when_allowlist_empty(monkeypatch) -> None:
    app = replace(
        get_config(),
        mosaic=replace(
            get_config().mosaic,
            template_experiments=TemplateExperimentsConfig(
                enabled=True,
                allowlist=(),
                cohort_trip_ids=("*",),
            ),
        ),
    )
    monkeypatch.setattr("travelogue.config.get_config", lambda: app)
    reset_engine_cache_for_tests()
    keys = set(mosaic_registry(cfg=app, trip_id="any-trip").keys())
    assert PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD not in keys
    assert PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK not in keys


def test_grid_class_for_3p2l_patterns() -> None:
    assert grid_class_for_pattern(PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD) == (
        "layout-screen__grid--mosaic-5-3p2l-portrait-hero-quad"
    )
    assert grid_class_for_pattern(PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK) == (
        "layout-screen__grid--mosaic-5-3p2l-portrait-hero-lp-stack"
    )
    assert "1col" not in grid_class_for_pattern(PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD)
