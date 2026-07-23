"""MSA PR-B · crop_risk contain, whitespace budget, aux protect (AC-06～08)."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest

from travelogue.config import get_config
from travelogue.config.mosaic import SlotAdaptationConfig, mosaic_from_dict
from travelogue.layout_engine.mosaic.log import MosaicWindowLog
from travelogue.layout_engine.mosaic.msa_apply import maybe_apply_slot_adaptation
from travelogue.layout_engine.mosaic.msa_assign import refine_aux_assignment
from travelogue.layout_engine.mosaic.msa_fit import (
    apply_crop_risk_fits,
    crop_risk_for_pair,
    page_whitespace_ratio,
)
from travelogue.layout_templates.geometry_solidify import solidify_screen_geometry
from travelogue.layout_templates.registry import reset_engine_cache_for_tests

PATTERN_6 = "screen-mosaic-6-main-hero-plus-5"


@pytest.fixture(autouse=True)
def _reset_engine() -> None:
    reset_engine_cache_for_tests()
    yield
    reset_engine_cache_for_tests()


def _land(aid: str, *, w: int, h: int, focal: tuple[float, float] | None = None) -> dict:
    out: dict = {
        "id": aid,
        "width": w,
        "height": h,
        "aspectKind": "landscape",
        "quality": {"sharpness": 0.9},
    }
    if focal is not None:
        out["focalPoint"] = {"x": focal[0], "y": focal[1]}
    return out


def _six_screen(assets: dict[str, dict]) -> dict:
    ids = list(assets.keys())
    return {
        "patternId": PATTERN_6,
        "slots": [
            {
                "slot": i,
                "assetId": ids[i],
                "role": "main" if i == 0 else "tile",
                "fit": "cover",
            }
            for i in range(6)
        ],
    }


def test_crop_risk_proxy_increases_with_mismatch_and_edge() -> None:
    mild = crop_risk_for_pair(_land("a", w=3000, h=2000), 1.50)
    harsh = crop_risk_for_pair(_land("b", w=4000, h=1000), 1.50)
    edged = crop_risk_for_pair(
        _land("c", w=4000, h=1000, focal=(0.02, 0.5)), 1.50
    )
    assert harsh > mild
    assert edged > harsh


def test_ac06_high_risk_gets_contain_under_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    # Ultra-wide photos vs ~1.5 hero slots → high mismatch; low θ to exercise gate
    assets = {
        f"a{i}": _land(f"a{i}", w=5000, h=1000, focal=(0.05, 0.5)) for i in range(6)
    }
    screen = _six_screen(assets)
    sa = SlotAdaptationConfig(
        enabled=True,
        crop_risk_contain_threshold=0.35,
        whitespace_max=0.50,
    )
    cfg = replace(get_config(), mosaic=replace(mosaic_from_dict({}), slot_adaptation=sa))
    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.msa_apply.get_effective_mosaic_config",
        lambda: cfg.mosaic,
    )
    solidify_screen_geometry(screen, PATTERN_6, assets_map=assets)
    summary = maybe_apply_slot_adaptation(screen, PATTERN_6, assets_map=assets, cfg=cfg.mosaic)
    assert summary["cropRisk"] is not None
    assert any(r >= 0.35 for r in summary["cropRisk"])
    assert any(s.get("fit") == "contain" and s.get("msaContain") for s in screen["slots"])
    assert summary["whitespaceRatio"] is not None
    assert summary["whitespaceRatio"] <= sa.whitespace_max + 1e-6


def test_ac06_whitespace_budget_caps_contain() -> None:
    slots = [
        {
            "slot": 0,
            "assetId": "a0",
            "role": "main",
            "fit": "cover",
            "displayAspect": 1.5,
        },
        {
            "slot": 1,
            "assetId": "a1",
            "role": "tile",
            "fit": "cover",
            "displayAspect": 1.8,
        },
        {
            "slot": 2,
            "assetId": "a2",
            "role": "tile",
            "fit": "cover",
            "displayAspect": 1.8,
        },
    ]
    assets = {
        "a0": _land("a0", w=5000, h=1000, focal=(0.05, 0.5)),
        "a1": _land("a1", w=5000, h=1000, focal=(0.05, 0.5)),
        "a2": _land("a2", w=5000, h=1000, focal=(0.05, 0.5)),
    }
    screen = {"slots": deepcopy(slots)}
    sa = SlotAdaptationConfig(
        enabled=True,
        crop_risk_contain_threshold=0.2,
        whitespace_max=0.25,  # enough for one mid-area contain, not all three
    )
    areas = [0.4, 0.3, 0.3]
    risks, ws = apply_crop_risk_fits(
        screen, assets_map=assets, slot_areas=areas, cfg=sa
    )
    n_contain = sum(1 for s in screen["slots"] if s.get("fit") == "contain")
    assert n_contain >= 1
    assert n_contain < 3
    assert ws <= sa.whitespace_max + 1e-6
    assert len(risks) == 3


def test_ac06v_msa_contain_skips_blur_and_marks_paper() -> None:
    from travelogue.render.context import build_layout_screen

    screen = {
        "patternId": PATTERN_6,
        "layoutGeometry": {
            "stageAspect": "16:9",
            "cols": [1, 1, 1],
            "rows": [1, 1, 1],
            "gridClass": "layout-screen__grid--mosaic-6-main-hero-plus-5",
            "trackOverride": {"cols": [1, 1, 1], "rows": [1, 1, 1]},
        },
        "slots": [
            {
                "slot": 0,
                "assetId": "a0",
                "role": "main",
                "fit": "contain",
                "msaContain": True,
                "displayAspect": 1.5,
            }
        ],
    }
    assets = {"a0": _land("a0", w=3000, h=2000)}
    out = build_layout_screen(screen, assets, meta_title="Test", export_layout="web")
    slot0 = out["slots"][0]
    assert slot0.get("msaContain") is True
    assert slot0.get("hasBlurFill") is not True


def test_ac07_flattest_aux_rejects_highest_risk_land() -> None:
    # Slot1 flattest (AR=2.0); holds ultra-wide; slot2 holds milder 3:2 → expect swap
    screen = {
        "slots": [
            {
                "slot": 0,
                "assetId": "main",
                "role": "main",
                "fit": "cover",
                "displayAspect": 1.5,
            },
            {
                "slot": 1,
                "assetId": "wide",
                "role": "tile",
                "fit": "cover",
                "displayAspect": 2.0,
            },
            {
                "slot": 2,
                "assetId": "mild",
                "role": "tile",
                "fit": "cover",
                "displayAspect": 1.2,
            },
        ]
    }
    assets = {
        "main": _land("main", w=3000, h=2000),
        "wide": _land("wide", w=5000, h=1000),
        "mild": _land("mild", w=3000, h=2000),
    }
    assert refine_aux_assignment(screen, assets_map=assets) is True
    assert screen["slots"][1]["assetId"] == "mild"
    assert screen["slots"][2]["assetId"] == "wide"
    # Main untouched
    assert screen["slots"][0]["assetId"] == "main"


def test_ac08_raw_log_fields_from_screen() -> None:
    from travelogue.layout_engine.mosaic.compose import _attach_msa_log_from_screen

    screen = {
        "layoutGeometry": {
            "trackOverride": {"cols": [1.2, 1.0, 0.8], "rows": [1, 1, 1]},
            "msa": {
                "outcome": "applied",
                "profile": {"landPeak": "three_two", "rHeroTarget": 1.5},
                "rHeroTarget": 1.5,
                "cropRisk": [0.1, 0.6, 0.2],
                "whitespaceRatio": 0.04,
            },
        },
        "slots": [
            {"fit": "cover"},
            {"fit": "contain", "msaContain": True},
            {"fit": "cover"},
        ],
    }
    log = MosaicWindowLog()
    _attach_msa_log_from_screen(log, screen)
    d = log.to_dict()
    assert d["msaOutcome"] == "applied"
    assert d["msaProfile"]["landPeak"] == "three_two"
    assert d["rHeroTarget"] == 1.5
    assert d["trackOverride"]["cols"][0] == 1.2
    assert d["slotFits"] == ["cover", "contain", "cover"]
    assert d["cropRisk"] == [0.1, 0.6, 0.2]
    assert d["whitespaceRatio"] == 0.04


def test_page_whitespace_ratio_zero_when_all_cover() -> None:
    slots = [{"fit": "cover", "assetId": "a", "displayAspect": 1.5}]
    assets = {"a": _land("a", w=3000, h=2000)}
    assert page_whitespace_ratio(slots, assets_map=assets, slot_areas=[1.0]) == 0.0
