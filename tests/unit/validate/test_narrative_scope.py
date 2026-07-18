"""Narrative scope: frame vs full copy generation."""

from __future__ import annotations

import pytest

from travelogue.services.llm_narrate import run_llm_narrate
from travelogue.services.narrate import run_narrate
from travelogue.services.narrative_scope import (
    SCOPE_FRAME,
    SCOPE_FRAME_CHAPTERS,
    SCOPE_FULL,
    apply_scope_cleanup,
    chapter_lead_allowed,
)


def _sample_trip() -> dict:
    return {
        "tripId": "scope-test",
        "meta": {
            "title": "雨后京都",
            "dateStart": "2025-04-02",
            "dateEnd": "2025-04-06",
            "places": ["京都"],
            "tone": "relaxed",
            "hook": "",
        },
        "assets": [
            {"id": "a1", "type": "image", "place": {"city": "京都"}, "caption": "旧图注1"},
            {"id": "a2", "type": "image", "place": {"city": "祇园"}, "caption": "旧图注2"},
            {"id": "a3", "type": "image", "place": {"city": "岚山"}},
        ],
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "title": "4月2日",
                "lead": "旧导语1",
                "items": [{"type": "media-card", "assetId": "a1", "caption": "旧图注1"}],
            },
            {
                "id": "ch-02",
                "index": 2,
                "title": "4月3日",
                "lead": "旧导语2",
                "items": [{"type": "media-card", "assetId": "a2", "caption": "旧图注2"}],
            },
            {
                "id": "ch-03",
                "index": 3,
                "title": "尾声",
                "lead": "旧导语3",
                "items": [{"type": "media-card", "assetId": "a3"}],
            },
        ],
        "epilogue": "旧尾声",
        "pipeline": {"status": "structure_locked", "locks": {"structure": True, "copy": False}},
    }


def test_chapter_lead_allowed_by_scope() -> None:
    trip = _sample_trip()
    chapters = trip["chapters"]
    assert chapter_lead_allowed(chapters[0], chapters, SCOPE_FRAME) is False
    assert chapter_lead_allowed(chapters[1], chapters, SCOPE_FRAME) is False
    assert chapter_lead_allowed(chapters[0], chapters, SCOPE_FRAME_CHAPTERS) is True
    assert chapter_lead_allowed(chapters[1], chapters, SCOPE_FRAME_CHAPTERS) is False
    assert chapter_lead_allowed(chapters[2], chapters, SCOPE_FRAME_CHAPTERS) is True
    assert all(chapter_lead_allowed(ch, chapters, SCOPE_FULL) for ch in chapters)


def test_chapter_lead_allowed_uses_min_max_index_not_hardcoded_one() -> None:
    chapters = [
        {"id": "ch-a", "index": 2},
        {"id": "ch-b", "index": 5},
        {"id": "ch-c", "index": 7},
    ]
    assert chapter_lead_allowed(chapters[0], chapters, SCOPE_FRAME_CHAPTERS) is True
    assert chapter_lead_allowed(chapters[1], chapters, SCOPE_FRAME_CHAPTERS) is False
    assert chapter_lead_allowed(chapters[2], chapters, SCOPE_FRAME_CHAPTERS) is True


def test_narrate_chapter_id_rejected_when_out_of_scope() -> None:
    from travelogue.services.narrate import NarrateError

    trip = _sample_trip()
    with pytest.raises(NarrateError) as exc:
        run_narrate(trip, provider="stub", chapter_id="ch-02", scope=SCOPE_FRAME)
    assert exc.value.code == "E_NARRATE_SCOPE"


def test_apply_scope_cleanup_clears_middle_copy() -> None:
    trip = _sample_trip()
    cleared = apply_scope_cleanup(trip, SCOPE_FRAME)
    assert any("chapters.ch-02.lead" in c for c in cleared)
    assert not trip["chapters"][1].get("lead")
    assert not trip["chapters"][0].get("lead")
    assert trip["assets"][0].get("skipCaption") is True
    assert not trip["assets"][0].get("caption")


def test_narrate_frame_stub_only_hook_epilogue() -> None:
    trip = _sample_trip()
    result = run_narrate(trip, provider="stub", scope=SCOPE_FRAME, regenerate=True)
    assert "meta.hook" in result.fields_updated
    assert "epilogue" in result.fields_updated
    assert not any("lead" in f for f in result.fields_updated)
    assert trip["meta"]["hook"]
    # BE-FST-03 · stub still touches epilogue field but leaves it empty
    assert not (trip.get("epilogue") or "").strip()
    assert not trip["chapters"][0].get("lead")
    assert not trip["chapters"][1].get("lead")
    assert not trip["chapters"][2].get("lead")
    assert trip["curation"]["narrativeScope"] == SCOPE_FRAME


def test_narrate_frame_chapters_stub_first_last_lead() -> None:
    trip = _sample_trip()
    run_narrate(trip, provider="stub", scope=SCOPE_FRAME_CHAPTERS, regenerate=True)
    assert trip["chapters"][0].get("lead")
    assert not trip["chapters"][1].get("lead")
    assert trip["chapters"][2].get("lead")


def test_llm_narrate_frame_skips_chapter_calls() -> None:
    import json

    trip = _sample_trip()
    calls: list[str] = []

    def fake_chat(messages: list[dict[str, str]]) -> str:
        user = messages[-1]["content"]
        calls.append(user)
        if "meta 文案" in user:
            return json.dumps(
                {"meta": {"hook": "frame hook。"}, "epilogue": "frame 尾声。"},
                ensure_ascii=False,
            )
        pytest.fail(f"unexpected chapter prompt under frame scope: {user[:200]}")

    apply_scope_cleanup(trip, SCOPE_FRAME)
    run_llm_narrate(trip, provider="deepseek", chat_fn=fake_chat, scope=SCOPE_FRAME, regenerate=True)
    assert len(calls) == 1
    assert trip["meta"]["hook"] == "frame hook。"
    assert not trip["chapters"][0].get("lead")


def test_narrate_full_preserves_legacy_behavior() -> None:
    trip = _sample_trip()
    for ch in trip["chapters"]:
        ch["lead"] = ""
    for asset in trip["assets"]:
        asset.pop("caption", None)
    run_narrate(trip, provider="stub", scope=SCOPE_FULL)
    assert all(ch.get("lead") for ch in trip["chapters"])
    assert trip["meta"]["hook"]
    assert trip.get("epilogue")


def test_resolve_cover_show_title_frame_hides_place_name() -> None:
    from travelogue.services.narrative_scope import resolve_cover_show_title

    trip = _sample_trip()
    trip["meta"]["title"] = "大理"
    trip["meta"]["places"] = ["大理"]
    trip.setdefault("curation", {})["narrativeScope"] = SCOPE_FRAME
    assert resolve_cover_show_title(trip) is False


def test_resolve_cover_show_title_frame_hides_custom_title() -> None:
    from travelogue.services.narrative_scope import resolve_cover_show_title

    trip = _sample_trip()
    trip["meta"]["title"] = "雨后京都"
    trip["meta"]["places"] = ["京都"]
    trip.setdefault("curation", {})["narrativeScope"] = SCOPE_FRAME
    assert resolve_cover_show_title(trip) is False


def test_resolve_cover_show_title_full_always_shows() -> None:
    from travelogue.services.narrative_scope import resolve_cover_show_title

    trip = _sample_trip()
    trip["meta"]["title"] = "大理"
    trip["meta"]["places"] = ["大理"]
    trip.setdefault("curation", {})["narrativeScope"] = SCOPE_FULL
    assert resolve_cover_show_title(trip) is True
