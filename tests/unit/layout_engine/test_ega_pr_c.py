"""EGA PR-C · flat-window equal-grid bonus / hero-70 wasted extra (AC-EGA-07)."""

from __future__ import annotations

import dataclasses

import pytest

from travelogue.config.mosaic import (
    EqualGridContractConfig,
    MosaicConfig,
    MosaicDensityBudgetConfig,
    NearSceneCloneGateConfig,
    TemplateContractConfig,
    TemplateExperimentsConfig,
    ega_flat_window_equal_bonus,
    ega_wasted_hero_extra,
    is_ega_hero70_family,
    mosaic_from_dict,
)
from travelogue.layout_engine.mosaic.builders import build_screen
from travelogue.layout_engine.mosaic.constants import PATTERN_LANDSCAPE_4
from travelogue.layout_engine.mosaic.pattern_catalog import patterns_for_window_size
from travelogue.layout_engine.mosaic.scorer import score_candidate
from travelogue.layout_templates.registry import reset_engine_cache_for_tests

PATTERN_HERO70 = "screen-mosaic-4-hero-70-sidebar"


@pytest.fixture(autouse=True)
def _reset_engine() -> None:
    reset_engine_cache_for_tests()
    yield
    reset_engine_cache_for_tests()


def _four_flat_landscape() -> tuple[dict, dict]:
    """Uniform quality 4L → low hero gap (flat window)."""
    stamps = (
        "2025-06-23T10:00:00Z",
        "2025-06-23T10:05:00Z",
        "2025-06-23T10:10:00Z",
        "2025-06-23T10:15:00Z",
    )
    assets = {
        f"a{i}": {
            "id": f"a{i}",
            "takenAt": stamps[i],
            "shotGroupId": f"sg-{i}",  # avoid clone/anti-slice noise
            "sceneClusterId": "0",
            "tags": ["person", "face"],
            "width": 3200,
            "height": 2133,
            "quality": {"sharpness": 0.7},
        }
        for i in range(4)
    }
    aspects = {aid: "landscape" for aid in assets}
    return assets, aspects


def _cfg(
    *,
    ega_enabled: bool = True,
    flat_bonus: float | None = None,
    wasted_extra: float | None = None,
) -> MosaicConfig:
    base = MosaicConfig()
    scoring = base.equal_grid_admission.scoring
    if flat_bonus is not None or wasted_extra is not None:
        scoring = dataclasses.replace(
            scoring,
            flat_window_equal_bonus=(
                scoring.flat_window_equal_bonus if flat_bonus is None else flat_bonus
            ),
            wasted_hero_ega_extra=(
                scoring.wasted_hero_ega_extra if wasted_extra is None else wasted_extra
            ),
        )
    return dataclasses.replace(
        base,
        density_budget=MosaicDensityBudgetConfig(enabled=False),
        template_contract=TemplateContractConfig(enabled=False, shadow_log=False),
        template_experiments=TemplateExperimentsConfig(
            enabled=False, allowlist=(), cohort_trip_ids=()
        ),
        near_scene_clone_gate=NearSceneCloneGateConfig(
            enabled=False, conditional=False
        ),
        # Isolate PR-C from MEGC 3:2 demote (orthogonal · D-EGA-08).
        equal_grid_contract=EqualGridContractConfig(enabled=False),
        equal_grid_admission=dataclasses.replace(
            base.equal_grid_admission,
            enabled=ega_enabled,
            scoring=scoring,
        ),
    )


def _screens(assets: dict, aspects: dict) -> tuple[dict, dict]:
    pats = {p.pattern_id: p for p in patterns_for_window_size(4, cfg=_cfg())}
    assert PATTERN_LANDSCAPE_4 in pats
    assert PATTERN_HERO70 in pats
    ids = list(assets)
    l4 = build_screen(pats[PATTERN_LANDSCAPE_4], ids, assets_map=assets)
    hero = build_screen(pats[PATTERN_HERO70], ids, assets_map=assets)
    assert l4 and hero
    return l4, hero


@pytest.mark.unit
def test_ega_scoring_helpers_and_hero70_family() -> None:
    on = _cfg(ega_enabled=True)
    off = _cfg(ega_enabled=False)
    assert ega_flat_window_equal_bonus(on) == pytest.approx(0.08)
    assert ega_wasted_hero_extra(on) == pytest.approx(0.10)
    assert ega_flat_window_equal_bonus(off) == 0.0
    assert ega_wasted_hero_extra(off) == 0.0
    assert is_ega_hero70_family(PATTERN_HERO70)
    assert not is_ega_hero70_family(PATTERN_LANDSCAPE_4)

    zero = mosaic_from_dict(
        {
            "equal_grid_admission": {
                "enabled": True,
                "scoring": {
                    "flat_window_equal_bonus": 0,
                    "wasted_hero_ega_extra": 0,
                },
            }
        }
    )
    assert ega_flat_window_equal_bonus(zero) == 0.0
    assert ega_wasted_hero_extra(zero) == 0.0


@pytest.mark.unit
def test_ac_ega_07_flat_window_landscape4_beats_or_ties_hero70() -> None:
    """AC-EGA-07 · flat 4L：equal-grid 分 ≥ hero-70（或胜出）。"""
    assets, aspects = _four_flat_landscape()
    l4_screen, hero_screen = _screens(assets, aspects)
    cfg = _cfg(ega_enabled=True)
    sr_l4 = score_candidate(
        l4_screen, aspects=aspects, assets_by_id=assets, cfg=cfg
    )
    sr_hero = score_candidate(
        hero_screen, aspects=aspects, assets_by_id=assets, cfg=cfg
    )
    assert "R_EGA_FLAT_BONUS" in sr_l4.reason_codes
    assert "R_EGA_WASTED_HERO" in sr_hero.reason_codes
    assert sr_l4.total >= sr_hero.total


@pytest.mark.unit
def test_ac_ega_07_bonus_zero_disables_flat_bias() -> None:
    """bonus/extra=0 → 无 R_EGA_FLAT_BONUS / R_EGA_WASTED_HERO。"""
    assets, aspects = _four_flat_landscape()
    l4_screen, hero_screen = _screens(assets, aspects)
    cfg = _cfg(ega_enabled=True, flat_bonus=0.0, wasted_extra=0.0)
    sr_l4 = score_candidate(
        l4_screen, aspects=aspects, assets_by_id=assets, cfg=cfg
    )
    sr_hero = score_candidate(
        hero_screen, aspects=aspects, assets_by_id=assets, cfg=cfg
    )
    assert "R_EGA_FLAT_BONUS" not in sr_l4.reason_codes
    assert "R_EGA_WASTED_HERO" not in sr_hero.reason_codes


@pytest.mark.unit
def test_ega_off_no_flat_bias_codes() -> None:
    assets, aspects = _four_flat_landscape()
    l4_screen, hero_screen = _screens(assets, aspects)
    cfg = _cfg(ega_enabled=False)
    sr_l4 = score_candidate(
        l4_screen, aspects=aspects, assets_by_id=assets, cfg=cfg
    )
    sr_hero = score_candidate(
        hero_screen, aspects=aspects, assets_by_id=assets, cfg=cfg
    )
    assert "R_EGA_FLAT_BONUS" not in sr_l4.reason_codes
    assert "R_EGA_WASTED_HERO" not in sr_hero.reason_codes
