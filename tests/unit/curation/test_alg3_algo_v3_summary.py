"""ALG-V3 W0 · algoV3 summary + buildScreenCalls counter."""

from __future__ import annotations

from travelogue.config import AppConfig
from travelogue.config.misc import LlmConfig
from travelogue.curation.algo_v3_summary import attach_algo_v3_summary, build_algo_v3_summary
from travelogue.layout_engine.mosaic.builders import (
    get_build_screen_calls,
    reset_build_screen_calls,
)


def test_build_screen_calls_counter_increments() -> None:
    reset_build_screen_calls()
    assert get_build_screen_calls() == 0
    from travelogue.layout_engine.mosaic.builders import _note_build_screen_call

    _note_build_screen_call()
    _note_build_screen_call()
    assert get_build_screen_calls() == 2
    reset_build_screen_calls()
    assert get_build_screen_calls() == 0


def test_algo_v3_summary_schema_keys(monkeypatch) -> None:
    monkeypatch.setattr(
        "travelogue.llm.ready.probe_llm_ready",
        lambda *, cfg=None: False,
    )
    trip = {
        "assets": [
            {"id": "a1", "sceneClusterId": 0},
            {"id": "a2", "sceneClusterId": -1},
        ],
        "curation": {
            "mosaicDecisionLog": [
                {
                    "isWinnerPlan": True,
                    "rejectedTemplates": [
                        {"templateId": "screen-x", "reason": "atom_boundary"},
                        {"templateId": "screen-y", "reason": "shot_group_cross"},
                        {"templateId": "screen-z", "reason": "near_scene_clone"},
                    ],
                }
            ]
        },
    }
    cfg = AppConfig(llm=LlmConfig(capability="auto"))
    summary = build_algo_v3_summary(trip, cfg=cfg, build_screen_calls=7)
    for key in (
        "visionEffective",
        "ssgMode",
        "clusterNoiseRatio",
        "cloneGateEffective",
        "layoutScoringEffective",
        "wallClockHardLimit",
        "llm",
        "degradeReasons",
        "rejectFunnelTop",
        "buildScreenCalls",
    ):
        assert key in summary
    assert summary["buildScreenCalls"] == 7
    assert summary["clusterNoiseRatio"] == 0.5
    assert summary["ssgMode"] == "off"
    assert summary["rejectFunnelTop"]["atom_boundary"] == 1
    assert summary["rejectFunnelTop"]["shot_group"] == 1
    assert summary["rejectFunnelTop"]["near_scene_clone"] == 1
    assert summary["llm"]["ready"] is False
    assert summary["llm"]["usedOnImport"] is False
    assert summary["degradeReasons"] == []


def test_attach_algo_v3_writes_curation(monkeypatch) -> None:
    monkeypatch.setattr(
        "travelogue.llm.ready.probe_llm_ready",
        lambda *, cfg=None: False,
    )
    trip: dict = {"assets": [], "curation": {}}
    out = attach_algo_v3_summary(trip, cfg=AppConfig())
    assert trip["curation"]["algoV3"] is out
    assert "buildScreenCalls" in out


def test_ac30_no_key_vs_ssg_empty_values_diverge(monkeypatch) -> None:
    """AC-30: 无 Key / SSG empty 两场景键齐全且值分化（禁「键存在即过」X07）。"""
    monkeypatch.setattr(
        "travelogue.llm.ready.probe_llm_ready",
        lambda *, cfg=None: False,
    )

    no_key_trip = {"assets": [], "curation": {}}
    no_key = build_algo_v3_summary(
        no_key_trip,
        cfg=AppConfig(llm=LlmConfig(capability="true")),
        build_screen_calls=0,
    )

    ssg_empty_trip = {
        "assets": [{"id": "a1"}],
        "curation": {
            # shotGrouping 块存在但无可用 groups / look → ssgMode=empty
            "shotGrouping": {
                "groups": [],
                "stats": {"lookGroupCount": 0},
                "telemetry": {},
            }
        },
    }
    ssg_empty = build_algo_v3_summary(
        ssg_empty_trip,
        cfg=AppConfig(llm=LlmConfig(capability="auto")),
        build_screen_calls=3,
    )

    required = (
        "visionEffective",
        "ssgMode",
        "clusterNoiseRatio",
        "cloneGateEffective",
        "layoutScoringEffective",
        "wallClockHardLimit",
        "llm",
        "degradeReasons",
        "rejectFunnelTop",
        "buildScreenCalls",
    )
    for key in required:
        assert key in no_key
        assert key in ssg_empty

    # 无 Key + capability=true → llm_no_key；auto 无凭证不写 degrade
    assert "llm_no_key" in no_key["degradeReasons"]
    assert no_key["llm"]["ready"] is False
    assert no_key["llm"]["capability"] == "true"
    assert ssg_empty["degradeReasons"] == []
    assert ssg_empty["llm"]["capability"] == "auto"

    # SSG empty vs 无 shotGrouping → ssgMode 分化
    assert no_key["ssgMode"] == "off"
    assert ssg_empty["ssgMode"] == "empty"
    assert no_key["buildScreenCalls"] != ssg_empty["buildScreenCalls"]
