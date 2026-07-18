"""TPC W2 · evaluator + mainSlotPolicy bridge (enabled=false default)."""

from __future__ import annotations

from dataclasses import replace
from typing import Any
from unittest.mock import patch

import pytest

from travelogue.config import get_config
from travelogue.config.mosaic import TemplateContractConfig
from travelogue.layout_engine.contract.evaluator import (
    _fallback_feasible,
    evaluate_contract_eligibility,
    patterns_for_contract_window,
    reset_evaluator_state_for_tests,
    resolve_eligibility_spec,
)
from travelogue.layout_engine.contract.shadow import reset_mix_index_cache_for_tests
from travelogue.layout_engine.mosaic.candidates import (
    generate_window_candidates_with_rejections,
)
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
)
from travelogue.layout_engine.mosaic.main_eligibility import screen_main_slot_eligible


def _asset(aid: str, *, w: int, h: int) -> dict[str, Any]:
    return {"id": aid, "width": w, "height": h}


@pytest.fixture(autouse=True)
def _reset_tpc_state() -> None:
    reset_evaluator_state_for_tests()
    reset_mix_index_cache_for_tests()
    yield
    reset_evaluator_state_for_tests()
    reset_mix_index_cache_for_tests()


def test_resolve_eligibility_prefers_eligibility_yaml() -> None:
    """AC-TPC-04 · hero YAML migrated to eligibility (no mainSlotPolicy key)."""
    source_spec, source = resolve_eligibility_spec("screen-mosaic-5-main-hero-plus-4")
    assert source == "eligibility"
    assert isinstance(source_spec, dict)
    assert source_spec.get("eligibleAspectKinds") == ["landscape"]


@pytest.mark.parametrize(
    "pattern_id,main_asset,expect_ok",
    [
        (
            PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
            _asset("p1", w=900, h=1600),  # portrait → blocked
            False,
        ),
        (
            PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
            _asset("l1", w=3000, h=1687),  # ~16:9 → ok
            True,
        ),
        (
            PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
            _asset("pano", w=5000, h=2000),  # panorama → blocked
            False,
        ),
        (
            PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
            _asset("std", w=3000, h=1687),
            True,
        ),
        (
            PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
            _asset("odd", w=1900, h=1000),  # off-ladder
            False,
        ),
    ],
)
def test_hero_equivalence_fixture_bridge_vs_legacy(
    pattern_id: str,
    main_asset: dict[str, Any],
    expect_ok: bool,
) -> None:
    """AC-TPC-04① · hero 等价 fixture：桥接结果逐例对照 screen_main_slot_eligible."""
    cfg = get_config().mosaic
    aid = str(main_asset["id"])
    screen = {
        "patternId": pattern_id,
        "slots": [{"role": "main", "assetId": aid}],
    }
    assets = {aid: main_asset}
    legacy_ok, legacy_reason = screen_main_slot_eligible(
        screen, assets, pattern_id=pattern_id, cfg=cfg
    )
    ok, reason, detail = evaluate_contract_eligibility(
        screen, assets, pattern_id=pattern_id, cfg=cfg
    )
    assert legacy_ok is expect_ok
    assert ok is legacy_ok
    if not expect_ok:
        assert reason == "contract:eligibility_main_ar"
        assert detail == legacy_reason


def test_bridge_deprecation_log_once(caplog) -> None:
    """Bridge path still logs once when only legacy mainSlotPolicy remains."""
    import logging

    from travelogue.layout_engine.contract import evaluator as ev

    cfg = get_config().mosaic
    screen = {
        "patternId": "synthetic-legacy-policy",
        "slots": [{"role": "main", "assetId": "l1"}],
    }
    assets = {"l1": _asset("l1", w=3000, h=1687)}
    legacy_only = {
        "mainSlotPolicy": {
            "eligibleAspectKinds": ["landscape"],
            "forbidKinds": ["portrait", "square", "panorama", "tall"],
        }
    }
    with patch.object(ev, "_template_constraints", return_value=legacy_only):
        with patch.object(
            ev,
            "screen_main_slot_eligible",
            return_value=(True, None),
        ):
            with caplog.at_level(
                logging.INFO, logger="travelogue.layout_engine.contract.evaluator"
            ):
                evaluate_contract_eligibility(
                    screen, assets, pattern_id="synthetic-legacy-policy", cfg=cfg
                )
                evaluate_contract_eligibility(
                    screen, assets, pattern_id="synthetic-legacy-policy", cfg=cfg
                )
    msgs = [r.message for r in caplog.records if "tpc.deprecation" in r.message]
    assert len(msgs) == 1


