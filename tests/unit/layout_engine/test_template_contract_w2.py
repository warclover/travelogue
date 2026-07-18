"""TPC W2 · evaluator + mainSlotPolicy bridge (enabled=false default)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from travelogue.config import get_config
from travelogue.config.mosaic import TemplateContractConfig
from travelogue.layout_engine.contract.evaluator import (
    evaluate_contract_eligibility,
    patterns_for_contract_window,
    reset_evaluator_state_for_tests,
    resolve_eligibility_spec,
)
from travelogue.layout_engine.contract.shadow import reset_mix_index_cache_for_tests
from travelogue.layout_engine.mosaic.candidates import (
    generate_window_candidates_with_rejections,
)
from travelogue.layout_engine.mosaic.main_eligibility import screen_main_slot_eligible


@pytest.fixture(autouse=True)
def _reset_tpc_state() -> None:
    reset_evaluator_state_for_tests()
    reset_mix_index_cache_for_tests()
    yield
    reset_evaluator_state_for_tests()
    reset_mix_index_cache_for_tests()


def test_resolve_eligibility_bridges_main_slot_policy() -> None:
    source_spec, source = resolve_eligibility_spec("screen-mosaic-5-main-hero-plus-4")
    assert source == "mainSlotPolicy"
    assert isinstance(source_spec, dict)
    assert source_spec.get("eligibleAspectKinds") == ["landscape"]


def test_bridge_matches_screen_main_slot_eligible(lte_pattern_enabled) -> None:
    """AC-TPC-04①: bridge outcome ≡ screen_main_slot_eligible."""
    from travelogue.layout_engine.mosaic.constants import PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4

    cfg = get_config().mosaic
    # Portrait in main → ineligible
    screen = {
        "patternId": PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
        "slots": [
            {"role": "main", "assetId": "p1"},
            {"role": "tile", "assetId": "l1"},
        ],
    }
    assets = {
        "p1": {"id": "p1", "width": 900, "height": 1600},
        "l1": {"id": "l1", "width": 1600, "height": 900},
    }
    legacy_ok, legacy_reason = screen_main_slot_eligible(
        screen, assets, pattern_id=PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4, cfg=cfg
    )
    ok, reason, detail = evaluate_contract_eligibility(
        screen,
        assets,
        pattern_id=PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
        cfg=cfg,
    )
    assert ok is legacy_ok
    if not legacy_ok:
        assert reason == "contract:eligibility_main_ar"
        assert detail == legacy_reason


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
    patterns, source, mix = patterns_for_contract_window(ids, aspects)
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
