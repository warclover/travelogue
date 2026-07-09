"""Disk cache for LLM narrate responses."""

from __future__ import annotations

import json

from travelogue.llm.narrate_cache import brief_hash, cache_file, read_cached, write_cached


def test_brief_hash_stable_and_order_independent() -> None:
    a = {"scope": "full", "tripId": "t1", "chapters": ["ch-01"]}
    b = {"chapters": ["ch-01"], "scope": "full", "tripId": "t1"}
    assert brief_hash(a) == brief_hash(b)
    assert len(brief_hash(a)) == 16


def test_narrate_cache_roundtrip(tmp_path) -> None:
    brief = {"tripId": "demo", "scope": "chapter", "chapterId": "ch-01"}
    payload = {"lead": "导语", "items": []}
    write_cached(
        tmp_path,
        provider="stub",
        model="test",
        scope="chapter/ch-01",
        brief=brief,
        payload=payload,
    )
    path = cache_file(
        tmp_path,
        provider="stub",
        model="test",
        scope="chapter/ch-01",
        brief=brief,
    )
    assert path.is_file()
    assert read_cached(
        tmp_path,
        provider="stub",
        model="test",
        scope="chapter/ch-01",
        brief=brief,
    ) == payload


def test_narrate_cache_miss_on_corrupt_file(tmp_path) -> None:
    brief = {"tripId": "demo"}
    path = cache_file(tmp_path, provider="stub", model="m", scope="full", brief=brief)
    path.parent.mkdir(parents=True)
    path.write_text("not json", encoding="utf-8")
    assert read_cached(tmp_path, provider="stub", model="m", scope="full", brief=brief) is None


def test_narrate_cache_miss_on_non_dict(tmp_path) -> None:
    brief = {"tripId": "demo"}
    path = cache_file(tmp_path, provider="stub", model="m", scope="full", brief=brief)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(["array"]), encoding="utf-8")
    assert read_cached(tmp_path, provider="stub", model="m", scope="full", brief=brief) is None
