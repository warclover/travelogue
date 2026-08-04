"""EGA · L6 auto-match P0–P3 (atom soften / pure-6 prefer / quota / flood)."""

from __future__ import annotations

import dataclasses

import pytest

from travelogue.config.mosaic import (
    EqualGridAdmissionConfig,
    EqualGridAdmissionSize6Config,
    MosaicConfig,
    NearSceneCloneGateConfig,
    TemplateContractConfig,
    TemplateExperimentsConfig,
    effective_ega_l6_large_quota_exempt,
    effective_ega_prefer_pure_landscape_six,
    effective_ega_soften_atom_valid_invalid_mix,
)
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_engine.mosaic.candidates import (
    generate_window_candidates_with_rejections,
)
from travelogue.layout_engine.mosaic.constants import PATTERN_LANDSCAPE_6
from travelogue.layout_engine.mosaic.hook import (
    _prioritize_equal_six_pure_landscape,
    _ega_landscape1_flood_reopen,
)
from travelogue.layout_templates.registry import reset_engine_cache_for_tests


@pytest.fixture(autouse=True)
def _reset_engine() -> None:
    reset_engine_cache_for_tests()
    yield
    reset_engine_cache_for_tests()


def _cfg(**size6_kw) -> MosaicConfig:
    base = MosaicConfig(
        enabled=True,
        near_scene_clone_gate=NearSceneCloneGateConfig(enabled=False),
        template_contract=TemplateContractConfig(enabled=False),
        template_experiments=TemplateExperimentsConfig(enabled=False),
        equal_grid_admission=EqualGridAdmissionConfig(
            enabled=True,
            size6=EqualGridAdmissionSize6Config(**size6_kw),
        ),
    )
    return base


def _mixed_cluster_six() -> tuple[list[str], dict, dict]:
    """Same shotGroup; sceneCluster -1 then 0 → pre-EGA atom_boundary."""
    ids = [f"a{i}" for i in range(6)]
    assets = {
        aid: {
            "id": aid,
            "takenAt": f"2025-06-23T10:0{i}:00Z",
            "shotGroupId": "sg-scene-0",
            "sceneClusterId": -1 if i < 2 else 0,
            "width": 3200,
            "height": 2133,
            "aspectKind": "landscape",
            "quality": {"sharpness": 0.7},
            "tags": ["person"],
        }
        for i, aid in enumerate(ids)
    }
    aspects = {aid: "landscape" for aid in ids}
    return ids, aspects, assets


def test_p0_atom_soften_allows_valid_invalid_mix_on_l6() -> None:
    ids, aspects, assets = _mixed_cluster_six()
    on = _cfg(soften_atom_valid_invalid_mix=True)
    off = _cfg(soften_atom_valid_invalid_mix=False)

    res_on = generate_window_candidates_with_rejections(
        ids, aspects, assets, cfg=on, allow_six_hero=False
    )
    res_off = generate_window_candidates_with_rejections(
        ids, aspects, assets, cfg=off, allow_six_hero=False
    )

    assert any(c.pattern_id == PATTERN_LANDSCAPE_6 for c in res_on.candidates)
    assert not any(c.pattern_id == PATTERN_LANDSCAPE_6 for c in res_off.candidates)
    assert any(
        r.get("templateId") == PATTERN_LANDSCAPE_6
        and r.get("reason") == "atom_boundary"
        and r.get("detail") == "scene_cluster_valid_invalid_mix"
        for r in res_off.rejected
    )


def test_p0_atom_soften_still_rejects_cross_shot_group() -> None:
    ids, aspects, assets = _mixed_cluster_six()
    assets["a3"]["shotGroupId"] = "sg-other"
    cfg = _cfg(soften_atom_valid_invalid_mix=True)
    res = generate_window_candidates_with_rejections(
        ids, aspects, assets, cfg=cfg, allow_six_hero=False
    )
    assert not any(c.pattern_id == PATTERN_LANDSCAPE_6 for c in res.candidates)
    assert any(
        r.get("templateId") == PATTERN_LANDSCAPE_6 and r.get("reason") == "atom_boundary"
        for r in res.rejected
    )


def test_p1_prefer_pure_landscape_six_order() -> None:
    cfg = _cfg(prefer_pure_landscape_window=True)
    assert effective_ega_prefer_pure_landscape_six(cfg) is True
    ids = [f"a{i}" for i in range(6)]
    aspects = {aid: "landscape" for aid in ids}
    ordered = _prioritize_equal_six_pure_landscape(
        [5, 4, 6, 9], ids, aspects, cfg=cfg
    )
    assert ordered[0] == 6
    off = _cfg(prefer_pure_landscape_window=False)
    assert _prioritize_equal_six_pure_landscape([5, 4, 6, 9], ids, aspects, cfg=off) == [
        5,
        4,
        6,
        9,
    ]
    st = ScreenLayoutPlannerState(nine_min=0, nine_max=0)
    st.last_pattern_id = PATTERN_LANDSCAPE_6
    assert _prioritize_equal_six_pure_landscape(
        [5, 4, 6, 9], ids, aspects, cfg=cfg, layout_state=st
    ) == [5, 4, 6, 9]


def test_p2_l6_large_quota_exempt() -> None:
    cfg = _cfg(large_mosaic_quota_exempt=True)
    assert effective_ega_l6_large_quota_exempt(cfg) is True
    st = ScreenLayoutPlannerState(nine_min=0, nine_max=0)
    st.large_mosaic_min_slots = 5
    st.large_mosaic_max_per_chapter = 1
    st.large_mosaic_chapter_used = 1
    from unittest.mock import patch

    from travelogue.config import get_config, reset_config_cache

    reset_config_cache()
    live = get_config(reload=True)
    fake = dataclasses.replace(live, mosaic=cfg)
    with patch("travelogue.config.get_config", return_value=fake):
        assert st.can_use_large_mosaic(PATTERN_LANDSCAPE_6) is True
        st.note_screen(PATTERN_LANDSCAPE_6)
        assert st.large_mosaic_chapter_used == 1  # L6 did not consume
        st.note_screen("screen-mosaic-5-3p2l-portrait-hero-quad")
        assert st.large_mosaic_chapter_used == 2


def test_p3_flood_reopen_gate() -> None:
    cfg = _cfg(landscape1_flood_reopen_after=4)

    class _Ctx:
        layout_state = ScreenLayoutPlannerState(nine_min=0, nine_max=0)

    ctx = _Ctx()
    ctx.layout_state.last_pattern_id = "screen-landscape-1"
    ctx.layout_state.pattern_streak = 4
    assert _ega_landscape1_flood_reopen(ctx, cfg=cfg, remaining=6) is True
    ctx.layout_state.pattern_streak = 3
    assert _ega_landscape1_flood_reopen(ctx, cfg=cfg, remaining=6) is False
    off = _cfg(landscape1_flood_reopen_after=0)
    ctx.layout_state.pattern_streak = 10
    assert _ega_landscape1_flood_reopen(ctx, cfg=off, remaining=6) is False
