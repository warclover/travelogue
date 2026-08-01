"""ALG-V3 B2a · static geometry precheck before build_screen."""

from __future__ import annotations

from dataclasses import replace

from travelogue.config import MosaicConfig
from travelogue.config.mosaic import SlotAdaptationConfig
from travelogue.layout_engine.mosaic.candidates import (
    generate_window_candidates_with_rejections,
)
from travelogue.layout_engine.mosaic.slot_geometry import (
    pattern_geometry_precheck,
    screen_slots_geometry_ok,
)


def test_precheck_defers_mixed_orientation_auto_flow():
    """Mixed P/L windows need assignment — not a definite static fail."""
    aspects = {"p0": "portrait", "p1": "portrait", "l0": "landscape", "l1": "landscape"}
    ordered = ["p0", "p1", "l0", "l1"]
    assert (
        pattern_geometry_precheck(
            "screen-portrait-2-landscape-2", ordered, aspects, cfg=MosaicConfig()
        )
        is None
    )


def test_precheck_accepts_all_landscape_four():
    aspects = {"l0": "landscape", "l1": "landscape", "l2": "landscape", "l3": "landscape"}
    ordered = ["l0", "l1", "l2", "l3"]
    assert (
        pattern_geometry_precheck(
            "screen-landscape-4", ordered, aspects, cfg=MosaicConfig()
        )
        is True
    )


def test_precheck_matches_screen_slots_geometry_ok_without_display_aspect():
    aspects = {"p0": "portrait", "p1": "portrait", "p2": "portrait", "p3": "portrait"}
    ordered = ["p0", "p1", "p2", "p3"]
    fake = {
        "patternId": "screen-portrait-4",
        "slots": [{"slot": i, "assetId": a} for i, a in enumerate(ordered)],
    }
    assert screen_slots_geometry_ok(fake, aspects) is True
    assert pattern_geometry_precheck(
        "screen-portrait-4", ordered, aspects, cfg=MosaicConfig()
    ) is True


def test_precheck_returns_none_when_msa_enabled():
    cfg = MosaicConfig(slot_adaptation=SlotAdaptationConfig(enabled=True))
    aspects = {"l0": "landscape", "l1": "landscape", "l2": "landscape", "l3": "landscape"}
    assert (
        pattern_geometry_precheck(
            "screen-landscape-4",
            ["l0", "l1", "l2", "l3"],
            aspects,
            cfg=cfg,
        )
        is None
    )


def test_precheck_returns_none_for_unknown_pattern():
    aspects = {"a": "landscape"}
    assert (
        pattern_geometry_precheck("screen-not-a-real-pattern", ["a"], aspects)
        is None
    )


def test_candidates_skip_build_screen_on_static_precheck_fail(monkeypatch):
    """AC-20 neighbor: static_precheck reject must not call build_screen."""
    from travelogue.layout_engine.mosaic.constants import PATTERN_PORTRAIT_2_LANDSCAPE_2
    from travelogue.layout_engine.mosaic.pattern_catalog import AspectProfile, MosaicPattern

    aspects = {
        "p0": "portrait",
        "p1": "portrait",
        "l0": "landscape",
        "l1": "landscape",
    }
    assets = {
        aid: {
            "id": aid,
            "aspectKind": kind,
            "width": 1000 if kind == "landscape" else 800,
            "height": 800 if kind == "landscape" else 1200,
            "curation": {"layoutEligible": True},
        }
        for aid, kind in aspects.items()
    }
    reg = {
        PATTERN_PORTRAIT_2_LANDSCAPE_2: MosaicPattern(
            pattern_id=PATTERN_PORTRAIT_2_LANDSCAPE_2,
            slot_count=4,
            grid_class="mixed",
            roles=("a", "b", "c", "d"),
            accepts=AspectProfile(),
        )
    }
    cfg = replace(
        MosaicConfig(),
        enabled_window_sizes=(4,),
        unified_mode=True,
        lse_hungarian_assignment=False,
    )
    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.candidates.try_order_for_pattern",
        lambda *a, **k: ["p0", "p1", "l0", "l1"],
    )
    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.candidates.pattern_geometry_precheck",
        lambda *a, **k: False,
    )

    build_calls = {"n": 0}
    real_build = __import__(
        "travelogue.layout_engine.mosaic.builders", fromlist=["build_screen"]
    ).build_screen

    def _counting_build(*args, **kwargs):
        build_calls["n"] += 1
        return real_build(*args, **kwargs)

    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.candidates.build_screen",
        _counting_build,
    )

    result = generate_window_candidates_with_rejections(
        ["p0", "p1", "l0", "l1"],
        aspects,  # type: ignore[arg-type]
        assets,
        cfg=cfg,
        registry=reg,
        burst_seconds=3600.0,
    )
    assert build_calls["n"] == 0
    assert any(
        r.get("reason") == "geometry_invalid" and r.get("detail") == "static_precheck"
        for r in result.rejected
    )
    assert result.candidates == []
