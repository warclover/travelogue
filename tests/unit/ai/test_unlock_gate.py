"""ACP W4 · unlock_gate deterministic verdicts (AC-ACP-11)."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.ai.eval.unlock_gate import (
    UnlockMetrics,
    UnlockThresholds,
    aggregate_studio_events,
    compute_unlock_gate,
    format_unlock_report,
    metrics_from_dict,
)
from travelogue.ai.telemetry import clear_ops_summary, ops_summary


def setup_function() -> None:
    clear_ops_summary()


def _full(n: int = 40, *, cfg_rate: float = 0.5, nar_rate: float = 0.8, copy_rate: float = 0.4) -> UnlockMetrics:
    return UnlockMetrics(
        config_opens=n,
        config_completions=int(n * cfg_rate),
        narrate_attempts=n,
        narrate_successes=int(n * nar_rate),
        copy_opportunities=n,
        copy_successes=int(n * copy_rate),
        source="fixture",
    )


def test_insufficient_data_when_samples_low() -> None:
    m = _full(10)
    r = compute_unlock_gate(m, thresholds=UnlockThresholds(min_samples=30))
    assert r.verdict == "insufficient-data"


def test_go_when_all_floors_met() -> None:
    r = compute_unlock_gate(_full(40), thresholds=UnlockThresholds(min_samples=30))
    assert r.verdict == "go"
    assert "AIR" in format_unlock_report(r) or "解冻" in format_unlock_report(r)


def test_nogo_when_narrate_below_floor() -> None:
    r = compute_unlock_gate(
        _full(40, nar_rate=0.2),
        thresholds=UnlockThresholds(min_samples=30, narrate_success_rate=0.7),
    )
    assert r.verdict == "no-go"
    assert any("narrateSuccess" in x for x in r.reasons)


def test_metrics_from_dict_and_jsonl(tmp_path: Path) -> None:
    m = metrics_from_dict(
        {
            "configOpens": 40,
            "configCompletions": 20,
            "narrateAttempts": 40,
            "narrateSuccesses": 32,
            "copyOpportunities": 40,
            "copySuccesses": 16,
        }
    )
    assert compute_unlock_gate(m).verdict == "go"

    lines = [
        {"event": "llm_settings_open"},
        {"event": "llm_settings_save"},
        {"event": "llm_narrate_click"},
        {"event": "import_success"},
        {"event": "sfp_xhs_copy_pack_copied"},
        {"event": "title_art_impression"},
        {"event": "title_art_resolve", "meta": {"outcome": "success"}},
    ]
    p = tmp_path / "events.jsonl"
    p.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
    agg = aggregate_studio_events(p)
    assert agg.config_opens == 1
    assert agg.config_completions == 1
    assert agg.title_art_impressions == 1
    assert agg.title_art_resolves == 1


def test_ops_summary_includes_six_known_agents() -> None:
    agents = ops_summary()
    for name in (
        "intent_brief",
        "layout_critic",
        "mosaic_judge",
        "narrate",
        "title_art_route_c",
        "aesthetic_mllm",
    ):
        assert name in agents
    assert len(agents) >= 6


def test_ac_acp_10_ops_summary_six_agents_nonzero_after_calls() -> None:
    """AC-ACP-10 · 六类 Agent 经 record_agent_call 后 ops_summary 可验非零。"""
    from travelogue.ai.telemetry import AgentCallRecord, KNOWN_OPS_AGENTS, record_agent_call

    for name in KNOWN_OPS_AGENTS:
        record_agent_call(
            None,
            AgentCallRecord(
                agent=name,
                source="llm",
                ok=True,
                latency_ms=12.0,
            ),
        )
    agents = ops_summary()
    assert len(KNOWN_OPS_AGENTS) >= 6
    for name in KNOWN_OPS_AGENTS:
        assert agents[name]["calls"] >= 1
        assert agents[name]["ok"] >= 1
        assert agents[name]["avgLatencyMs"] > 0
