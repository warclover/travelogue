"""MSA PR-A · profile + whitelist solve + persist + parent-off (AC-MSA-01～05)."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest

from travelogue.config import get_config
from travelogue.config.mosaic import SlotAdaptationConfig, mosaic_from_dict
from travelogue.layout_engine.mosaic.builders import _finalize_mosaic_screen
from travelogue.layout_engine.mosaic.msa_apply import maybe_apply_slot_adaptation
from travelogue.layout_engine.mosaic.msa_profile import build_msa_profile
from travelogue.layout_engine.mosaic.msa_solve import (
    list_stage_variants,
    solve_all_variants,
    solve_track_override,
)
from travelogue.layout_templates.geometry import slot_display_aspect
from travelogue.layout_templates.geometry_solidify import solidify_screen_geometry
from travelogue.layout_templates.registry import get_engine, reset_engine_cache_for_tests

PATTERN_6 = "screen-mosaic-6-main-hero-plus-5"
PATTERN_4_SIDEBAR = "screen-mosaic-4-hero-70-sidebar"


@pytest.fixture(autouse=True)
def _reset_engine() -> None:
    reset_engine_cache_for_tests()
    yield
    reset_engine_cache_for_tests()


def _land(aid: str, *, w: int, h: int) -> dict:
    return {
        "id": aid,
        "width": w,
        "height": h,
        "aspectKind": "landscape",
        "quality": {"sharpness": 0.9},
    }


def _six_screen(assets: dict[str, dict]) -> dict:
    ids = list(assets.keys())
    return {
        "patternId": PATTERN_6,
        "slots": [
            {"slot": i, "assetId": ids[i], "role": "main" if i == 0 else "tile", "fit": "cover"}
            for i in range(6)
        ],
    }


def test_ac01_parent_off_zero_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    assets = {f"a{i}": _land(f"a{i}", w=3000, h=2000) for i in range(6)}
    screen = _six_screen(assets)
    cfg = replace(get_config(), mosaic=mosaic_from_dict({"slot_adaptation": {"enabled": False}}))
    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.msa_apply.get_effective_mosaic_config",
        lambda: cfg.mosaic,
    )
    solidify_screen_geometry(screen, PATTERN_6, assets_map=assets)
    before = deepcopy(screen)
    summary = maybe_apply_slot_adaptation(screen, PATTERN_6, assets_map=assets, cfg=cfg.mosaic)
    assert summary["msaOutcome"] == "skipped_parent_off"
    assert "trackOverride" not in (screen.get("layoutGeometry") or {})
    assert screen["layoutGeometry"]["cols"] == before["layoutGeometry"]["cols"]
    assert screen["layoutGeometry"]["rows"] == before["layoutGeometry"]["rows"]
    for a, b in zip(screen["slots"], before["slots"]):
        assert a.get("displayAspect") == b.get("displayAspect")
        assert a.get("fit") == b.get("fit")


def test_ac02_dslr_32_main_hits_150() -> None:
    assets = [_land(f"a{i}", w=3000, h=2000) for i in range(6)]
    profile = build_msa_profile(assets)
    assert profile.land_peak == "three_two"
    assert profile.r_hero_target == pytest.approx(1.50, abs=0.01)
    tpl = get_engine().get(PATTERN_6)
    result = solve_track_override(tpl, r_hero_target=1.50)
    assert result.ok, result
    assert result.main_display_aspect is not None
    assert abs(result.main_display_aspect - 1.50) <= 0.08
    assert result.main_area is not None and result.main_area >= 0.35


def test_ac03_phone_43_main_hits_133() -> None:
    assets = [_land(f"a{i}", w=4000, h=3000) for i in range(6)]
    profile = build_msa_profile(assets)
    assert profile.land_peak == "four_three"
    assert profile.r_hero_target == pytest.approx(1.3333, abs=0.01)
    tpl = get_engine().get(PATTERN_6)
    result = solve_track_override(tpl, r_hero_target=1.3333)
    assert result.ok, result
    assert result.main_display_aspect is not None
    assert abs(result.main_display_aspect - 1.3333) <= 0.08


def test_ac04_mixed_peak_clamp() -> None:
    # 3×3:2 + 3×4:3 → mixed; median in clamp
    assets = [
        _land("a0", w=3000, h=2000),
        _land("a1", w=3000, h=2000),
        _land("a2", w=3000, h=2000),
        _land("a3", w=4000, h=3000),
        _land("a4", w=4000, h=3000),
        _land("a5", w=4000, h=3000),
    ]
    profile = build_msa_profile(assets)
    assert profile.land_peak == "mixed"
    assert profile.r_hero_target is not None
    assert 1.30 <= profile.r_hero_target <= 1.60
    tpl = get_engine().get(PATTERN_6)
    result = solve_track_override(tpl, r_hero_target=float(profile.r_hero_target))
    assert result.ok, result
    # Single override (not per-slot extremes)
    assert len(result.cols) == 3 and len(result.rows) == 3


def test_ac05_solve_miss_keeps_static(monkeypatch: pytest.MonkeyPatch) -> None:
    assets = {f"a{i}": _land(f"a{i}", w=3000, h=2000) for i in range(6)}
    screen = _six_screen(assets)
    sa = SlotAdaptationConfig(enabled=True)
    # Impossible target under area floor → miss
    cfg = replace(get_config(), mosaic=replace(mosaic_from_dict({}), slot_adaptation=sa))
    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.msa_apply.get_effective_mosaic_config",
        lambda: cfg.mosaic,
    )
    solidify_screen_geometry(screen, PATTERN_6, assets_map=assets)
    static_cols = list(screen["layoutGeometry"]["cols"])
    # Force miss by patching profile to an absurd r*
    from travelogue.layout_engine.mosaic import msa_apply as msa_apply_mod
    from travelogue.layout_engine.mosaic.msa_profile import MsaProfile

    monkeypatch.setattr(
        msa_apply_mod,
        "build_msa_profile",
        lambda assets_in, *, cfg=None: MsaProfile(
            n_land=6,
            n_port=0,
            n_other=0,
            land_peak="three_two",
            port_peak="none",
            land_median_r=1.5,
            r_hero_target=0.2,
        ),
    )
    summary = maybe_apply_slot_adaptation(screen, PATTERN_6, assets_map=assets, cfg=cfg.mosaic)
    assert summary["msaOutcome"] == "msa_solve_miss"
    assert screen["layoutGeometry"].get("trackOverride") is None
    assert screen["layoutGeometry"]["cols"] == static_cols
    assert len(screen["slots"]) == 6


def test_ac05v_variants_each_solved() -> None:
    tpl = get_engine().get(PATTERN_4_SIDEBAR)
    variants = list_stage_variants(tpl)
    assert any(v["layout"] == "web" for v in variants)
    assert any(v["layout"] == "mobile" for v in variants)
    results = solve_all_variants(tpl, r_hero_target=1.50)
    assert "web" in results and "mobile" in results
    # Each variant has independent outcome (ok or miss) — never silently skip mobile
    for layout, res in results.items():
        assert res.reason in {"applied", "msa_solve_miss", "no_target", "skipped_not_whitelisted"}
        assert len(res.cols) >= 1 and len(res.rows) >= 1


def test_ac05p_persist_track_override_and_fits(monkeypatch: pytest.MonkeyPatch) -> None:
    assets = {f"a{i}": _land(f"a{i}", w=3000, h=2000) for i in range(6)}
    screen = _six_screen(assets)
    sa = SlotAdaptationConfig(enabled=True)
    cfg = replace(get_config(), mosaic=replace(mosaic_from_dict({}), slot_adaptation=sa))
    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.msa_apply.get_effective_mosaic_config",
        lambda: cfg.mosaic,
    )
    _finalize_mosaic_screen(screen, PATTERN_6, assets_map=assets)
    geo = screen["layoutGeometry"]
    assert geo.get("trackOverride")
    assert geo["trackOverride"]["cols"] == geo["cols"]
    assert geo["trackOverride"]["rows"] == geo["rows"]
    assert all(s.get("fit") for s in screen["slots"])
    main = next(s for s in screen["slots"] if s.get("role") == "main" or s.get("slot") == 0)
    assert abs(float(main["displayAspect"]) - 1.50) <= 0.08
    # Idempotent second apply
    again = deepcopy(screen)
    maybe_apply_slot_adaptation(again, PATTERN_6, assets_map=assets, cfg=cfg.mosaic)
    assert again["layoutGeometry"]["trackOverride"] == geo["trackOverride"]


def test_solve_preserves_topology_rects() -> None:
    tpl = get_engine().get(PATTERN_6)
    before = [tuple(s.rect) for s in tpl.slots]
    result = solve_track_override(tpl, r_hero_target=1.50)
    assert result.ok
    after = [tuple(s.rect) for s in tpl.slots]
    assert before == after
    # Recomputed AR matches result
    from travelogue.layout_templates.models import TemplateStage

    stage = TemplateStage(
        aspect=tpl.stage.aspect,
        cols=tuple(result.cols),
        rows=tuple(result.rows),
    )
    main = next(s for s in tpl.slots if s.role == "main")
    assert abs(slot_display_aspect(main.rect, stage) - 1.50) <= 0.08
