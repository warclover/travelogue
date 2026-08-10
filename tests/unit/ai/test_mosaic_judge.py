"""ACP W3 · Mosaic Judge skeleton (D-ACP-15 / AC-ACP-08 / AC-ACP-17 prep)."""

from __future__ import annotations

import json

from travelogue.ai.agents.mosaic_judge import (
    is_tie_window,
    review_mosaic_tie,
)
from travelogue.ai.budget import clear_budgets
from travelogue.ai.telemetry import clear_ops_summary
from travelogue.config.ai_capability import AiCapabilityConfig, MosaicJudgeConfig
from travelogue.config.app import AppConfig
from travelogue.config.misc import LlmConfig
from travelogue.config.runtime import app_config_scope
from travelogue.config.studio import StudioConfig


def setup_function() -> None:
    clear_budgets()
    clear_ops_summary()


def test_is_tie_window() -> None:
    assert is_tie_window([1.0, 0.98], epsilon=0.03) is True
    assert is_tie_window([1.0, 0.9], epsilon=0.03) is False
    assert is_tie_window([1.0], epsilon=0.03) is False


def test_judge_disabled_keeps_first_pass() -> None:
    trip: dict = {"tripId": "t-mj", "curation": {}}
    with app_config_scope(AppConfig()):
        entry = review_mosaic_tie(
            window_id="w1",
            candidates=[{"id": "c1", "score": 1.0}, {"id": "c2", "score": 0.99}],
            first_pass_candidate_id="c1",
            trip=trip,
        )
    assert entry["chosenCandidateId"] == "c1"
    assert entry["overriddenFromFirstPass"] is False
    assert entry["source"] == "fallback"
    assert entry["reason"] == "mosaic_judge_disabled"


def test_judge_rejects_invented_id(monkeypatch) -> None:
    cfg = AppConfig(
        ai_capability=AiCapabilityConfig(
            enabled=False,
            mosaic_judge=MosaicJudgeConfig(enabled=True, tie_epsilon=0.05),
        ),
        studio=StudioConfig(ai_surface_enabled=True),
        llm=LlmConfig(provider="deepseek"),
    )
    monkeypatch.setattr(
        "travelogue.ai.agents.mosaic_judge.resolve_llm_may_call",
        lambda cfg=None: True,
    )
    monkeypatch.setattr(
        "travelogue.ai.agents.mosaic_judge.probe_llm_ready",
        lambda cfg=None: True,
    )

    def fake_chat(_messages):
        return json.dumps({"chosenCandidateId": "invented-never"}, ensure_ascii=False)

    trip: dict = {"tripId": "t-mj2", "curation": {}}
    with app_config_scope(cfg):
        entry = review_mosaic_tie(
            window_id="w2",
            candidates=[{"id": "c1"}, {"id": "c2"}],
            first_pass_candidate_id="c1",
            trip=trip,
            chat_fn=fake_chat,
        )
    assert entry["chosenCandidateId"] == "c1"
    assert entry["overriddenFromFirstPass"] is False
    assert entry["reason"] == "chosen_not_in_candidates"
    assert trip["curation"]["mosaicJudgeLog"][-1]["chosenCandidateId"] == "c1"


def test_judge_may_override_within_set(monkeypatch) -> None:
    cfg = AppConfig(
        ai_capability=AiCapabilityConfig(
            enabled=False,
            mosaic_judge=MosaicJudgeConfig(enabled=True),
        ),
        studio=StudioConfig(ai_surface_enabled=True),
        llm=LlmConfig(provider="deepseek"),
    )
    monkeypatch.setattr(
        "travelogue.ai.agents.mosaic_judge.resolve_llm_may_call",
        lambda cfg=None: True,
    )
    monkeypatch.setattr(
        "travelogue.ai.agents.mosaic_judge.probe_llm_ready",
        lambda cfg=None: True,
    )

    def fake_chat(_messages):
        return json.dumps({"chosenCandidateId": "c2"}, ensure_ascii=False)

    trip: dict = {"tripId": "t-mj3", "curation": {}}
    with app_config_scope(cfg):
        entry = review_mosaic_tie(
            window_id="w3",
            candidates=[{"id": "c1", "summary": "A"}, {"id": "c2", "summary": "B"}],
            first_pass_candidate_id="c1",
            trip=trip,
            chat_fn=fake_chat,
        )
    assert entry["chosenCandidateId"] == "c2"
    assert entry["overriddenFromFirstPass"] is True
    assert entry["source"] == "llm"


def test_judge_exception_fail_open(monkeypatch) -> None:
    cfg = AppConfig(
        ai_capability=AiCapabilityConfig(
            enabled=False,
            mosaic_judge=MosaicJudgeConfig(enabled=True),
        ),
        studio=StudioConfig(ai_surface_enabled=True),
        llm=LlmConfig(provider="deepseek"),
    )
    monkeypatch.setattr(
        "travelogue.ai.agents.mosaic_judge.resolve_llm_may_call",
        lambda cfg=None: True,
    )
    monkeypatch.setattr(
        "travelogue.ai.agents.mosaic_judge.probe_llm_ready",
        lambda cfg=None: True,
    )

    def boom(_m):
        raise TimeoutError("slow")

    with app_config_scope(cfg):
        entry = review_mosaic_tie(
            window_id="w4",
            candidates=["c1", "c2"],
            first_pass_candidate_id="c1",
            chat_fn=boom,
        )
    assert entry["chosenCandidateId"] == "c1"
    assert entry["source"] == "fallback"
