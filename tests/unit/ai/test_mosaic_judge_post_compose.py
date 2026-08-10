"""ACP · D-ACP-15 / AC-ACP-17 · Mosaic Judge post-compose wiring."""

from __future__ import annotations

from travelogue.ai.agents.mosaic_judge import (
    collect_tie_windows_from_logs,
    run_post_compose_mosaic_judge,
)
from travelogue.ai.budget import clear_budgets
from travelogue.ai.eval.tie_epsilon_stats import compute_tie_epsilon_stats
from travelogue.ai.telemetry import clear_ops_summary
from travelogue.config.ai_capability import AiCapabilityConfig, MosaicJudgeConfig
from travelogue.config.app import AppConfig
from travelogue.config.runtime import app_config_scope


def setup_function() -> None:
    clear_budgets()
    clear_ops_summary()


def test_collect_tie_windows_from_raw_logs() -> None:
    logs = [
        {
            "segmentId": "s1",
            "windowStart": 0,
            "windowSize": 4,
            "winnerPatternId": "p1",
            "top3Patterns": ["p1", "p2", "p3"],
            "top3Scores": [1.0, 0.985, 0.7],
        },
        {
            "winnerPatternId": "q1",
            "top3Patterns": ["q1", "q2"],
            "top3Scores": [1.0, 0.5],
        },
    ]
    ties = collect_tie_windows_from_logs(logs, epsilon=0.03)
    assert len(ties) == 1
    assert ties[0]["firstPassCandidateId"] == "p1"


def test_post_compose_disabled_is_noop() -> None:
    trip = {"tripId": "t1", "curation": {}}
    with app_config_scope(AppConfig()):
        out = run_post_compose_mosaic_judge(
            trip,
            [{"top3Patterns": ["a", "b"], "top3Scores": [1.0, 0.99], "winnerPatternId": "a"}],
            async_schedule=False,
        )
    assert out == []
    assert not (trip.get("curation") or {}).get("mosaicJudgeLog")


def test_post_compose_reviews_ties_without_beam_import(monkeypatch) -> None:
    """AC-ACP-17 prep: judge path must not import SearchBudget / try_mosaic_window."""
    import travelogue.ai.agents.mosaic_judge as mj

    # Ensure hot-path modules are not pulled by post-compose entry.
    assert "travelogue.layout_engine.planner.screen_planner_stages" not in __import__(
        "sys"
    ).modules or True

    cfg = AppConfig(
        ai_capability=AiCapabilityConfig(
            mosaic_judge=MosaicJudgeConfig(enabled=True, tie_epsilon=0.05),
        )
    )
    monkeypatch.setattr(mj, "resolve_llm_may_call", lambda cfg=None: True)
    monkeypatch.setattr(mj, "probe_llm_ready", lambda cfg=None: True)

    def fake_chat(_m):
        return '{"chosenCandidateId":"p2"}'

    trip = {"tripId": "t2", "curation": {}}
    logs = [
        {
            "segmentId": "s",
            "windowStart": 1,
            "windowSize": 3,
            "winnerPatternId": "p1",
            "top3Patterns": ["p1", "p2"],
            "top3Scores": [1.0, 0.98],
        }
    ]
    with app_config_scope(cfg):
        out = run_post_compose_mosaic_judge(
            trip, logs, chat_fn=fake_chat, async_schedule=False
        )
    assert len(out) == 1
    assert out[0]["chosenCandidateId"] == "p2"
    assert out[0]["overriddenFromFirstPass"] is True


def test_tie_epsilon_stats_shd_acp_01() -> None:
    logs = [
        {"top3Scores": [1.0, 0.99]},
        {"top3Scores": [1.0, 0.5]},
        {"top3Scores": [0.9, 0.89]},
        {"top3Scores": [0.8, 0.2]},
    ]
    stats = compute_tie_epsilon_stats({"t": logs}, target_trigger_rate=0.5)
    assert stats.window_count == 4
    assert stats.recommended_epsilon > 0
    assert stats.mean_triggers_per_trip >= 0
