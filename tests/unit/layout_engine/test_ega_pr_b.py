"""EGA PR-B · size=6 kept for equal-grid after hero-6 precheck fail (AC-EGA-06)."""

from __future__ import annotations

import dataclasses

import pytest

from travelogue.config import get_config
from travelogue.config.mosaic import (
    MosaicConfig,
    MosaicDensityBudgetConfig,
    NearSceneCloneGateConfig,
    SelectionOptimizationConfig,
    TemplateContractConfig,
    TemplateExperimentsConfig,
    effective_ega_keep_equal_six,
)
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_engine.mosaic.candidates import (
    generate_window_candidates_with_rejections,
)
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_LANDSCAPE_6,
    PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
)
from travelogue.layout_engine.mosaic.hero_six import qualify_hero_six
from travelogue.layout_engine.mosaic.hook import (
    begin_mosaic_capture,
    drain_mosaic_capture,
    try_mosaic_window,
)
from travelogue.layout_engine.mosaic.lifecycle import six_hero_family_id
from travelogue.layout_engine.planner.screen_planner_stages import build_chapter_plan_context
from travelogue.layout_templates.registry import reset_engine_cache_for_tests


@pytest.fixture(autouse=True)
def _reset_engine() -> None:
    reset_engine_cache_for_tests()
    yield
    reset_engine_cache_for_tests()


def _six_flat_landscape() -> tuple[list[str], dict, dict]:
    """Uniform 6L window → hero gap below threshold → admit=false."""
    stamps = [f"2025-06-23T10:0{i}:00Z" for i in range(6)]
    ids = [f"a{i}" for i in range(6)]
    assets = {
        aid: {
            "id": aid,
            "takenAt": stamps[i],
            "shotGroupId": "sg-scene-0",
            "sceneClusterId": "0",
            "tags": ["person", "face"],
            "width": 3200,
            "height": 2133,
            "quality": {"sharpness": 0.7},
            "aspectKind": "landscape",
        }
        for i, aid in enumerate(ids)
    }
    aspects = {aid: "landscape" for aid in ids}
    return ids, aspects, assets


def _six_admit_landscape() -> tuple[list[str], dict, dict]:
    """One ladder main + five off-ladder → gap=inf → admit=true (MTSO SUP-02)."""
    ids = [f"l{i}" for i in range(6)]
    aspects = {aid: "landscape" for aid in ids}
    assets = {
        "l0": {
            "id": "l0",
            "width": 3000,
            "height": 1687,
            "takenAt": "2024-06-01T12:00:00Z",
            "aspectKind": "landscape",
            "quality": {"sharpness": 0.9},
            "shotGroupId": "sg-scene-0",
            "sceneClusterId": "0",
            "tags": ["person", "face"],
        },
        **{
            f"l{i}": {
                "id": f"l{i}",
                "width": 1900,
                "height": 1000,
                "takenAt": f"2024-06-01T12:0{i}:00Z",
                "aspectKind": "landscape",
                "quality": {"sharpness": 0.5},
                "shotGroupId": "sg-scene-0",
                "sceneClusterId": "0",
                "tags": ["person"],
            }
            for i in range(1, 6)
        },
    }
    return ids, aspects, assets


def _cfg(*, ega_enabled: bool = True) -> MosaicConfig:
    base = MosaicConfig()
    return dataclasses.replace(
        base,
        enabled=True,
        enabled_window_sizes=(4, 5, 6),
        min_candidate_score=0.0,
        density_budget=MosaicDensityBudgetConfig(
            enabled=True,
            window_order=(5, 4, 6),
        ),
        template_contract=TemplateContractConfig(enabled=False, shadow_log=False),
        template_experiments=TemplateExperimentsConfig(
            enabled=False, allowlist=(), cohort_trip_ids=()
        ),
        near_scene_clone_gate=NearSceneCloneGateConfig(
            enabled=True, conditional=False
        ),
        selection_optimization=SelectionOptimizationConfig(
            enabled=True,
            hero_six_opportunity_enabled=True,
            mixed_hero_routing_enabled=True,
            hero_gap_threshold=0.15,
        ),
        equal_grid_admission=dataclasses.replace(
            base.equal_grid_admission, enabled=ega_enabled
        ),
    )


def _install_cfg(monkeypatch, cfg: MosaicConfig) -> MosaicConfig:
    app = dataclasses.replace(get_config(), mosaic=cfg)
    monkeypatch.setattr("travelogue.config.get_config", lambda: app)
    return cfg


@pytest.mark.unit
def test_ega_keep_equal_six_helper() -> None:
    on = _cfg(ega_enabled=True)
    off = _cfg(ega_enabled=False)
    assert effective_ega_keep_equal_six(on) is True
    assert effective_ega_keep_equal_six(off) is False
    gated = dataclasses.replace(
        on,
        equal_grid_admission=dataclasses.replace(
            on.equal_grid_admission,
            size6=dataclasses.replace(
                on.equal_grid_admission.size6,
                keep_equal_grid_after_hero_precheck_fail=False,
            ),
        ),
    )
    assert effective_ega_keep_equal_six(gated) is False


