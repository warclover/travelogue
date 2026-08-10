"""ACP W2 · Intent Brief agent unit tests."""

from __future__ import annotations

import json

from travelogue.ai.agents.intent_brief import (
    build_intent_brief_summary,
    run_intent_brief,
)
from travelogue.ai.budget import clear_budgets
from travelogue.ai.telemetry import clear_ops_summary
from travelogue.config.ai_capability import AiCapabilityConfig, IntentBriefConfig
from travelogue.config.app import AppConfig
from travelogue.config.misc import LlmConfig
from travelogue.config.runtime import app_config_scope
from travelogue.config.studio import StudioConfig
from travelogue.layout_engine.intent_hints import (
    build_intent_hints,
    peak_chapter_hints_for_trip,
)


def setup_function() -> None:
    clear_budgets()
    clear_ops_summary()


def _trip() -> dict:
    return {
        "tripId": "t-intent",
        "userNotes": "雨后京都，day2 最难忘，只要风景",
        "intent": {"version": "1"},
        "assets": [
            {"id": "a1", "place": "京都"},
            {"id": "a2", "city": "大阪"},
        ],
        "meta": {"title": "拾光"},
    }


def test_build_summary_has_no_pixel_fields() -> None:
    summary = build_intent_brief_summary(_trip())
    assert summary["userNotes"]
    assert summary["assetCount"] == 2
    assert "京都" in summary["placeSamples"]
    raw = json.dumps(summary)
    assert "base64" not in raw.lower()
    assert "file://" not in raw


def test_intent_brief_disabled_returns_fallback() -> None:
    with app_config_scope(AppConfig()):
        brief = run_intent_brief(_trip(), force=True)
    assert brief["source"] == "fallback"
    assert brief.get("reason") == "intent_brief_disabled"


def test_intent_brief_with_chat_fn_when_may_call(monkeypatch, tmp_path) -> None:
    cfg = AppConfig(
        ai_capability=AiCapabilityConfig(
            enabled=False,
            intent_brief=IntentBriefConfig(enabled=True),
        ),
        studio=StudioConfig(ai_surface_enabled=True),
        llm=LlmConfig(provider="deepseek"),
    )
    monkeypatch.setattr(
        "travelogue.ai.agents.intent_brief.resolve_llm_may_call",
        lambda cfg=None: True,
    )
    monkeypatch.setattr(
        "travelogue.ai.agents.intent_brief.probe_llm_ready",
        lambda cfg=None: True,
    )

    def fake_chat(_messages):
        return json.dumps(
            {
                "titleHint": "雨后京都",
                "tone": "quiet documentary",
                "peakMoments": ["祇园夜雨"],
                "cullPolicy": {"dropScreenshots": True},
                "clusterHints": {},
                "layoutHints": {"peakChapterIndex": 2, "preferMosaic": True},
                "narrativeHints": {},
            },
            ensure_ascii=False,
        )

    trip = _trip()
    with app_config_scope(cfg):
        brief = run_intent_brief(
            trip, chat_fn=fake_chat, force=True, cache_dir=tmp_path / "c"
        )
    assert brief["source"] == "llm"
    assert brief["titleHint"] == "雨后京都"
    assert trip["intent"]["intentBrief"]["layoutHints"]["peakChapterIndex"] == 2


def test_intent_hints_prefer_brief_peak() -> None:
    trip = _trip()
    trip["intent"]["intentBrief"] = {
        "source": "llm",
        "confidence": 0.8,
        "layoutHints": {"peakChapterIndex": 3, "preferMosaic": True},
        "peakMoments": ["高潮夜"],
        "cullPolicy": {"dropScreenshots": True},
    }
    assert peak_chapter_hints_for_trip(trip, 5) == {3}
    hints = build_intent_hints(trip)
    assert hints.get("preferMosaic") is True
    assert hints.get("intentBriefCullPolicy", {}).get("dropScreenshots") is True
    assert any("高潮" in str(k) or "夜" in str(k) for k in hints.get("userNotesKeywords") or [])
