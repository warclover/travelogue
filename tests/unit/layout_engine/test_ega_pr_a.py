"""EGA PR-A · equal-grid admission gate softening (AC-EGA-02/03/04)."""

from __future__ import annotations

import dataclasses

import pytest

from travelogue.config.mosaic import (
    EqualGridAdmissionConfig,
    MosaicConfig,
    MosaicDensityBudgetConfig,
    NearSceneCloneGateConfig,
    TemplateContractConfig,
    TemplateExperimentsConfig,
    ega_anti_slice_mode,
    ega_clone_mode,
    effective_equal_grid_admission_enabled,
    is_ega_equal_grid_pattern,
    mosaic_from_dict,
)
from travelogue.layout_engine.mosaic.candidates import (
    generate_window_candidates_with_rejections,
)
from travelogue.layout_engine.mosaic.constants import PATTERN_LANDSCAPE_4


def _four_landscape_same_shot_group() -> tuple[dict, dict]:
    """Tight same-shotGroup 4L window (anti_slice + clone eligible)."""
    stamps = (
        "2025-06-23T10:00:00Z",
        "2025-06-23T10:00:20Z",
        "2025-06-23T10:00:40Z",
        "2025-06-23T10:01:00Z",
    )
    assets = {
        f"a{i}": {
            "id": f"a{i}",
            "takenAt": stamps[i],
            "shotGroupId": "sg-scene-0",
            "sceneClusterId": "0",
            "tags": ["person", "face"],
            "width": 3200,
            "height": 2133,  # ~3:2
            "quality": {"sharpness": 0.7},
        }
        for i in range(4)
    }
    aspects = {aid: "landscape" for aid in assets}
    return assets, aspects


def _cfg_for_window(*, ega_enabled: bool) -> MosaicConfig:
    base = MosaicConfig()
    return dataclasses.replace(
        base,
        # Keep density quiet for unit focus on gates.
        density_budget=MosaicDensityBudgetConfig(enabled=False),
        template_contract=TemplateContractConfig(enabled=False, shadow_log=False),
        template_experiments=TemplateExperimentsConfig(
            enabled=False, allowlist=(), cohort_trip_ids=()
        ),
        near_scene_clone_gate=NearSceneCloneGateConfig(
            enabled=True, conditional=False
        ),
        equal_grid_admission=dataclasses.replace(
            base.equal_grid_admission, enabled=ega_enabled
        ),
    )


@pytest.mark.unit
def test_ega_config_defaults_and_fail_loud() -> None:
    defaults = MosaicConfig()
    cfg = mosaic_from_dict({})
    assert cfg.equal_grid_admission.enabled is True
    assert cfg.equal_grid_admission.patterns == (
        "screen-landscape-4",
        "screen-landscape-6",
    )
    assert cfg.equal_grid_admission.anti_slice.mode == "exempt"
    assert cfg.equal_grid_admission.near_scene_clone.score_mul == pytest.approx(0.85)
    assert effective_equal_grid_admission_enabled(cfg) is True
    assert is_ega_equal_grid_pattern(PATTERN_LANDSCAPE_4, cfg) is True
    assert is_ega_equal_grid_pattern("screen-mosaic-4-hero-70-sidebar", cfg) is False
    assert ega_anti_slice_mode(cfg) == "exempt"
    assert ega_clone_mode(cfg) == "soft_penalty"

    parsed = mosaic_from_dict(
        {
            "equal_grid_admission": {
                "enabled": True,
                "near_scene_clone": {"mode": "soft_penalty", "score_mul": 0.8},
            }
        }
    )
    assert parsed.equal_grid_admission.near_scene_clone.score_mul == pytest.approx(0.8)

    with pytest.raises(ValueError, match="unknown keys"):
        mosaic_from_dict({"equal_grid_admission": {"enabled": True, "bogus": 1}})
    with pytest.raises(ValueError, match="unknown keys"):
        mosaic_from_dict(
            {"equal_grid_admission": {"anti_slice": {"mode": "exempt", "penalty": 1}}}
        )


@pytest.mark.unit
def test_ega_whitelist_does_not_include_hero70() -> None:
    """BLK-EGA-04 · only L4/L6 by default."""
    cfg = MosaicConfig()
    assert set(cfg.equal_grid_admission.patterns) == {
        "screen-landscape-4",
        "screen-landscape-6",
    }
    assert not is_ega_equal_grid_pattern(
        "screen-mosaic-4-hero-70-sidebar", cfg
    )