@pytest.mark.unit
def test_ac_ega_06_candidates_skip_hero_keep_landscape6() -> None:
    """AC-EGA-06 · allow_six_hero=False → hero-6 rejected; landscape-6 evaluated."""
    ids, aspects, assets = _six_flat_landscape()
    cfg = _cfg(ega_enabled=True)
    res = generate_window_candidates_with_rejections(
        ids, aspects, assets, cfg=cfg, allow_six_hero=False
    )
    hero_rejects = [
        r
        for r in res.rejected
        if six_hero_family_id(str(r.get("templateId") or ""))
        and r.get("reason") == "six_hero_precheck"
        and r.get("detail") == "ega_equal_six_only"
    ]
    assert hero_rejects, "six-hero family must be skipped under equal-six-only"
    assert any(
        c.pattern_id == PATTERN_LANDSCAPE_6 and c.hard_valid for c in res.candidates
    ) or any(
        r.get("templateId") == PATTERN_LANDSCAPE_6
        and r.get("reason") not in ("pattern_disabled", "lifecycle_deprecated")
        for r in res.rejected
    ), "landscape-6 must be considered (scored or non-lifecycle reject)"
    # Must not silently omit landscape-6 from the try set.
    seen_ids = {c.pattern_id for c in res.candidates} | {
        str(r.get("templateId") or "") for r in res.rejected
    }
    assert PATTERN_LANDSCAPE_6 in seen_ids
    assert PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5 in {
        str(r.get("templateId") or "") for r in res.rejected
    } or PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4 in {
        str(r.get("templateId") or "") for r in res.rejected
    }


@pytest.mark.unit
def test_ac_ega_06_funnel_keeps_size6_and_probe_flag(monkeypatch) -> None:
    """AC-EGA-06 · precheck fail → sizes still contain 6; probe has egaEqualSixKept."""
    cfg = _install_cfg(monkeypatch, _cfg(ega_enabled=True))
    ids, aspects, assets = _six_flat_landscape()
    st = ScreenLayoutPlannerState.from_trip_total(40)
    q = qualify_hero_six(
        ids, aspects, assets, cfg=cfg, layout_state=st, seg_cap=6, median_sharp=0.7
    )
    assert q.admit is False

    ctx = build_chapter_plan_context(
        ids,
        aspects,
        assets=assets,
        trip_photo_total=40,
        include_chapter_hero=False,
        layout_state=st,
    )
    begin_mosaic_capture()
    try_mosaic_window(ctx, 0)
    _formatted, raw = drain_mosaic_capture()
    assert raw

    probes = [
        e
        for e in raw
        if e.get("fallbackReason") == "six_hero_precheck" and e.get("windowSize") == 6
    ]
    assert probes, "expected six_hero_precheck probe"
    probe = probes[0]
    assert probe.get("egaEqualSixKept") is True
    order = list(probe.get("effectiveWindowOrder") or [])
    assert 6 in order

    # At least one size=6 MCS attempt that considered equal-six (L6 or hero skip).
    size6_attempts = [
        e
        for e in raw
        if e.get("windowSize") == 6 and e.get("fallbackReason") != "six_hero_precheck"
    ]
    assert size6_attempts, (
        "size=6 must still be attempted after precheck fail (not deleted from funnel)"
    )
    landscape_or_skip = False
    for e in size6_attempts:
        win = str(e.get("winnerPatternId") or "")
        rej = list(e.get("rejectedTemplates") or [])
        rej_ids = {str(r.get("templateId") or "") for r in rej}
        if (
            win == PATTERN_LANDSCAPE_6
            or PATTERN_LANDSCAPE_6 in rej_ids
            or PATTERN_LANDSCAPE_6 in (e.get("top3Patterns") or [])
            or any(
                six_hero_family_id(str(r.get("templateId") or ""))
                and r.get("detail") == "ega_equal_six_only"
                for r in rej
            )
        ):
            landscape_or_skip = True
            break
    assert landscape_or_skip, "equal-six path must evaluate L6 or skip hero-6 with ega detail"


@pytest.mark.unit
def test_ega_admit_true_keeps_hero_six_family() -> None:
    """PRD §9 · admit × equal-6 矩阵：admit 路径不得 ega_equal_six_only 清 hero-6."""
    ids, aspects, assets = _six_admit_landscape()
    cfg = _cfg(ega_enabled=True)
    res = generate_window_candidates_with_rejections(
        ids, aspects, assets, cfg=cfg, allow_six_hero=True
    )
    assert not any(
        six_hero_family_id(str(r.get("templateId") or ""))
        and r.get("detail") == "ega_equal_six_only"
        for r in res.rejected
    )
    # Hero family still evaluated (candidate or non-ega reject).
    seen = {c.pattern_id for c in res.candidates} | {
        str(r.get("templateId") or "") for r in res.rejected
    }
    assert PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5 in seen or PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4 in seen


