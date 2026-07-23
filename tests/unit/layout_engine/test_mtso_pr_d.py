"""MTSO PR-D · AC-10 parent OFF baseline + dogfood path smoke."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import patch

import pytest

from travelogue.config import get_config
from travelogue.config.mosaic import (
    SelectionOptimizationConfig,
    TemplateContractConfig,
    TemplateExperimentsConfig,
)
from travelogue.layout_engine.mosaic.compose import pick_best_window
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO,
    PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
)
from travelogue.layout_engine.mosaic.lifecycle import lifecycle_admit
from travelogue.layout_engine.mosaic.lte_adapter import mosaic_registry
from travelogue.layout_templates.registry import reset_engine_cache_for_tests


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


def _strong_portrait_1p4l() -> tuple[list[str], dict, dict]:
    ids = ["p0"] + [f"l{i}" for i in range(4)]
    aspects = {"p0": "portrait", **{f"l{i}": "landscape" for i in range(4)}}
    assets = {
        "p0": _asset("p0", w=1200, h=1800, sharp=0.99, kind="portrait"),
        **{
            f"l{i}": _asset(f"l{i}", w=3000, h=1687, sharp=0.40, kind="landscape")
            for i in range(4)
        },
    }
    return ids, aspects, assets


def test_ac10_parent_off_ignores_nested_switches(monkeypatch) -> None:
    """AC-MTSO-10 · selection_optimization=false ⇒ nested ON is inert vs baseline."""
    ids, aspects, assets = _strong_portrait_1p4l()
    base = get_config().mosaic
    off = replace(
        base,
        enabled=True,
        enabled_window_sizes=(4, 5, 6),
        min_candidate_score=0.0,
        selection_optimization=SelectionOptimizationConfig(
            enabled=False,
            hero_six_opportunity_enabled=True,
            mixed_hero_routing_enabled=True,
        ),
    )
    nested_on_but_parent_off = replace(
        off,
        selection_optimization=SelectionOptimizationConfig(
            enabled=False,
            hero_six_opportunity_enabled=True,
            mixed_hero_routing_enabled=True,
            hero_gap_threshold=0.01,
        ),
    )
    app_a = replace(get_config(), mosaic=off)
    app_b = replace(get_config(), mosaic=nested_on_but_parent_off)
    with patch("travelogue.config.get_config", return_value=app_a), patch(
        "travelogue.layout_engine.mosaic.runtime.get_effective_mosaic_config",
        return_value=off,
    ):
        pick_a = pick_best_window(
            ids, aspects, assets, cfg=off, window_size=5, trip_photo_total=40
        )
    with patch("travelogue.config.get_config", return_value=app_b), patch(
        "travelogue.layout_engine.mosaic.runtime.get_effective_mosaic_config",
        return_value=nested_on_but_parent_off,
    ):
        pick_b = pick_best_window(
            ids,
            aspects,
            assets,
            cfg=nested_on_but_parent_off,
            window_size=5,
            trip_photo_total=40,
        )
    pid_a = (pick_a.screen or {}).get("patternId")
    pid_b = (pick_b.screen or {}).get("patternId")
    assert pid_a == pid_b
    assert (pick_a.screen or {}).get("slots") == (pick_b.screen or {}).get("slots")
    # Parent OFF must not hard-reject via mixed routing (main-portrait still eligible).
    from travelogue.layout_engine.mosaic.candidates import (
        generate_window_candidates_with_rejections,
    )

    result = generate_window_candidates_with_rejections(
        ids, aspects, assets, cfg=off, median_sharp=0.5
    )
    assert not any(
        str(r.get("reason") or "").startswith("mixed_routing:") for r in result.rejected
    )
    assert any(
        c.pattern_id == PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND and c.hard_valid
        for c in result.candidates
    )


def test_dogfood_experiments_admits_portrait_hero_sku(monkeypatch) -> None:
    """短狗粮路径：三元组 ON ⇒ 竖主 SKU 进 registry；OFF ⇒ 不可见。"""
    trip_id = "mtso-dogfood-trip"
    app_on = replace(
        get_config(),
        mosaic=replace(
            get_config().mosaic,
            template_contract=TemplateContractConfig(enabled=True, shadow_log=False),
            template_experiments=TemplateExperimentsConfig(
                enabled=True,
                allowlist=(PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO,),
                cohort_trip_ids=(trip_id,),
            ),
            selection_optimization=SelectionOptimizationConfig(
                enabled=True,
                mixed_hero_routing_enabled=True,
            ),
        ),
    )
    monkeypatch.setattr("travelogue.config.get_config", lambda: app_on)
    reset_engine_cache_for_tests()
    assert lifecycle_admit(
        PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO,
        app=app_on,
        trip_id=trip_id,
    ).ok
    assert PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO in mosaic_registry(
        cfg=app_on, trip_id=trip_id
    )
    assert not lifecycle_admit(
        PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO, app=app_on, trip_id=None
    ).ok
