"""LTN Wave A · H6 / H8 / R-A3 / C2 regression locks."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import MagicMock

from travelogue.config import get_config
from travelogue.layout_contract.density import LayoutDensityParams
from travelogue.layout_engine.mosaic.hook import try_mosaic_window
from travelogue.layout_engine.mosaic.scorer import _duplicate_density_penalty
from travelogue.layout_templates.models import TemplateDef, TemplateSlot, TemplateStage
from travelogue.layout_templates.validator import (
    _GRANDFATHERED_DENSE_SLOT_IDS,
    validate_template_def,
)


def test_h6_s1_prefers_burst_skips_duplicate_density_penalty(monkeypatch) -> None:
    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.scorer.template_prefers_burst",
        lambda pid: True if pid == "screen-mosaic-4-hero-70-sidebar" else False,
    )
    assets = {f"a{i}": {"id": f"a{i}", "burstGroupId": "bg-1"} for i in range(4)}
    ids = list(assets)
    assert (
        _duplicate_density_penalty(
            ids, assets, pattern_id="screen-mosaic-4-hero-70-sidebar"
        )
        == 0.0
    )
    assert _duplicate_density_penalty(ids, assets, pattern_id="screen-landscape-4") == 0.8


def test_h6_s3_dense_floor() -> None:
    params = LayoutDensityParams(density="hero_first")
    assert params.adjust_dense_collage_limits(0, 1)[1] == 1
    assert params.adjust_dense_collage_limits(0, 0)[1] == 0


def test_c2_hero_first_attempts_mcs(monkeypatch) -> None:
    """hero_first must no longer hard-return before MCS window tries."""
    cfg = replace(
        get_config().mosaic,
        enabled=True,
        enabled_window_sizes=(5, 4, 6),
    )
    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.hook._mosaic_cfg", lambda: cfg
    )
    called: list[int] = []

    def fake_mcs(ctx, start, size, mosaic_cfg, **_kwargs):
        called.append(size)
        return False

    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.hook.try_mosaic_window_mcs", fake_mcs
    )
    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.hook._defer_portrait_grid8",
        lambda *a, **k: False,
    )
    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.hook.planner_mosaic_window_sizes",
        lambda *a, **k: (5, 4, 6),
    )
    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.hook.window_has_candidates",
        lambda *a, **k: True,
    )
    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.hook._mixed_portrait_dense_skip",
        lambda *a, **k: False,
    )
    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.hook._single_portrait_dense_skip",
        lambda *a, **k: False,
    )
    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.hook._window_all_std_portrait",
        lambda *a, **k: False,
    )

    layout_state = MagicMock()
    layout_state.layout_density = "hero_first"
    layout_state.can_use_dense_collage_window.return_value = True
    layout_state.can_use_large_mosaic_window.return_value = True
    layout_state.large_mosaic_min_slots = 8
    layout_state.dense_collage_min_slots = 4

    ctx = MagicMock()
    ctx.enable_mosaic = True
    ctx.layout_state = layout_state
    ctx.ids = [f"a{i}" for i in range(10)]
    ctx.aspects = {aid: "landscape" for aid in ctx.ids}
    ctx.assets_map = {aid: {"id": aid} for aid in ctx.ids}
    ctx.screens = []
    ctx.mix_gap = 1800.0
    ctx.med_sharp = 0.5
    ctx.trip_total = 40
    ctx.chapter_id = "ch-01"
    ctx.burst_seconds = 1800.0
    ctx.use_portrait_grid8 = False

    assert try_mosaic_window(ctx, 0) is None
    assert called, "hero_first must attempt MCS windows (LTN C2)"


def test_a3_freeze_blocks_new_dense_sku() -> None:
    slots = tuple(
        TemplateSlot(index=i, rect=(i + 1, i + 1, 1, 1), role="support")
        for i in range(7)
    )
    tpl = TemplateDef(
        id="screen-mosaic-7-forbidden-new",
        version=1,
        status="experimental",
        kind="composite",
        display_name="forbidden",
        stage=TemplateStage(aspect="16:9", cols=(1,) * 7, rows=(1,), gap="2px"),
        photo_count_min=7,
        photo_count_max=7,
        slots=slots,
        render_grid_class="layout-screen__grid--x",
        render_css_bundle="journal-screens.css",
    )
    report = validate_template_def(tpl, mode="ci")
    assert any(i.code == "V-LTN-FREEZE" for i in report.issues)


def test_a3_grandfather_allows_grid8() -> None:
    assert "screen-portrait-grid-8" in _GRANDFATHERED_DENSE_SLOT_IDS


def test_h8_active_set_gate_script() -> None:
    from scripts.ltn_active_set_gate import check

    report = check()
    assert report["ok"], report
    assert report["policyCount"] == 11


def test_h7_geometry_audit_script() -> None:
    from scripts.ltn_geometry_audit import audit

    report = audit()
    assert report["ok"], report["failures"]


def test_c3_four_hero_in_active_set() -> None:
    from travelogue.layout_engine.mosaic.constants import MOSAIC_4_PATTERN_IDS
    from travelogue.layout_templates.registry import get_engine

    assert "screen-mosaic-4-hero-70-sidebar" in MOSAIC_4_PATTERN_IDS
    tpl = get_engine().get("screen-mosaic-4-hero-70-sidebar")
    assert tpl.status == "ga"
    assert int((tpl.rollout or {}).get("percent", 0)) == 100


def test_c3_pruned_flats_deprecated() -> None:
    from travelogue.layout_templates.registry import get_engine

    engine = get_engine()
    for tid in (
        "screen-portrait-6",
        "screen-portrait-9",
        "screen-landscape-9",
        "screen-portrait-grid-8",
    ):
        assert engine.get(tid).status == "deprecated", tid
    # 2026-07-31 · landscape-6 revived as experimental (not lte_policy / not MCS-6)
    assert engine.get("screen-landscape-6").status == "experimental"


def test_c1_no_aux3_in_planner_sizes() -> None:
    from travelogue.config import MosaicConfig, MosaicDensityBudgetConfig
    from travelogue.layout_engine.mosaic.runtime import planner_mosaic_window_sizes

    cfg = MosaicConfig(
        enabled=True,
        enabled_window_sizes=(4, 5, 6),
        density_budget=MosaicDensityBudgetConfig(enabled=True, window_order=(5, 4, 6)),
    )
    assert 3 not in planner_mosaic_window_sizes(cfg, density="balanced")
    assert 3 not in planner_mosaic_window_sizes(cfg, density="collage_first")


def test_h9_fixtures_exist() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[2] / "fixtures" / "ltn"
    assert (root / "trip.ltn_oracle_positive.json").is_file()
    assert (root / "trip.ltn_oracle_negative.json").is_file()