@pytest.mark.unit
def test_ega_admit_funnel_no_equal_six_kept(monkeypatch) -> None:
    """admit=true → egaEqualSixKept false；size=6 仍可胜出 hero 族（不强制 L6）."""
    cfg = _install_cfg(monkeypatch, _cfg(ega_enabled=True))
    ids, aspects, assets = _six_admit_landscape()
    st = ScreenLayoutPlannerState.from_trip_total(40)
    q = qualify_hero_six(
        ids, aspects, assets, cfg=cfg, layout_state=st, seg_cap=6, median_sharp=0.5
    )
    assert q.admit is True

    ctx = build_chapter_plan_context(
        ids,
        aspects,
        assets=assets,
        trip_photo_total=40,
        include_chapter_hero=False,
        layout_state=st,
    )
    begin_mosaic_capture()
    try_mosaic_window(ctx, 0)
    _formatted, raw = drain_mosaic_capture()
    assert raw
    for e in raw:
        assert e.get("egaEqualSixKept") is not True
    admitted = [e for e in raw if e.get("admitSixHero") is True]
    assert admitted, "expected at least one admitSixHero=true funnel log"
    # size=6 attempt must not stamp ega_equal_six_only rejects when admitted.
    for e in raw:
        if e.get("windowSize") != 6:
            continue
        assert not any(
            r.get("detail") == "ega_equal_six_only"
            for r in (e.get("rejectedTemplates") or [])
        )


@pytest.mark.unit
def test_ac_ega_08_cross_shot_group_still_hard_under_ega() -> None:
    """AC-EGA-08 / D-EGA-12 · EGA 不放宽跨组 slice 硬拒."""
    from dataclasses import replace as dc_replace

    from travelogue.config.shot_grouping import resolve_shot_group_mosaic_policy
    from travelogue.layout_engine.mosaic.constants import PATTERN_LANDSCAPE_4
    from travelogue.layout_engine.mosaic.shot_group_gate import hard_reject_cross_shot_group

    stamps = (
        "2025-06-23T10:00:00Z",
        "2025-06-23T10:00:20Z",
        "2025-06-23T10:00:40Z",
        "2025-06-23T10:01:00Z",
    )
    ids = [f"x{i}" for i in range(4)]
    assets = {
        aid: {
            "id": aid,
            "takenAt": stamps[i],
            "shotGroupId": f"sg-{i % 2}",  # two groups → cross
            "sceneClusterId": "0",
            "tags": ["person"],
            "width": 3200,
            "height": 1800,
            "quality": {"sharpness": 0.8},
            "aspectKind": "landscape",
        }
        for i, aid in enumerate(ids)
    }
    aspects = {aid: "landscape" for aid in ids}
    # Gate helper itself still fires (independent of atom packing).
    assert hard_reject_cross_shot_group(PATTERN_LANDSCAPE_4, ids, assets)
    # Candidates path: disable atom so cross reason is visible (atom would mask it).
    policy = resolve_shot_group_mosaic_policy()
    policy = dc_replace(policy, atom=dc_replace(policy.atom, enabled=False))
    cfg = _cfg(ega_enabled=True)
    res = generate_window_candidates_with_rejections(
        ids, aspects, assets, cfg=cfg, ssg_policy=policy
    )
    assert any(
        r.get("templateId") == PATTERN_LANDSCAPE_4
        and r.get("reason") == "shot_group_cross"
        for r in res.rejected
    ), "landscape-4 must still hard-reject cross-shotGroup under EGA"
    assert not any(c.pattern_id == PATTERN_LANDSCAPE_4 for c in res.candidates)


@pytest.mark.unit
def test_ac_ega_08_megc_sixteen_nine_still_allows_with_ega() -> None:
    """AC-EGA-08 · EGA 不改 MEGC allow_peaks；16:9 电影峰仍 gate_allow."""
    from travelogue.config.mosaic import EqualGridContractConfig, EqualGridSelectionGateConfig
    from travelogue.layout_engine.mosaic.constants import PATTERN_LANDSCAPE_4
    from travelogue.layout_engine.mosaic.megc_gate import evaluate_megc_gate

    assets = [
        {
            "id": f"m{i}",
            "width": 3840,
            "height": 2160,  # 16:9
            "takenAt": f"2019-06-01T12:0{i}:00Z",
        }
        for i in range(4)
    ]
    cfg = dataclasses.replace(
        _cfg(ega_enabled=True),
        equal_grid_contract=EqualGridContractConfig(
            enabled=True,
            selection_gate=EqualGridSelectionGateConfig(
                enabled=True,
                mode="soft_penalty",
                score_mul=0.62,
                allow_peaks=("sixteen_nine",),
            ),
        ),
    )
    decision = evaluate_megc_gate(PATTERN_LANDSCAPE_4, assets, cfg)
    assert decision.outcome == "gate_allow"
    assert decision.land_peak == "sixteen_nine"
