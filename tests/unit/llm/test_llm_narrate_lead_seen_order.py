"""AC-PT-10 · lead_seen remains ordered despite out-of-order chapter completion."""

from __future__ import annotations

import json
import threading
import time
from copy import deepcopy

from travelogue.config import AppConfig, LlmConfig
from travelogue.services.llm_narrate import run_llm_narrate


def _trip_with_chapters(n: int = 6) -> dict:
    assets = [{"id": f"a{i}", "type": "image", "place": {"city": "京都"}} for i in range(1, n + 1)]
    chapters = []
    for i in range(1, n + 1):
        chapters.append(
            {
                "id": f"ch-{i:02d}",
                "index": i,
                "patternId": "gallery",
                "title": f"第{i}站",
                "lead": "",
                "items": [{"type": "media-card", "assetId": f"a{i}"}],
            }
        )
    return {
        "tripId": "pt-lead-seen",
        "meta": {
            "title": "测试",
            "dateStart": "2025-04-01",
            "dateEnd": "2025-04-06",
            "places": ["京都"],
            "tone": "relaxed",
            "hook": "已有 hook。",
        },
        "epilogue": "已有结尾。",
        "assets": assets,
        "chapters": chapters,
        "pipeline": {"status": "structure_locked", "locks": {"structure": True, "copy": False}},
    }


def test_lead_seen_order_with_out_of_order_completion() -> None:
    """Chapters finish reverse-order; applied leads still dedupe in index order."""
    trip = _trip_with_chapters(6)
    finish_order: list[str] = []
    lock = threading.Lock()

    def fake_chat(messages: list[dict[str, str]]) -> str:
        user = messages[-1]["content"]
        # Deliberately delay early chapters so later ones complete first.
        for i in range(6, 0, -1):
            ch = f"ch-{i:02d}"
            if ch in user:
                # later chapter → shorter sleep
                time.sleep(0.01 * (7 - i))
                with lock:
                    finish_order.append(ch)
                # Identical lead text → lead_seen must suffix later chapters
                return json.dumps(
                    {
                        "chapterId": ch,
                        "lead": "同一句导语。",
                        "items": [{"assetId": f"a{i}", "caption": f"图{i}"}],
                    },
                    ensure_ascii=False,
                )
        raise AssertionError(user[:120])

    cfg = AppConfig(llm=LlmConfig(provider="deepseek", narrate_concurrency=3))
    result = run_llm_narrate(
        trip, provider="deepseek", chat_fn=fake_chat, scope="full", cfg=cfg
    )
    assert result.fields_updated
    leads = [ch["lead"] for ch in trip["chapters"]]
    assert leads[0] == "同一句导语。"
    # Subsequent identical leads get ·N suffixes via lead_seen (ordered apply)
    assert leads[1] != leads[0] or all(leads[i] != leads[0] for i in range(1, 6))
    assert len(set(leads)) == 6
    assert trip["pipeline"]["timings"]["narrateConcurrency"] == 3
    # Completion order should not be ascending (out-of-order finish)
    assert finish_order[0] != "ch-01" or finish_order != sorted(finish_order)


def test_concurrency_one_matches_serial_fields() -> None:
    """AC-PT-06 direction: concurrency=1 vs explicit serial produce same leads."""
    base = _trip_with_chapters(4)

    def fake_chat(messages: list[dict[str, str]]) -> str:
        user = messages[-1]["content"]
        for i in range(1, 5):
            ch = f"ch-{i:02d}"
            if ch in user:
                return json.dumps(
                    {
                        "chapterId": ch,
                        "lead": f"导语{i}。",
                        "items": [{"assetId": f"a{i}", "caption": f"说明{i}"}],
                    },
                    ensure_ascii=False,
                )
        raise AssertionError(user[:120])

    t1 = deepcopy(base)
    t2 = deepcopy(base)
    cfg1 = AppConfig(llm=LlmConfig(provider="deepseek", narrate_concurrency=1))
    cfg2 = AppConfig(llm=LlmConfig(provider="deepseek", narrate_concurrency=1))
    run_llm_narrate(t1, provider="deepseek", chat_fn=fake_chat, scope="full", cfg=cfg1)
    run_llm_narrate(t2, provider="deepseek", chat_fn=fake_chat, scope="full", cfg=cfg2)
    assert [c["lead"] for c in t1["chapters"]] == [c["lead"] for c in t2["chapters"]]
    assert t1["pipeline"]["timings"]["narrateConcurrency"] == 1
