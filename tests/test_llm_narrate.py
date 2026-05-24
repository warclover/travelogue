"""LLM narrate tests (mocked chat, no live API)."""

from __future__ import annotations

import json

import pytest

from travelogue.llm.client import parse_json_content
from travelogue.services.llm_narrate import run_llm_narrate
from travelogue.services.narrate import run_narrate


def _sample_trip() -> dict:
    return {
        "tripId": "kyoto-test",
        "meta": {
            "title": "雨后京都",
            "dateStart": "2025-04-02",
            "dateEnd": "2025-04-06",
            "places": ["京都"],
            "tone": "relaxed",
        },
        "assets": [
            {
                "id": "a1",
                "type": "image",
                "takenAt": "2025-04-02T10:00:00Z",
                "tags": ["雨", "街道"],
                "place": {"city": "京都"},
            },
            {
                "id": "a2",
                "type": "image",
                "takenAt": "2025-04-03T10:00:00Z",
                "tags": ["夜景"],
                "place": {"city": "祇园"},
            },
            {
                "id": "a3",
                "type": "image",
                "takenAt": "2025-04-04T10:00:00Z",
                "place": {"city": "岚山"},
            },
            {"id": "a4", "type": "image", "place": {"city": "京都"}},
        ],
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "patternId": "open",
                "title": "4月2日",
                "lead": "",
                "items": [{"type": "media-card", "assetId": "a1"}],
            },
            {
                "id": "ch-02",
                "index": 2,
                "patternId": "gallery",
                "title": "4月3日",
                "lead": "",
                "items": [{"type": "media-card", "assetId": "a2"}],
            },
            {
                "id": "ch-03",
                "index": 3,
                "patternId": "close",
                "title": "尾声",
                "lead": "",
                "items": [{"type": "media-card", "assetId": "a3"}],
            },
        ],
        "pipeline": {"status": "structure_locked", "locks": {"structure": True, "copy": False}},
    }


def test_parse_json_content_strips_fence():
    raw = '```json\n{"meta": {"hook": "你好"}}\n```'
    data = parse_json_content(raw)
    assert data["meta"]["hook"] == "你好"


def test_run_narrate_defaults_to_stub():
    trip = _sample_trip()
    result = run_narrate(trip, provider="stub")
    assert trip["meta"]["hook"]
    assert result.fields_updated
    assert trip["pipeline"]["runs"][-1]["model"] == "rule-stub"


def test_llm_narrate_mock_meta_and_chapters():
    trip = _sample_trip()
    calls: list[str] = []

    def fake_chat(messages: list[dict[str, str]]) -> str:
        user = messages[-1]["content"]
        calls.append(user)
        if "fill_trip_meta" in user or "meta 文案" in user:
            return json.dumps(
                {"meta": {"hook": "雨中的京都，慢慢走。"}, "epilogue": "下次再见。"},
                ensure_ascii=False,
            )
        if "ch-01" in user:
            return json.dumps(
                {
                    "chapterId": "ch-01",
                    "lead": "从车站出发，雨没停。",
                    "items": [{"assetId": "a1", "caption": "湿漉漉的站前。"}],
                },
                ensure_ascii=False,
            )
        if "ch-02" in user:
            return json.dumps(
                {
                    "chapterId": "ch-02",
                    "lead": "夜里走进祇园。",
                    "items": [{"assetId": "a2", "caption": "灯笼映在石板路上。"}],
                },
                ensure_ascii=False,
            )
        if "ch-03" in user:
            return json.dumps(
                {
                    "chapterId": "ch-03",
                    "lead": "岚山的风很轻。",
                    "items": [{"assetId": "a3", "caption": "山道上的余温。"}],
                },
                ensure_ascii=False,
            )
        pytest.fail(f"unexpected prompt: {user[:200]}")

    result = run_llm_narrate(trip, provider="deepseek", chat_fn=fake_chat)
    assert "meta.hook" in result.fields_updated
    assert trip["meta"]["hook"] == "雨中的京都，慢慢走。"
    assert all(ch["lead"] for ch in trip["chapters"])
    assert trip["chapters"][0]["items"][0].get("caption")
    assert len(calls) >= 4
    assert trip["pipeline"]["runs"][-1]["model"].startswith("deepseek/")


def test_llm_narrate_dry_run_lists_fields():
    trip = _sample_trip()
    result = run_llm_narrate(trip, provider="deepseek", dry_run=True)
    assert "meta.hook" in result.fields_updated
    assert not trip["meta"].get("hook")