def test_enabled_false_unchanged_vs_size_path(lte_pattern_enabled) -> None:
    from tests._golden.helpers import build_mosaic_five_2p3l_window

    ids, aspects, assets_map = build_mosaic_five_2p3l_window()
    cfg = replace(
        get_config().mosaic,
        template_contract=TemplateContractConfig(enabled=False, shadow_log=False),
    )
    a = generate_window_candidates_with_rejections(ids, aspects, assets_map, cfg=cfg)
    b = generate_window_candidates_with_rejections(ids, aspects, assets_map, cfg=cfg)
    assert [c.pattern_id for c in a.candidates] == [c.pattern_id for c in b.candidates]


def test_enabled_true_uses_mix_index(lte_pattern_enabled) -> None:
    from tests._golden.helpers import build_mosaic_five_2p3l_window

    ids, aspects, assets_map = build_mosaic_five_2p3l_window()
    cfg = replace(
        get_config().mosaic,
        template_contract=TemplateContractConfig(enabled=True, shadow_log=False),
    )
    result = generate_window_candidates_with_rejections(
        ids, aspects, assets_map, cfg=cfg
    )
    patterns, source, mix, _sq, _inf = patterns_for_contract_window(ids, aspects)
    assert mix.startswith("L")
    assert source in ("exact", "fallback", "miss")
    assert (result.contract_shadow or {}).get("candidateSource") == source

    if source == "miss":
        assert result.candidates == []
        assert any(r.get("reason") == "contract:mix_miss" for r in result.rejected)
    else:
        allowed = {p.pattern_id for p in patterns}
        for c in result.candidates:
            assert c.pattern_id in allowed
            assert c.feature_summary.get("candidateSource") == source
        if source == "fallback" and result.candidates:
            assert any(
                c.feature_summary.get("contractMixFallback") for c in result.candidates
            )


def test_undeclared_eligibility_is_pass() -> None:
    cfg = get_config().mosaic
    ok, reason, _ = evaluate_contract_eligibility(
        {"slots": [{"role": "main", "assetId": "a"}]},
        {"a": {"id": "a", "width": 1000, "height": 1000}},
        pattern_id="screen-portrait-3",
        cfg=cfg,
    )
    # portrait-3 has no mainSlotPolicy / eligibility → BLK-11 pass
    assert ok is True
    assert reason is None


def test_fallback_feasibility_rejects_direction_conflict() -> None:
    """AC-TPC-03 · infeasible mix must not enter fallback (BLK-TPC-01)."""
    assert _fallback_feasible((4, 0, 0), (4, 0, 0)) == (True, False)
    assert _fallback_feasible((2, 2, 0), (4, 0, 0)) == (False, False)
    assert _fallback_feasible((3, 2, 0), (3, 2, 0)) == (True, False)


def test_fallback_square_relaxed_s_to_p() -> None:
    """BLK-TPC-01 · fallback S→P then S→L."""
    ok, relaxed = _fallback_feasible((2, 2, 0), (2, 1, 1))
    assert ok is True
    assert relaxed is True
    # Template S cannot be filled by P/L
    assert _fallback_feasible((0, 0, 2), (1, 1, 0)) == (False, False)


def test_ac_tpc_01_off_pick_best_stable(lte_pattern_enabled) -> None:
    """AC-TPC-01: enabled=false → deterministic pick matches across runs."""
    from tests._golden.helpers import build_mosaic_five_2p3l_window
    from travelogue.layout_engine.mosaic.compose import pick_best_window

    ids, aspects, assets_map = build_mosaic_five_2p3l_window()
    cfg = replace(
        get_config().mosaic,
        template_contract=TemplateContractConfig(enabled=False, shadow_log=True),
    )
    a = pick_best_window(
        ids, aspects, assets_map, cfg=cfg, window_size=5, trip_photo_total=40
    )
    b = pick_best_window(
        ids, aspects, assets_map, cfg=cfg, window_size=5, trip_photo_total=40
    )
    assert a.log.winner_pattern_id == b.log.winner_pattern_id
    assert a.log.planner_path == b.log.planner_path
    if a.screen and b.screen:
        assert [s.get("assetId") for s in a.screen.get("slots") or []] == [
            s.get("assetId") for s in b.screen.get("slots") or []
        ]


def test_asset_native_ar_shared_tool() -> None:
    """W2 step-0: shared geometry helper lives in layout_contract."""
    from travelogue.layout_contract.asset_geometry import asset_native_ar
    from travelogue.layout_engine.mosaic import main_eligibility as me

    asset = {"width": 1600, "height": 900}
    assert asset_native_ar(asset) == pytest.approx(1600 / 900)
    assert me.asset_native_ar(asset) == asset_native_ar(asset)