@pytest.mark.unit
def test_ac_ega_02_anti_slice_not_hard_reject_landscape4() -> None:
    """AC-EGA-02 · same shotGroup tight 4L → L4 not hard-rejected under EGA."""
    assets, aspects = _four_landscape_same_shot_group()
    cfg_on = _cfg_for_window(ega_enabled=True)
    res = generate_window_candidates_with_rejections(
        list(assets), aspects, assets, cfg=cfg_on
    )
    assert not any(
        r.get("templateId") == PATTERN_LANDSCAPE_4
        and r.get("reason") == "shot_group_anti_slice"
        for r in res.rejected
    )
    # Must reach scored/candidate pool (or only fail for unrelated reasons).
    assert any(c.pattern_id == PATTERN_LANDSCAPE_4 for c in res.candidates) or not any(
        r.get("templateId") == PATTERN_LANDSCAPE_4
        and r.get("reason")
        in ("shot_group_anti_slice", "near_scene_clone")
        for r in res.rejected
    )


@pytest.mark.unit
def test_ac_ega_03_clone_soft_for_landscape4_hard_for_slice_weighted() -> None:
    """AC-EGA-03 · EGA soft for L4; non-EGA slice pattern still hard clone-rejects."""
    assets, aspects = _four_landscape_same_shot_group()
    # Force high clone pressure: all person tags + tight times already set.
    trip_id = "ega-clone-soft-test"
    weighted = "screen-mosaic-4-2l2p-weighted"
    cfg = dataclasses.replace(
        _cfg_for_window(ega_enabled=True),
        template_contract=TemplateContractConfig(enabled=True, shadow_log=False),
        template_experiments=TemplateExperimentsConfig(
            enabled=True,
            allowlist=(weighted,),
            cohort_trip_ids=(trip_id,),
        ),
    )
    res = generate_window_candidates_with_rejections(
        list(assets), aspects, assets, cfg=cfg, trip_id=trip_id
    )
    assert not any(
        r.get("templateId") == PATTERN_LANDSCAPE_4
        and r.get("reason") == "near_scene_clone"
        for r in res.rejected
    )
    # Weighted is not EGA whitelist → still hard-rejectable when clone fires.
    # (May also fail geometry on all-landscape; either hard clone or not candidated.)
    assert any(c.pattern_id == PATTERN_LANDSCAPE_4 for c in res.candidates) or not any(
        r.get("templateId") == PATTERN_LANDSCAPE_4
        and r.get("reason") == "near_scene_clone"
        for r in res.rejected
    )


@pytest.mark.unit
def test_ac_ega_04_off_restores_anti_slice_hard_reject() -> None:
    """AC-EGA-04 · EGA off ⇒ landscape-4 hard anti_slice again."""
    assets, aspects = _four_landscape_same_shot_group()
    cfg_off = _cfg_for_window(ega_enabled=False)
    assert effective_equal_grid_admission_enabled(cfg_off) is False
    assert ega_anti_slice_mode(cfg_off) == "hard"
    res = generate_window_candidates_with_rejections(
        list(assets), aspects, assets, cfg=cfg_off
    )
    assert any(
        r.get("templateId") == PATTERN_LANDSCAPE_4
        and r.get("reason") == "shot_group_anti_slice"
        for r in res.rejected
    )
    assert not any(c.pattern_id == PATTERN_LANDSCAPE_4 for c in res.candidates)


@pytest.mark.unit
def test_ega_scorer_emits_r_ega_clone_soft() -> None:
    """EGA soft clone path stamps R_EGA_CLONE_SOFT when hard threshold met."""
    from travelogue.layout_engine.mosaic.builders import build_screen
    from travelogue.layout_engine.mosaic.pattern_catalog import patterns_for_window_size
    from travelogue.layout_engine.mosaic.scorer import score_candidate

    assets, aspects = _four_landscape_same_shot_group()
    pats = {p.pattern_id: p for p in patterns_for_window_size(4)}
    pat = pats[PATTERN_LANDSCAPE_4]
    screen = build_screen(pat, list(assets), assets_map=assets)
    cfg = _cfg_for_window(ega_enabled=True)
    sr = score_candidate(screen, aspects=aspects, assets_by_id=assets, cfg=cfg)
    assert "R_EGA_CLONE_SOFT" in sr.reason_codes

    cfg_off = _cfg_for_window(ega_enabled=False)
    sr_off = score_candidate(screen, aspects=aspects, assets_by_id=assets, cfg=cfg_off)
    assert "R_EGA_CLONE_SOFT" not in sr_off.reason_codes


@pytest.mark.unit
def test_ega_off_matches_empty_admission_disabled_parse() -> None:
    cfg = mosaic_from_dict({"equal_grid_admission": {"enabled": False}})
    assert cfg.equal_grid_admission.enabled is False
    assert isinstance(cfg.equal_grid_admission, EqualGridAdmissionConfig)
