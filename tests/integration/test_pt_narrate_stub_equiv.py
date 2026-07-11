"""AC-PT stub field equivalence: concurrency 1 vs N (LLM mock)."""

from __future__ import annotations

import json
from copy import deepcopy

import pytest

from travelogue.config import AppConfig, LlmConfig
from travelogue.services.llm_narrate import run_llm_narrate

pytestmark = pytest.mark.integration


def _sample_trip() -> dict:
    return {
        "tripId": "pt-stub-equiv",
        "meta": {
            "title": "雨后京都",
            "dateStart": "2025-04-02",
            "dateEnd": "2025-04-06",
            "places": ["京都"],
            "tone": "relaxed",
            "hook": "已有。",
        },
        "epilogue": "尾声已有。",
        "assets": [
            {"id": "a1", "type": "image", "place": {"city": "京都"}},
            {"id": "a2", "type": "image", "place": {"city": "祇园"}},
            {"id": "a3", "type": "image", "place": {"city": "岚山"}},
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


def _fake_chat(messages: list[dict[str, str]]) -> str:
    user = messages[-1]["content"]
    mapping = {
        "ch-01": (
            "从车站出发，雨没停。",
            "a1",
            "湿漉漉的站前。",
        ),
        "ch-02": (
            "夜里走进祇园。",
            "a2",
            "灯笼映在石板路上。",
        ),
        "ch-03": (
            "岚山的风很轻。",
            "a3",
            "山道上的余温。",
        ),
    }
    for ch_id, (lead, aid, cap) in mapping.items():
        if ch_id in user:
            return json.dumps(
                {
                    "chapterId": ch_id,
                    "lead": lead,
                    "items": [{"assetId": aid, "caption": cap}],
                },
                ensure_ascii=False,
            )
    raise AssertionError(user[:160])


def test_pt_narrate_concurrency_1_vs_n_field_equiv() -> None:
    base = _sample_trip()
    t1 = deepcopy(base)
    t2 = deepcopy(base)
    cfg1 = AppConfig(llm=LlmConfig(provider="deepseek", narrate_concurrency=1))
    cfg_n = AppConfig(llm=LlmConfig(provider="deepseek", narrate_concurrency=3))
    run_llm_narrate(t1, provider="deepseek", chat_fn=_fake_chat, scope="full", cfg=cfg1)
    run_llm_narrate(t2, provider="deepseek", chat_fn=_fake_chat, scope="full", cfg=cfg_n)

    def fingerprint(trip: dict) -> dict:
        return {
            "leads": [c.get("lead") for c in trip["chapters"]],
            "captions": [
                (it.get("caption") if it.get("type") == "media-card" else None)
                for c in trip["chapters"]
                for it in (c.get("items") or [])
            ],
        }

    assert fingerprint(t1) == fingerprint(t2)
    assert t1["pipeline"]["timings"]["narrateConcurrency"] == 1
    assert t2["pipeline"]["timings"]["narrateConcurrency"] == 3
