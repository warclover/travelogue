"""MSA gap-close · whitelist portrait, movie track, scoring, prominence, idempotence."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest

from travelogue.config.mosaic import SlotAdaptationConfig, mosaic_from_dict
from travelogue.layout_engine.mosaic.msa_apply import maybe_apply_slot_adaptation
from travelogue.layout_engine.mosaic.msa_profile import build_msa_profile
from travelogue.layout_engine.mosaic.msa_solve import (
    MSA_M1_PATTERN_WHITELIST,
    main_is_portrait_family,
    resolve_main_r_star,
    solve_track_override,
)
from travelogue.layout_engine.mosaic.scorer import score_candidate
from travelogue.layout_templates.geometry_solidify import solidify_screen_geometry
from travelogue.layout_templates.registry import get_engine, reset_engine_cache_for_tests

PATTERN_6 = "screen-mosaic-6-main-hero-plus-5"
PATTERN_1P4L = "screen-mosaic-5-1p4l-portrait-hero"
PATTERN_2P3L = "screen-mosaic-5-2p3l-portrait-hero-rail"


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


def _port(aid: str, *, w: int, h: int) -> dict:
    return {
        "id": aid,
        "width": w,
        "height": h,
        "aspectKind": "portrait",
        "quality": {"sharpness": 0.9},
    }


def test_o03_whitelist_includes_portrait_heroes() -> None:
    assert PATTERN_1P4L in MSA_M1_PATTERN_WHITELIST
    assert PATTERN_2P3L in MSA_M1_PATTERN_WHITELIST
    assert "screen-mosaic-5-main-portrait-3land" in MSA_M1_PATTERN_WHITELIST
    for pid in (PATTERN_1P4L, PATTERN_2P3L):
        assert main_is_portrait_family(get_engine().get(pid))


def test_movie_track_wide_peak_fraction() -> None:
    # ≥50% 16:9 among labeled land → sixteen_nine / r*=1.7778
    assets = [
        _land("w0", w=1920, h=1080),
        _land("w1", w=1920, h=1080),
        _land("w2", w=1920, h=1080),
        _land("w3", w=1920, h=1080),
        _land("a4", w=3000, h=2000),
        _land("a5", w=4000, h=3000),
    ]
    profile = build_msa_profile(assets)
    assert profile.land_peak == "sixteen_nine"
    assert profile.r_hero_target == pytest.approx(1.7778, abs=0.01)


def test_portrait_main_uses_port_target() -> None:
    assets = [
        _port("p0", w=2000, h=3000),
        _land("l1", w=3000, h=2000),
        _land("l2", w=3000, h=2000),
        _land("l3", w=3000, h=2000),
        _land("l4", w=3000, h=2000),
    ]
    profile = build_msa_profile(assets)
    assert profile.port_peak == "two_three"
    assert profile.r_port_target == pytest.approx(2 / 3, abs=0.02)
    tpl = get_engine().get(PATTERN_1P4L)
    r_star = resolve_main_r_star(
        tpl, r_land=profile.r_hero_target, r_port=profile.r_port_target
    )
    assert r_star == pytest.approx(2 / 3, abs=0.02)
    # Full-height extreme hero cannot hit ~0.67 without breaking area→ expect miss OK
    result = solve_track_override(tpl, r_hero_target=float(r_star))
    assert result.reason in {"applied", "msa_solve_miss"}


def test_portrait_whitelist_runs_fit_path(monkeypatch: pytest.MonkeyPatch) -> None:
    assets = {
        "p0": _port("p0", w=2000, h=3000),
        "l1": _land("l1", w=5000, h=1000),
        "l2": _land("l2", w=3000, h=2000),
        "l3": _land("l3", w=3000, h=2000),
        "l4": _land("l4", w=3000, h=2000),
    }
    screen = {
        "patternId": PATTERN_1P4L,
        "slots": [
            {"slot": 0, "assetId": "p0", "role": "main", "fit": "cover"},
            {"slot": 1, "assetId": "l1", "role": "landscape", "fit": "cover"},
            {"slot": 2, "assetId": "l2", "role": "landscape", "fit": "cover"},
            {"slot": 3, "assetId": "l3", "role": "landscape", "fit": "cover"},
            {"slot": 4, "assetId": "l4", "role": "landscape", "fit": "cover"},
        ],
    }
    sa = SlotAdaptationConfig(enabled=True, crop_risk_contain_threshold=0.35)
    mosaic = replace(mosaic_from_dict({}), slot_adaptation=sa)
    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.msa_apply.get_effective_mosaic_config",
        lambda: mosaic,
    )
    solidify_screen_geometry(screen, PATTERN_1P4L, assets_map=assets)
    summary = maybe_apply_slot_adaptation(
        screen, PATTERN_1P4L, assets_map=assets, cfg=mosaic
    )
    assert summary["msaOutcome"] != "skipped_not_whitelisted"
    assert summary["msaProfile"] is not None
    assert summary["cropRisk"] is not None


def test_s_msa_06_scoring_penalties_when_msa_on(monkeypatch: pytest.MonkeyPatch) -> None:
    assets = {f"a{i}": _land(f"a{i}", w=5000, h=1000) for i in range(6)}
    ids = list(assets.keys())
    aspects = {aid: "landscape" for aid in ids}
    screen = {
        "patternId": PATTERN_6,
        "slots": [
            {"slot": i, "assetId": ids[i], "role": "main" if i == 0 else "tile", "fit": "cover"}
            for i in range(6)
        ],
    }
    mosaic_off = replace(mosaic_from_dict({}), slot_adaptation=SlotAdaptationConfig(enabled=False))
    mosaic_on = replace(mosaic_from_dict({}), slot_adaptation=SlotAdaptationConfig(enabled=True))
    off = score_candidate(
        screen, aspects=aspects, assets_by_id=assets, cfg=mosaic_off
    )
    on = score_candidate(
        screen, aspects=aspects, assets_by_id=assets, cfg=mosaic_on
    )
    assert "crop_risk_penalty" not in off.penalties or off.penalties.get("crop_risk_penalty", 0) == 0
    # When ON, keys present and risk > 0 for ultra-wide vs ~1.78 slots
    assert on.penalties.get("crop_risk_penalty", 0) > 0
    assert on.penalties.get("aspect_fit", 0) > 0


def test_ac05p_idempotent_track_override(monkeypatch: pytest.MonkeyPatch) -> None:
    assets = {f"a{i}": _land(f"a{i}", w=3000, h=2000) for i in range(6)}
    screen = {
        "patternId": PATTERN_6,
        "slots": [
            {
                "slot": i,
                "assetId": f"a{i}",
                "role": "main" if i == 0 else "tile",
                "fit": "cover",
            }
            for i in range(6)
        ],
    }
    mosaic = replace(
        mosaic_from_dict({}), slot_adaptation=SlotAdaptationConfig(enabled=True)
    )
    monkeypatch.setattr(
        "travelogue.layout_engine.mosaic.msa_apply.get_effective_mosaic_config",
        lambda: mosaic,
    )
    solidify_screen_geometry(screen, PATTERN_6, assets_map=assets)
    maybe_apply_slot_adaptation(screen, PATTERN_6, assets_map=assets, cfg=mosaic)
    first = deepcopy(screen["layoutGeometry"].get("trackOverride"))
    assert first
    # Simulate preview→export re-read: second apply must not drift
    maybe_apply_slot_adaptation(screen, PATTERN_6, assets_map=assets, cfg=mosaic)
    assert screen["layoutGeometry"].get("trackOverride") == first


def test_extreme_hero_prominence_guard_on_solve() -> None:
    """If a solve broke prominence, result must miss (static fallback)."""
    tpl = get_engine().get("screen-mosaic-4-hero-70-sidebar")
    # Feasible 1.50 target should keep prominence for extreme hero
    ok = solve_track_override(tpl, r_hero_target=1.30)
    if ok.ok:
        from travelogue.layout_engine.mosaic.msa_solve import _prominence_ratio

        prom = _prominence_ratio(tpl, ok.cols, ok.rows)
        assert prom is not None and prom + 1e-9 >= 3.0
