"""Tri-col family · 2P2L bookends / 1P4L center-rails / landscape-6 revive."""

from __future__ import annotations

from dataclasses import replace

import pytest

from travelogue.config import get_config
from travelogue.config.mosaic import TemplateExperimentsConfig
from travelogue.layout_engine.mosaic.builders import try_order_for_pattern
from travelogue.layout_engine.mosaic.coarse_segments import SIGNATURE_WHITELIST
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_LANDSCAPE_6,
    PATTERN_MOSAIC_4_2P2L_PORTRAIT_BOOKENDS,
    PATTERN_MOSAIC_5_1P4L_PORTRAIT_CENTER_RAILS,
    PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO,
)
from travelogue.layout_engine.mosaic.lifecycle import lifecycle_admit
from travelogue.layout_engine.mosaic.lte_adapter import mosaic_registry
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


def _experiments(*, allow: tuple[str, ...], trip: str = "dogfood-tri-col") -> object:
    app = get_config()
    return replace(
        app,
        mosaic=replace(
            app.mosaic,
            template_experiments=TemplateExperimentsConfig(
                enabled=True,
                allowlist=allow,
                cohort_trip_ids=(trip,),
            ),
        ),
    )


def test_yaml_and_grid_classes_registered() -> None:
    eng = get_engine()
    bookends = eng.get(PATTERN_MOSAIC_4_2P2L_PORTRAIT_BOOKENDS)
    rails = eng.get(PATTERN_MOSAIC_5_1P4L_PORTRAIT_CENTER_RAILS)
    land6 = eng.get(PATTERN_LANDSCAPE_6)
    assert bookends.status == "experimental"
    assert rails.status == "experimental"
    assert land6.status == "experimental"
    assert bookends.mix_portrait == 2 and bookends.mix_landscape == 2
    assert rails.mix_portrait == 1 and rails.mix_landscape == 4
    assert land6.mix_portrait == 0 and land6.mix_landscape == 6
    assert (
        grid_class_for_pattern(PATTERN_MOSAIC_4_2P2L_PORTRAIT_BOOKENDS)
        == "layout-screen__grid--mosaic-4-2p2l-portrait-bookends"
    )
    assert (
        grid_class_for_pattern(PATTERN_MOSAIC_5_1P4L_PORTRAIT_CENTER_RAILS)
        == "layout-screen__grid--mosaic-5-1p4l-portrait-center-rails"
    )
    assert grid_class_for_pattern(PATTERN_LANDSCAPE_6) == "layout-screen__grid--3x2"


def test_signature_whitelist_includes_tri_col_skus() -> None:
    assert PATTERN_MOSAIC_4_2P2L_PORTRAIT_BOOKENDS in SIGNATURE_WHITELIST[(2, 2, True)]
    assert PATTERN_MOSAIC_5_1P4L_PORTRAIT_CENTER_RAILS in SIGNATURE_WHITELIST[(1, 4, True)]
    assert PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO in SIGNATURE_WHITELIST[(1, 4, True)]


def test_order_bookends_and_center_rails() -> None:
    assets = {
        "p0": _asset("p0", w=900, h=1600, sharp=0.9, kind="portrait"),
        "p1": _asset("p1", w=900, h=1600, sharp=0.5, kind="portrait"),
        "l0": _asset("l0", w=1600, h=900, sharp=0.7, kind="landscape"),
        "l1": _asset("l1", w=1600, h=900, sharp=0.6, kind="landscape"),
        "l2": _asset("l2", w=1600, h=900, sharp=0.55, kind="landscape"),
        "l3": _asset("l3", w=1600, h=900, sharp=0.5, kind="landscape"),
    }
    aspects = {k: v["aspectKind"] for k, v in assets.items()}

    ordered4 = try_order_for_pattern(
        PATTERN_MOSAIC_4_2P2L_PORTRAIT_BOOKENDS,
        ["p0", "p1", "l0", "l1"],
        aspects,
        assets,
        burst_seconds=60.0,
        median_sharp=0.6,
    )
    assert ordered4 is not None
    assert ordered4[0] == "p0"  # stronger left bookend
    assert ordered4[3] == "p1"
    assert set(ordered4[1:3]) == {"l0", "l1"}

    ordered5 = try_order_for_pattern(
        PATTERN_MOSAIC_5_1P4L_PORTRAIT_CENTER_RAILS,
        ["p0", "l0", "l1", "l2", "l3"],
        aspects,
        assets,
        burst_seconds=60.0,
        median_sharp=0.6,
    )
    assert ordered5 == ["p0", "l0", "l1", "l2", "l3"]


def test_experiments_gate_admits_tri_col_family() -> None:
    trip = "dogfood-tri-col"
    tri_col_allow = (
        PATTERN_MOSAIC_4_2P2L_PORTRAIT_BOOKENDS,
        PATTERN_MOSAIC_5_1P4L_PORTRAIT_CENTER_RAILS,
    )
    allow = tri_col_allow + (PATTERN_LANDSCAPE_6,)
    app = _experiments(allow=allow, trip=trip)
    for pid in allow:
        assert lifecycle_admit(
            pid, app=app, mosaic_cfg=app.mosaic, trip_id=trip
        ).ok
    # Default path (no allowlist hit) stays gated.
    bare = get_config()
    for pid in tri_col_allow:
        assert not lifecycle_admit(
            pid,
            app=bare,
            mosaic_cfg=bare.mosaic,
            trip_id=trip,
        ).ok
    # GOLDEN-BUMP-JUSTIFICATION: EGA D-EGA-06 / AC-EGA-06 · 默认 experiments 路径下，
    # 只有 white-list equal-grid 的 landscape-6 会被 EGA 放行。
    assert lifecycle_admit(
        PATTERN_LANDSCAPE_6, app=bare, mosaic_cfg=bare.mosaic, trip_id=trip
    ).ok


def test_registry_includes_when_experiments_open(monkeypatch) -> None:
    trip = "dogfood-tri-col"
    allow = (
        PATTERN_MOSAIC_4_2P2L_PORTRAIT_BOOKENDS,
        PATTERN_MOSAIC_5_1P4L_PORTRAIT_CENTER_RAILS,
        PATTERN_LANDSCAPE_6,
    )
    app = _experiments(allow=allow, trip=trip)
    monkeypatch.setattr("travelogue.config.get_config", lambda: app)
    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.lte_adapter.get_config", lambda: app
    )
    reg = mosaic_registry(app, trip_id=trip)
    for pid in allow:
        assert pid in reg
