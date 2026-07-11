"""AC-PT-08 · concurrent narrate respects cache hits (no duplicate HTTP)."""

from __future__ import annotations

import json
from copy import deepcopy

from travelogue.config import AppConfig, LlmConfig
from travelogue.services.llm_narrate import run_llm_narrate


def _trip() -> dict:
    return {
        "tripId": "pt-cache",
        "meta": {
            "title": "缓存",
            "dateStart": "2025-04-01",
            "dateEnd": "2025-04-03",
            "places": ["京都"],
            "tone": "relaxed",
            "hook": "hook。",
        },
        "epilogue": "尾。",
        "assets": [
            {"id": "a1", "type": "image", "place": {"city": "京都"}},
            {"id": "a2", "type": "image", "place": {"city": "京都"}},
            {"id": "a3", "type": "image", "place": {"city": "京都"}},
        ],
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "patternId": "open",
                "title": "一",
                "lead": "",
                "items": [{"type": "media-card", "assetId": "a1"}],
            },
            {
                "id": "ch-02",
                "index": 2,
                "patternId": "gallery",
                "title": "二",
                "lead": "",
                "items": [{"type": "media-card", "assetId": "a2"}],
            },
            {
                "id": "ch-03",
                "index": 3,
                "patternId": "close",
                "title": "三",
                "lead": "",
                "items": [{"type": "media-card", "assetId": "a3"}],
            },
        ],
        "pipeline": {"status": "structure_locked", "locks": {"structure": True, "copy": False}},
    }


def test_concurrent_cache_hit_skips_http(tmp_path) -> None:
    trip = _trip()
    calls = {"n": 0}

    def fake_chat(messages: list[dict[str, str]]) -> str:
        calls["n"] += 1
        user = messages[-1]["content"]
        for i, ch in enumerate(("ch-01", "ch-02", "ch-03"), start=1):
            if ch in user:
                return json.dumps(
                    {
                        "chapterId": ch,
                        "lead": f"导语{i}",
                        "items": [{"assetId": f"a{i}", "caption": f"c{i}"}],
                    },
                    ensure_ascii=False,
                )
        raise AssertionError(user[:80])

    cfg = AppConfig(llm=LlmConfig(provider="deepseek", narrate_concurrency=3))
    run_llm_narrate(
        trip,
        provider="deepseek",
        chat_fn=fake_chat,
        scope="full",
        cfg=cfg,
        cache_dir=tmp_path,
    )
    first_calls = calls["n"]
    assert first_calls >= 3
    assert trip["pipeline"]["timings"]["narrateCacheMisses"] >= 3

    # Second run: empty leads cleared → needs copy again but cache should hit
    trip2 = deepcopy(trip)
    for ch in trip2["chapters"]:
        ch["lead"] = ""
        for it in ch.get("items") or []:
            it.pop("caption", None)
    for a in trip2["assets"]:
        a.pop("caption", None)
    calls["n"] = 0
    run_llm_narrate(
        trip2,
        provider="deepseek",
        chat_fn=fake_chat,
        scope="full",
        cfg=cfg,
        cache_dir=tmp_path,
    )
    assert calls["n"] == 0
    assert trip2["pipeline"]["timings"]["narrateCacheHits"] >= 3
    assert all((ch.get("lead") or "").strip() for ch in trip2["chapters"])
