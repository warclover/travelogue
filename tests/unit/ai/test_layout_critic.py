"""ACP W3 · Layout Critic agent unit tests (AC-ACP-07 / SHD-ACP-02)."""

from __future__ import annotations

import json

from travelogue.ai.agents.layout_critic import (
    SUGGESTION_HARD_MAX,
    accept_layout_suggestion,
    build_chapter_screen_summaries,
    pattern_whitelist,
    run_layout_critic,
)
from travelogue.ai.budget import clear_budgets
from travelogue.ai.telemetry import clear_ops_summary
from travelogue.config.ai_capability import AiCapabilityConfig, LayoutCriticConfig
from travelogue.config.app import AppConfig
from travelogue.config.misc import LlmConfig
from travelogue.config.runtime import app_config_scope
from travelogue.config.studio import StudioConfig


def setup_function() -> None:
    clear_budgets()
    clear_ops_summary()


def _trip() -> dict:
    return {
        "tripId": "t-critic",
        "assets": [
            {"id": "a1", "width": 1000, "height": 1500},
            {"id": "a2", "width": 1000, "height": 1400},
            {"id": "a3", "width": 1000, "height": 1600},
            {"id": "a4", "width": 1600, "height": 1000},
        ],
        "chapters": [
            {
                "id": "ch-01",
                "title": "雨巷",
                "screens": [
                    {
                        "screenId": "s1",
                        "patternId": "screen-portrait-3",
                        "assetIds": ["a1", "a2", "a3"],
                    },
                    {
                        "screenId": "s2",
                        "patternId": "screen-landscape-1",
                        "assetIds": ["a4"],
                    },
                ],
            }
        ],
        "curation": {},
    }


def test_summary_has_no_pixel_fields() -> None:
    summary = build_chapter_screen_summaries(_trip())
    raw = json.dumps(summary)
    assert "base64" not in raw.lower()
    assert "file://" not in raw
    assert summary[0]["chapterId"] == "ch-01"
    assert summary[0]["orientationCounts"]["portrait"] >= 1


def test_layout_critic_disabled_returns_fallback() -> None:
    with app_config_scope(AppConfig()):
        result = run_layout_critic(_trip(), force=True)
    assert result["source"] == "fallback"
    assert result.get("reason") == "layout_critic_disabled"
    assert result["suggestions"] == []


def test_layout_critic_filters_unknown_pattern(monkeypatch, tmp_path) -> None:
    cfg = AppConfig(
        ai_capability=AiCapabilityConfig(
            enabled=False,
            layout_critic=LayoutCriticConfig(enabled=True),
        ),
        studio=StudioConfig(ai_surface_enabled=True),
        llm=LlmConfig(provider="deepseek"),
    )
    monkeypatch.setattr(
        "travelogue.ai.agents.layout_critic.resolve_llm_may_call",
        lambda cfg=None: True,
    )
    monkeypatch.setattr(
        "travelogue.ai.agents.layout_critic.probe_llm_ready",
        lambda cfg=None: True,
    )

    def fake_chat(_messages):
        return json.dumps(
            {
                "suggestions": [
                    {
                        "chapterId": "ch-01",
                        "suggestedPatternId": "screen-invented-xyz",
                        "suggestion": "发明版式应被丢弃",
                        "confidence": 0.9,
                    },
                    {
                        "chapterId": "ch-01",
                        "suggestedPatternId": "screen-portrait-3",
                        "suggestion": "竖图较多可保持三联或改 gallery",
                        "confidence": 0.8,
                    },
                ]
            },
            ensure_ascii=False,
        )

    trip = _trip()
    wl = pattern_whitelist(trip)
    assert "screen-portrait-3" in wl
    with app_config_scope(cfg):
        result = run_layout_critic(
            trip, chat_fn=fake_chat, force=True, cache_dir=tmp_path / "c"
        )
    assert result["source"] == "llm"
    pids = [s["suggestedPatternId"] for s in result["suggestions"]]
    assert "screen-invented-xyz" not in pids
    assert "screen-portrait-3" in pids
    assert all(len(s["suggestion"]) <= SUGGESTION_HARD_MAX for s in result["suggestions"])
    assert trip["curation"]["layoutSuggestions"]


def test_layout_critic_exception_fail_open(monkeypatch, tmp_path) -> None:
    cfg = AppConfig(
        ai_capability=AiCapabilityConfig(
            enabled=False,
            layout_critic=LayoutCriticConfig(enabled=True),
        ),
        studio=StudioConfig(ai_surface_enabled=True),
        llm=LlmConfig(provider="deepseek"),
    )
    monkeypatch.setattr(
        "travelogue.ai.agents.layout_critic.resolve_llm_may_call",
        lambda cfg=None: True,
    )
    monkeypatch.setattr(
        "travelogue.ai.agents.layout_critic.probe_llm_ready",
        lambda cfg=None: True,
    )

    def boom(_messages):
        raise RuntimeError("network down")

    with app_config_scope(cfg):
        result = run_layout_critic(
            _trip(), chat_fn=boom, force=True, cache_dir=tmp_path / "c"
        )
    assert result["source"] == "fallback"
    assert result["suggestions"] == []


def test_accept_layout_suggestion() -> None:
    trip = _trip()
    trip["curation"]["layoutSuggestions"] = [
        {
            "chapterId": "ch-01",
            "suggestedPatternId": "screen-portrait-3",
            "suggestion": "保持三联",
            "accepted": False,
            "source": "llm",
        }
    ]
    hit = accept_layout_suggestion(trip, chapter_id="ch-01")
    assert hit is not None and hit["accepted"] is True
    assert trip["curation"]["layoutSuggestions"][0]["accepted"] is True
