"""P17 golden metrics + explain + capability_flags."""

from __future__ import annotations

from dataclasses import replace

from travelogue.config import get_config
from travelogue.layout_engine.adapter import strategy_trace_meta
from travelogue.layout_engine.capabilities import capability_flags_snapshot
from travelogue.layout_engine.decision_log import project_mosaic_window
from travelogue.layout_engine.explain import build_explain
from travelogue.layout_engine.metrics import (
    chapter_hero_first_screen_rate,
    evaluate_ac_delta,
    mixed_face_intact_rate,
)
from travelogue.layout_engine.mosaic.log import MosaicWindowLog


def test_build_explain_contributions() -> None:
    explain = build_explain(
        {"salient_crop": 0.4, "face_crop": 0.2},
        penalty_weights={"salient_crop": 0.28, "face_crop": 0.15},
    )
    assert explain["topFactors"]
    assert explain["contributions"]
    assert explain["penalties"]


def test_project_mosaic_window_explain_and_fallback() -> None:
    raw = MosaicWindowLog(
        segment_id="ch-01",
        winner_pattern_id="screen-mosaic-5-main-hero-plus-4",
        winner_score=0.82,
        winner_penalties={"salient_crop": 0.3},
        scoring_penalty_weights={"salient_crop": 0.28},
        slot_assignment_fallback="solver_unavailable",
    ).to_dict()
    event = project_mosaic_window(raw, chapter_id="ch-01")
    assert event["explain"]["contributions"]
    assert event["meta"]["slotAssignmentFallback"] == "solver_unavailable"
    assert event["meta"]["fallbackReason"] == "solver_unavailable"


def test_capability_flags_snapshot() -> None:
    cfg = get_config(reload=True)
    se = replace(
        cfg.layout.strategy_engine,
        enabled=True,
        capabilities=replace(
            cfg.layout.strategy_engine.capabilities,
            saliency_scoring=True,
            beat_profile="classic_magazine",
        ),
    )
    cfg_on = replace(cfg, layout=replace(cfg.layout, strategy_engine=se))
    flags = capability_flags_snapshot(cfg_on)
    assert flags["saliencyScoring"] is True
    assert flags["beatProfile"] == "classic_magazine"
    meta = strategy_trace_meta(cfg_on)
    assert meta["capabilityFlags"]["saliencyScoring"] is True


def test_mixed_face_intact_rate_fixture_shape() -> None:
    chapters = [
        {
            "screens": [
                {
                    "patternId": "screen-portrait-1-landscape-2",
                    "slots": [
                        {
                            "assetId": "a1",
                            "fit": "cover",
                            "displayAspect": 0.75,
                        }
                    ],
                }
            ]
        }
    ]
    assets = {
        "a1": {
            "id": "a1",
            "width": 3000,
            "height": 4000,
            "tags": ["person"],
            "focalPoint": {"x": 0.5, "y": 0.45},
        }
    }
    rate = mixed_face_intact_rate(chapters, assets)
    assert rate is not None
    assert 0.0 <= rate <= 1.0


def test_evaluate_ac_delta_thresholds() -> None:
    base = {
        "layout.mixed.face_intact_rate": 0.50,
        "layout.mixed.salient_retention_p50": 0.60,
        "layout.beat.hero_first_screen_rate": 0.20,
        "layout.tone.adjacent_delta_e_p50": 20.0,
        "layout.chapter.pattern_diversity_p50": 3.0,
    }
    cand = {
        "layout.mixed.face_intact_rate": 0.56,
        "layout.mixed.salient_retention_p50": 0.66,
        "layout.beat.hero_first_screen_rate": 0.30,
        "layout.tone.adjacent_delta_e_p50": 17.0,
        "layout.chapter.pattern_diversity_p50": 3.0,
    }
    ac = evaluate_ac_delta(base, cand)
    assert ac["AC-P17-16"]["passed"] is True
    assert ac["AC-P17-17"]["passed"] is True
    assert ac["AC-P17-18"]["passed"] is True
    assert ac["AC-P17-19"]["passed"] is True
    assert ac["AC-P17-16"]["measurable"] is True


def test_evaluate_ac_delta_unmeasurable_skipped() -> None:
    base = {
        "layout.mixed.face_intact_rate": None,
        "layout.beat.hero_first_screen_rate": 0.5,
        "layout.tone.adjacent_delta_e_p50": None,
        "layout.chapter.pattern_diversity_p50": 3.0,
    }
    cand = dict(base)
    ac = evaluate_ac_delta(base, cand)
    assert ac["AC-P17-16"]["passed"] is None
    assert ac["AC-P17-16"]["measurable"] is False
    assert ac["AC-P17-17"]["passed"] is False


def test_chapter_hero_first_screen_rate() -> None:
    chapters = [
        {"screens": [{"patternId": "screen-portrait-1", "slots": [{"assetId": "a"}]}]},
        {"screens": [{"patternId": "screen-landscape-3", "slots": [{}, {}, {}]}]},
    ]
    rate = chapter_hero_first_screen_rate(chapters)
    assert rate == 0.5
