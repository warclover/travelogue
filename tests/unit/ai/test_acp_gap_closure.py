"""ACP gap closure · AC-ACP-15/16 helpers, timeout, intent consumers."""

from __future__ import annotations

import json

import pytest

from travelogue.ai.agents.intent_brief import run_intent_brief
from travelogue.ai.budget import clear_budgets
from travelogue.ai.call import chat_with_timeout
from travelogue.ai.gate import check_gate
from travelogue.ai.telemetry import clear_ops_summary
from travelogue.config.ai_capability import AiCapabilityConfig, IntentBriefConfig
from travelogue.config.app import AppConfig
from travelogue.config.misc import LlmConfig
from travelogue.config.runtime import app_config_scope
from travelogue.config.studio import StudioConfig
from travelogue.layout_engine.intent_hints import build_intent_hints
from travelogue.llm.errors import LlmError


def setup_function() -> None:
    clear_budgets()
    clear_ops_summary()


def test_gate_blocks_when_any_and_false() -> None:
    """AC-ACP-16 · capability off → disallow."""
    with app_config_scope(AppConfig(ai_capability=AiCapabilityConfig(enabled=False))):
        d = check_gate()
    assert d.allow is False


def test_chat_with_timeout_raises(monkeypatch) -> None:
    def slow(_messages):
        import time

        time.sleep(0.35)
        return "{}"

    with pytest.raises(LlmError) as ei:
        chat_with_timeout([], chat_fn=slow, timeout=0.05)
    assert ei.value.code == "E_ACP_TIMEOUT"


def test_intent_brief_cluster_hints_mirrored(monkeypatch, tmp_path) -> None:
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

    def fake_chat(_m):
        return json.dumps(
            {
                "clusterHints": {"preferFewerChapters": True},
                "cullPolicy": {"dropScreenshots": False},
                "layoutHints": {},
                "narrativeHints": {},
                "peakMoments": [],
            },
            ensure_ascii=False,
        )

    trip = {"tripId": "t-c", "intent": {"version": "1"}, "assets": []}
    with app_config_scope(cfg):
        brief = run_intent_brief(
            trip, chat_fn=fake_chat, force=True, cache_dir=tmp_path / "c"
        )
    assert brief["source"] == "llm"
    hints = build_intent_hints(trip)
    assert hints.get("intentBriefClusterHints", {}).get("preferFewerChapters") is True
    assert hints.get("intentBriefCullPolicy", {}).get("dropScreenshots") is False


def test_prefer_fewer_chapters_caps_segments() -> None:
    from travelogue.curation.clustering_buckets import cap_geo_segments

    segs = [
        {"id": f"s{i}", "assetIds": [f"a{i}"], "startDate": "2026-01-01", "endDate": "2026-01-01"}
        for i in range(6)
    ]
    out = cap_geo_segments(segs, max_chapters=3)
    assert len(out) <= 3
