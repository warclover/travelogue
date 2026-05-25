"""Narrate rule-stub tests."""

from __future__ import annotations

import copy

from travelogue.services.narrate import BANNED_PHRASES, _manifest_limits, run_narrate


def _sample_trip() -> dict:
    return {
        "meta": {
            "title": "雨后京都",
            "dateStart": "2025-04-02",
            "dateEnd": "2025-04-06",
            "places": ["京都"],
            "tone": "relaxed",
        },
        "assets": [
            {"id": "a1", "type": "image", "place": {"city": "京都"}},
            {"id": "a2", "type": "image", "place": {"city": "祇园"}},
            {"id": "a3", "type": "image", "place": {"city": "京都"}},
            {"id": "a4", "type": "image", "place": {"city": "岚山"}},
        ],
        "chapters": [
            {
                "index": 1,
                "title": "4月2日",
                "lead": "",
                "items": [{"type": "media-card", "assetId": "a1"}],
            },
            {
                "index": 2,
                "title": "4月3日",
                "lead": "",
                "items": [
                    {"type": "media-card", "assetId": "a2"},
                    {"type": "media-card", "assetId": "a3"},
                ],
            },
            {
                "index": 3,
                "title": "尾声",
                "lead": "",
                "items": [{"type": "media-card", "assetId": "a4"}],
            },
        ],
        "pipeline": {"status": "structure_locked", "locks": {"structure": True, "copy": False}},
    }


def test_narrate_fills_hook_leads_epilogue() -> None:
    trip = _sample_trip()
    result = run_narrate(trip, tone="relaxed", provider="stub")
    assert "meta.hook" in result.fields_updated
    assert trip["meta"]["hook"]
    assert "京都" in trip["meta"]["hook"]
    assert all(ch["lead"] for ch in trip["chapters"])
    assert trip.get("epilogue")
    assert trip["pipeline"]["status"] == "copy_draft"


def test_narrate_respects_edited_chapter() -> None:
    trip = _sample_trip()
    trip["chapters"][0]["edited"] = True
    trip["chapters"][0]["lead"] = "用户写的导语"
    run_narrate(trip, provider="stub")
    assert trip["chapters"][0]["lead"] == "用户写的导语"


def test_narrate_documentary_tone_differs() -> None:
    trip = _sample_trip()
    run_narrate(trip, tone="documentary", provider="stub")
    doc_hook = trip["meta"]["hook"]
    trip2 = _sample_trip()
    run_narrate(trip2, tone="relaxed", provider="stub")
    assert doc_hook != trip2["meta"]["hook"]


def test_narrate_uses_voice_excerpt() -> None:
    trip = _sample_trip()
    trip["assets"][1]["voice"] = {
        "transcriptPreview": "雨太大了先回酒店",
        "transcript": "雨太大了我们先回酒店。",
    }
    run_narrate(trip, provider="stub")
    assert "雨太大了" in trip["chapters"][1]["lead"]


def test_narrate_lead_does_not_repeat_title_place() -> None:
    trip = _sample_trip()
    trip["meta"]["places"] = ["林芝"]
    trip["chapters"][1]["title"] = "5月–6月·林芝·2"
    trip["chapters"][1]["lead"] = ""
    run_narrate(trip, provider="stub")
    lead = trip["chapters"][1]["lead"]
    assert lead
    assert not lead.startswith(trip["chapters"][1]["title"])
    assert lead != f"{trip['chapters'][1]['title']}，林芝。"


def test_narrate_regenerate_overwrites_existing_lead() -> None:
    trip = _sample_trip()
    trip["chapters"][1]["title"] = "5月–6月·林芝·2"
    trip["chapters"][1]["lead"] = "5月–6月·林芝·2，林芝。"
    run_narrate(trip, provider="stub", regenerate=True)
    lead = trip["chapters"][1]["lead"]
    assert lead != "5月–6月·林芝·2，林芝。"
    assert not lead.startswith("5月–6月·林芝·2")


def test_narrate_dry_run_no_mutation() -> None:
    trip = _sample_trip()
    before = copy.deepcopy(trip)
    result = run_narrate(trip, dry_run=True, provider="stub")
    assert result.fields_updated
    assert trip == before


def test_narrate_respects_manifest_char_limits() -> None:
    trip = _sample_trip()
    run_narrate(trip, provider="stub")
    lim = _manifest_limits()
    assert len(trip["meta"]["hook"]) <= lim["hookMaxChars"]
    for ch in trip["chapters"]:
        assert len(ch["lead"]) <= lim["chapterLeadMaxChars"]
    if trip.get("epilogue"):
        assert len(trip["epilogue"]) <= lim["epilogueMaxChars"]


def test_narrate_strips_banned_phrases() -> None:
    from travelogue.services.narrate import _finalize_copy

    raw = "综上所述值得一提的是京都旅途。"
    hook = _finalize_copy(raw, 56)
    for phrase in BANNED_PHRASES:
        assert phrase not in hook
    assert "京都" in hook


def test_narrate_unique_leads_per_chapter() -> None:
    trip = _sample_trip()
    for ch in trip["chapters"]:
        ch["title"] = "4月2日"
    run_narrate(trip, provider="stub")
    leads = [ch["lead"] for ch in trip["chapters"]]
    assert len(leads) == len(set(leads))
