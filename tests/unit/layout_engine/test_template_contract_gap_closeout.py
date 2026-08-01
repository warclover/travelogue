"""TPC gap closeout · AC-TPC-05/10/13 + YAML mainSlotPolicy clear."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from travelogue.config import get_config, load_config, reset_config_cache
from travelogue.config.mosaic import TemplateContractConfig, mosaic_from_dict
from travelogue.layout_engine.contract.geometry_features import compute_raw_geometry_features
from travelogue.layout_engine.mosaic.compose import pick_best_window

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[3]
TEMPLATES = ROOT / "travelogue" / "layout_templates" / "templates"


@pytest.fixture(autouse=True)
def _restore_config_cache() -> None:
    yield
    reset_config_cache()


def test_ac_tpc_10_raw_geometry_on_log(lte_pattern_enabled) -> None:
    from tests._golden.helpers import build_mosaic_five_2p3l_window

    ids, aspects, assets_map = build_mosaic_five_2p3l_window()
    cfg = replace(
        get_config().mosaic,
        template_contract=TemplateContractConfig(enabled=False, shadow_log=False),
    )
    result = pick_best_window(
        ids, aspects, assets_map, cfg=cfg, window_size=5, trip_photo_total=40
    )
    if not result.log.winner_pattern_id:
        pytest.skip("no mosaic winner on fixture")
    d = result.log.to_dict()
    # Record-only: either present numbers or omitted when no main / n<3 content
    feats = compute_raw_geometry_features(result.log.winner_pattern_id)
    for key in ("heroProminenceRatio", "heroCoverageRatio", "cellAreaCv"):
        if feats.get(key) is not None:
            assert key in d
            assert key not in (result.log.winner_penalties or {})


def test_ac_tpc_10_hero_70_coverage_in_band() -> None:
    feats = compute_raw_geometry_features("screen-mosaic-4-hero-70-sidebar")
    cov = feats.get("heroCoverageRatio")
    assert cov is not None
    assert 0.60 <= float(cov) <= 0.78


def test_ac_tpc_13_scoring_default_false() -> None:
    """CI-style: layout.scoring.enabled default false; template_contract root unique."""
    cfg = load_config()
    assert cfg.layout.scoring.enabled is False
    # Unique config root: mosaic.template_contract only (no alias softPenalty etc.)
    mosaic_from_dict({"template_contract": {"enabled": False}})
    with pytest.raises(ValueError, match="unknown keys"):
        mosaic_from_dict({"template_contract": {"enabled": False, "extraRoot": True}})


def test_ac_tpc_04_yaml_no_main_slot_policy_key() -> None:
    """AC-TPC-04② progress: active template YAML must not declare mainSlotPolicy."""
    offenders: list[str] = []
    for path in TEMPLATES.glob("*.yaml"):
        text = path.read_text(encoding="utf-8")
        # Structural key (not prose in usage strings)
        for i, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("mainSlotPolicy:"):
                offenders.append(f"{path.name}:{i}")
    assert offenders == [], f"mainSlotPolicy YAML keys remain: {offenders}"


def test_ac_tpc_05_self_heal_drop_respects_contract_reject(lte_pattern_enabled) -> None:
    """Contract rejects must not be re-emitted via self-heal drop path."""
    from travelogue.layout_engine.mosaic.candidates import (
        ScreenCandidate,
        WindowCandidateResult,
    )
    from travelogue.layout_engine.mosaic.selfheal import try_self_heal_pick

    cfg = replace(
        get_config().mosaic,
        template_contract=TemplateContractConfig(enabled=True, shadow_log=False),
        min_candidate_score=0.99,
    )
    empty = WindowCandidateResult(
        candidates=[],
        rejected=[
            {
                "templateId": "screen-mosaic-4-2l2p-weighted",
                "reason": "contract:infeasible_mix",
            }
        ],
        usage_rule_hits=[],
        contract_shadow=None,
    )
    with patch(
        "travelogue.layout_engine.mosaic.candidates.generate_window_candidates_with_rejections",
        return_value=empty,
    ):
        fake_screen = {
            "patternId": "x",
            "slots": [
                {"assetId": "a1"},
                {"assetId": "a2"},
                {"assetId": "a3"},
                {"assetId": "a4"},
            ],
        }
        cand = ScreenCandidate(
            pattern_id="x",
            ordered_asset_ids=["a1", "a2", "a3", "a4"],
            screen=fake_screen,
            feature_summary={},
            hard_valid=True,
        )
        scored = [(cand, 0.1, [], {})]
        aspects = {f"a{i}": "landscape" for i in range(1, 5)}
        assets = {aid: {"id": aid, "width": 900, "height": 600} for aid in aspects}
        healed = try_self_heal_pick(
            scored,
            asset_ids=list(aspects),
            aspects=aspects,
            assets_map=assets,
            cfg=cfg,
            layout_state=None,
            trip_photo_total=20,
            burst_seconds=12.0,
            min_score=0.99,
        )
    assert healed is None


def test_hero_70_css_token_present() -> None:
    """§5.1 · hero-70 binds CSS grid class (gutter via gap token in YAML)."""
    yaml_text = (
        TEMPLATES / "screen-mosaic-4-hero-70-sidebar.yaml"
    ).read_text(encoding="utf-8")
    assert "layout-screen__grid--mosaic-4-hero-70-sidebar" in yaml_text
    assert "gap:" in yaml_text
    css = ROOT / "templates" / "visual-journal" / "journal-screens.css"
    assert css.is_file()
    assert "mosaic-4-hero-70-sidebar" in css.read_text(encoding="utf-8")
