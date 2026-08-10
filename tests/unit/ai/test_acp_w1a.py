"""ACP W1a · gate / budget / telemetry unit tests."""

from __future__ import annotations

from travelogue.ai.budget import TripLlmBudget, clear_budgets
from travelogue.ai.cache import content_sig, read_cached, write_cached
from travelogue.ai.gate import check_gate
from travelogue.ai.telemetry import (
    AgentCallRecord,
    clear_ops_summary,
    ops_summary,
    record_agent_call,
)
from travelogue.config.ai_capability import AiCapabilityConfig, ai_capability_config_from_dict
from travelogue.config.app import AppConfig
from travelogue.config.misc import LlmConfig
from travelogue.config.runtime import app_config_scope
from travelogue.config.studio import StudioConfig


def setup_function() -> None:
    clear_budgets()
    clear_ops_summary()


def test_ai_capability_config_defaults_disabled() -> None:
    cfg = ai_capability_config_from_dict({})
    assert cfg.enabled is False
    assert cfg.max_calls_per_trip == 12


def test_gate_capability_disabled_by_default() -> None:
    with app_config_scope(AppConfig()):
        decision = check_gate()
    assert decision.allow is False
    assert decision.reason == "capability_disabled"


def test_gate_and_matrix_surface_off() -> None:
    cfg = AppConfig(
        ai_capability=AiCapabilityConfig(enabled=True),
        studio=StudioConfig(ai_surface_enabled=False),
        llm=LlmConfig(provider="stub"),
    )
    with app_config_scope(cfg):
        decision = check_gate()
    assert decision.allow is False
    assert decision.reason == "surface_off"


def test_gate_and_matrix_stub_provider(monkeypatch) -> None:
    cfg = AppConfig(
        ai_capability=AiCapabilityConfig(enabled=True),
        studio=StudioConfig(ai_surface_enabled=True),
        llm=LlmConfig(provider="stub"),
    )
    monkeypatch.setattr(
        "travelogue.ai.gate.resolve_ready_provider", lambda cfg=None: "stub"
    )
    monkeypatch.setattr(
        "travelogue.ai.gate.probe_llm_ready", lambda cfg=None: False
    )
    with app_config_scope(cfg):
        decision = check_gate()
    assert decision.allow is False
    assert decision.reason in ("stub", "no_key")


def test_budget_try_consume_and_exceed() -> None:
    budget = TripLlmBudget(max_calls=2, trip_id="t1")
    assert budget.try_consume("a") is True
    assert budget.try_consume("b") is True
    assert budget.try_consume("c") is False
    assert budget.used == 2


def test_cache_roundtrip(tmp_path) -> None:
    sig = content_sig({"x": 1}, prompt_version="v1")
    write_cached(tmp_path, agent="intent_brief", sig=sig, payload={"ok": True})
    assert read_cached(tmp_path, agent="intent_brief", sig=sig) == {"ok": True}


def test_telemetry_summary_without_trip_persist_when_acp_off() -> None:
    trip: dict = {"tripId": "demo", "pipeline": {"runs": []}}
    with app_config_scope(AppConfig()):
        record_agent_call(
            trip,
            AgentCallRecord(
                agent="title_art_route_c",
                source="llm",
                ok=True,
                latency_ms=12.5,
            ),
        )
    assert trip["pipeline"]["runs"] == []
    summary = ops_summary()
    assert summary["title_art_route_c"]["calls"] == 1


def test_telemetry_persists_when_acp_on() -> None:
    trip: dict = {"tripId": "demo", "pipeline": {"runs": []}}
    cfg = AppConfig(ai_capability=AiCapabilityConfig(enabled=True))
    with app_config_scope(cfg):
        record_agent_call(
            trip,
            AgentCallRecord(
                agent="title_art_route_c",
                source="fallback",
                ok=False,
                latency_ms=0.0,
                reason="surface_off",
            ),
            persist_to_trip=True,
        )
    assert len(trip["pipeline"]["runs"]) == 1
    assert trip["pipeline"]["runs"][0]["agent"] == "title_art_route_c"
