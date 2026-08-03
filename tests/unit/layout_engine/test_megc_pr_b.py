"""MEGC PR-B · equal-grid selection gate (AC-MEGC-04～08)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from travelogue.config.mosaic import mosaic_from_dict
from travelogue.layout_engine.mosaic.candidates import (
    generate_window_candidates_with_rejections,
)
from travelogue.layout_engine.mosaic.compose import pick_best_window
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_LANDSCAPE_4,
    PATTERN_PORTRAIT_2_LANDSCAPE_2,
)
from travelogue.layout_engine.mosaic.megc_gate import (
    MEGC_REJECT_REASON,
    build_megc_profile,
    evaluate_megc_gate,
)
from travelogue.layout_engine.mosaic.scorer import score_candidate
from travelogue.layout_templates.registry import reset_engine_cache_for_tests


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


def _megc_on(*, mode: str = "soft_penalty") -> object:
    return mosaic_from_dict(
        {
            "equal_grid_contract": {
                "enabled": True,
                "selection_gate": {
                    "enabled": True,
                    "mode": mode,
                    "allow_peaks": ["sixteen_nine"],
                    "allow_mixed_median_min": 1.70,
                    "score_mul": 0.62,
                },
            }
        }
    )


def _four_land_3x2() -> tuple[list[str], dict[str, str], dict[str, dict]]:
    ids = [f"a{i}" for i in range(4)]
    assets = {aid: _land(aid, w=3000, h=2000) for aid in ids}
    aspects = {aid: "landscape" for aid in ids}
    return ids, aspects, assets


def _four_land_16x9() -> tuple[list[str], dict[str, str], dict[str, dict]]:
    ids = [f"w{i}" for i in range(4)]
    assets = {aid: _land(aid, w=3840, h=2160) for aid in ids}
    aspects = {aid: "landscape" for aid in ids}
    return ids, aspects, assets


def _two_l_two_p_3x2() -> tuple[list[str], dict[str, str], dict[str, dict]]:
    assets = {
        "l0": _land("l0", w=3000, h=2000),
        "l1": _land("l1", w=3000, h=2000),
        "p0": _port("p0", w=2000, h=3000),
        "p1": _port("p1", w=2000, h=3000),
    }
    ids = list(assets.keys())
    aspects = {
        "l0": "landscape",
        "l1": "landscape",
        "p0": "portrait",
        "p1": "portrait",
    }
    return ids, aspects, assets


def _screen(pattern_id: str, asset_ids: list[str]) -> dict:
    return {
        "patternId": pattern_id,
        "slots": [
            {"slot": i, "assetId": aid, "role": "tile", "fit": "cover"}
            for i, aid in enumerate(asset_ids)
        ],
    }


def test_config_score_mul_default_and_penalty_fail_loud() -> None:
    cfg = mosaic_from_dict({})
    assert cfg.equal_grid_contract.enabled is True
    assert cfg.equal_grid_contract.selection_gate.score_mul == pytest.approx(0.62)
    assert cfg.equal_grid_contract.selection_gate.mode == "soft_penalty"
    with pytest.raises(ValueError, match="unknown keys"):
        mosaic_from_dict(
            {
                "equal_grid_contract": {
                    "enabled": True,
                    "selection_gate": {"penalty": 8.0},
                }
            }
        )


def test_ac04_soft_penalizes_landscape4_on_3x2_peak() -> None:
    ids, aspects, assets = _four_land_3x2()
    cfg_off = mosaic_from_dict({"equal_grid_contract": {"enabled": False}})
    cfg_on = _megc_on(mode="soft_penalty")
    screen = _screen(PATTERN_LANDSCAPE_4, ids)
    off = score_candidate(screen, aspects=aspects, assets_by_id=assets, cfg=cfg_off)
    on = score_candidate(screen, aspects=aspects, assets_by_id=assets, cfg=cfg_on)
    assert on.total < off.total
    assert "R_MEGC_PEAK_MISMATCH" in on.reason_codes
    decision = evaluate_megc_gate(PATTERN_LANDSCAPE_4, list(assets.values()), cfg_on)
    assert decision.outcome == "gate_penalize"
    assert decision.hard_reject is False
    assert decision.score_mul == pytest.approx(0.62)


def test_ac04_hard_rejects_landscape4_when_alternatives_exist() -> None:
    ids, aspects, assets = _four_land_3x2()
    cfg = _megc_on(mode="hard_reject")
    bundle = generate_window_candidates_with_rejections(
        ids, aspects, assets, cfg=cfg
    )
    megc_rejects = [
        r
        for r in bundle.rejected
        if r.get("reason") == MEGC_REJECT_REASON
        and r.get("templateId") == PATTERN_LANDSCAPE_4
    ]
    assert megc_rejects
    assert all(c.pattern_id != PATTERN_LANDSCAPE_4 for c in bundle.candidates) or any(
        (c.feature_summary or {}).get("megcGateFallback") for c in bundle.candidates
    )
    # Prefer: with alternatives, landscape-4 is absent (not fallback-only pool).
    non_fallback = [
        c
        for c in bundle.candidates
        if not (c.feature_summary or {}).get("megcGateFallback")
    ]
    if non_fallback:
        assert all(c.pattern_id != PATTERN_LANDSCAPE_4 for c in non_fallback)


def test_ac05_sixteen_nine_peak_allows_landscape4() -> None:
    ids, aspects, assets = _four_land_16x9()
    cfg = _megc_on(mode="soft_penalty")
    screen = _screen(PATTERN_LANDSCAPE_4, ids)
    scored = score_candidate(screen, aspects=aspects, assets_by_id=assets, cfg=cfg)
    assert "R_MEGC_PEAK_MISMATCH" not in scored.reason_codes
    decision = evaluate_megc_gate(PATTERN_LANDSCAPE_4, list(assets.values()), cfg)
    assert decision.outcome == "gate_allow"
    assert decision.land_peak == "sixteen_nine"
    pick = pick_best_window(
        ids,
        aspects=aspects,
        assets_map=assets,
        window_size=4,
        cfg=cfg,
    )
    raw = pick.log.to_dict()
    assert raw.get("megcEnabled") is True
    assert raw.get("megcOutcome") == "gate_allow"
    assert raw.get("megcLandPeak") == "sixteen_nine"


def test_ac06_mixed_orient_hard_rejects_on_non_cinema() -> None:
    ids, aspects, assets = _two_l_two_p_3x2()
    cfg = _megc_on(mode="soft_penalty")
    decision = evaluate_megc_gate(
        PATTERN_PORTRAIT_2_LANDSCAPE_2, list(assets.values()), cfg
    )
    assert decision.mixed_orient is True
    assert decision.hard_reject is True
    assert decision.outcome == "gate_reject"
    bundle = generate_window_candidates_with_rejections(
        ids, aspects, assets, cfg=cfg
    )
    assert any(
        r.get("reason") == MEGC_REJECT_REASON
        and r.get("templateId") == PATTERN_PORTRAIT_2_LANDSCAPE_2
        for r in bundle.rejected
    )


def test_ac07_log_fields_on_soft_penalize_path() -> None:
    ids, aspects, assets = _four_land_3x2()
    cfg = _megc_on(mode="soft_penalty")
    pick = pick_best_window(
        ids,
        aspects=aspects,
        assets_map=assets,
        window_size=4,
        cfg=cfg,
    )
    raw = pick.log.to_dict()
    assert "megcEnabled" in raw
    assert "megcOutcome" in raw
    assert "megcLandPeak" in raw
    assert "megcPatternId" in raw
    assert raw["megcEnabled"] is True
    assert raw["megcLandPeak"] == "three_two"
    if pick.log.winner_pattern_id == PATTERN_LANDSCAPE_4:
        assert raw["megcOutcome"] == "gate_penalize"
        assert "R_MEGC_PEAK_MISMATCH" in pick.log.winner_reason_codes


def test_ac07b_msa_off_still_computes_same_peak() -> None:
    ids, _aspects, assets = _four_land_3x2()
    cfg = mosaic_from_dict(
        {
            "slot_adaptation": {"enabled": False},
            "equal_grid_contract": {
                "enabled": True,
                "selection_gate": {"enabled": True, "score_mul": 0.62},
            },
        }
    )
    assert cfg.slot_adaptation.enabled is False
    prof = build_megc_profile(list(assets.values()), cfg=cfg)
    assert prof.land_peak == "three_two"
    decision = evaluate_megc_gate(PATTERN_LANDSCAPE_4, list(assets.values()), cfg)
    assert decision.land_peak == "three_two"
    assert decision.outcome == "gate_penalize"


def test_ac08_parent_off_baseline_no_mul() -> None:
    ids, aspects, assets = _four_land_3x2()
    cfg = mosaic_from_dict({"equal_grid_contract": {"enabled": False}})
    screen = _screen(PATTERN_LANDSCAPE_4, ids)
    scored = score_candidate(screen, aspects=aspects, assets_by_id=assets, cfg=cfg)
    assert "R_MEGC_PEAK_MISMATCH" not in scored.reason_codes
    pick = pick_best_window(
        ids,
        aspects=aspects,
        assets_map=assets,
        window_size=4,
        cfg=cfg,
    )
    raw = pick.log.to_dict()
    assert raw.get("megcEnabled") is False
    assert raw.get("megcOutcome") == "skipped"
    bundle = generate_window_candidates_with_rejections(
        ids, aspects, assets, cfg=cfg
    )
    assert not any(r.get("reason") == MEGC_REJECT_REASON for r in bundle.rejected)


def test_sup03_hard_fallback_flags_when_pool_empty() -> None:
    """When MEGC hard-reject empties the pool, soft-reemit with megcGateFallback."""
    from travelogue.layout_engine.mosaic.pattern_catalog import AspectProfile, MosaicPattern

    ids, aspects, assets = _four_land_3x2()
    cfg = _megc_on(mode="hard_reject")
    only_l4 = {
        PATTERN_LANDSCAPE_4: MosaicPattern(
            pattern_id=PATTERN_LANDSCAPE_4,
            slot_count=4,
            grid_class="layout-screen__grid--2x2",
            roles=("tile", "tile", "tile", "tile"),
            accepts=AspectProfile(),
        )
    }
    bundle = generate_window_candidates_with_rejections(
        ids, aspects, assets, cfg=cfg, registry=only_l4
    )
    assert bundle.candidates, "SUP-03 must not leave an empty pool"
    assert any(
        (c.feature_summary or {}).get("megcGateFallback") for c in bundle.candidates
    )
    assert any(r.get("reason") == MEGC_REJECT_REASON for r in bundle.rejected)


def test_equal_grid_contract_parses_camel_case() -> None:
    cfg = mosaic_from_dict(
        {
            "equalGridContract": {
                "enabled": True,
                "selectionGate": {
                    "enabled": True,
                    "scoreMul": 0.55,
                    "allowMixedMedianMin": 1.65,
                    "allowPeaks": ["sixteen_nine"],
                },
            }
        }
    )
    assert cfg.equal_grid_contract.enabled is True
    assert cfg.equal_grid_contract.selection_gate.score_mul == pytest.approx(0.55)
    assert cfg.equal_grid_contract.selection_gate.allow_mixed_median_min == pytest.approx(
        1.65
    )
