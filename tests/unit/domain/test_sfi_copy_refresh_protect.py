"""QA-SFI-04 · 刷新手改保护（FX-SFI-05 / BE-SFI-06）。"""

from __future__ import annotations

from travelogue.curation.chapter_titles import refresh_chapter_titles_on_trip
from travelogue.domain.copy_origin import ORIGIN_USER, mark_origin
from travelogue.services.narrate import run_narrate
from travelogue.web.copy_patch import apply_copy_patch


def _mini_trip() -> dict:
    return {
        "tripId": "fixture-sfi-refresh",
        "meta": {
            "title": "手改杂志名",
            "displayTitle": "手改杂志名",
            "hook": "旧 hook",
            "hookOrigin": "stub",
            "dateStart": "2024-05-01",
            "dateEnd": "2024-05-03",
            "places": ["京都"],
            "tone": "relaxed",
        },
        "assets": [
            {
                "id": f"a{i}",
                "takenAt": f"2024-05-0{i}T12:00:00Z",
                "layoutEligible": True,
                "width": 1200,
                "height": 800,
                "type": "photo",
                "mediaClass": "photo",
                "caption": f"stub 图说{i}",
                "captionOrigin": "stub",
            }
            for i in range(1, 5)
        ],
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "patternId": "open",
                "title": "抵达",
                "lead": "用户手改开头",
                "leadOrigin": ORIGIN_USER,
                "items": [{"type": "media-card", "assetId": "a1"}],
                "curation": {"daySpan": ["2024-05-01"]},
            },
            {
                "id": "ch-02",
                "index": 2,
                "patternId": "close",
                "title": "尾声",
                "lead": "stub 导语",
                "leadOrigin": "stub",
                "items": [{"type": "media-card", "assetId": "a2"}],
                "curation": {"daySpan": ["2024-05-02"]},
            },
            {
                "id": "ch-appendix",
                "index": 3,
                "patternId": "gallery",
                "title": "往年 · 旧照 · 2 张",
                "lead": "",
                "items": [
                    {"type": "media-card", "assetId": "a3"},
                    {"type": "media-card", "assetId": "a4"},
                ],
                "curation": {
                    "isAppendix": True,
                    "appendixAssetIds": ["a3", "a4"],
                },
            },
        ],
        "curation": {},
        "pipeline": {"status": "draft"},
    }


def test_user_lead_survives_regenerate() -> None:
    trip = _mini_trip()
    run_narrate(trip, provider="stub", regenerate=True, scope="frame")
    assert trip["chapters"][0]["lead"] == "用户手改开头"
    assert trip["chapters"][0]["leadOrigin"] == ORIGIN_USER


def test_meta_title_hand_edit_survives_refresh() -> None:
    trip = _mini_trip()
    apply_copy_patch(trip, "meta.title", "我改的名字")
    run_narrate(trip, provider="stub", regenerate=True, scope="frame")
    assert trip["meta"]["title"] == "我改的名字"


def test_appendix_title_not_rewritten_by_cn() -> None:
    trip = _mini_trip()
    frozen = trip["chapters"][2]["title"]
    updated = refresh_chapter_titles_on_trip(trip)
    assert trip["chapters"][2]["title"] == frozen
    assert not any("appendix" in u for u in updated)


def test_user_title_origin_protected() -> None:
    trip = _mini_trip()
    mark_origin(trip["chapters"][1], "titleOrigin")
    trip["chapters"][1]["title"] = "我的章名"
    refresh_chapter_titles_on_trip(trip)
    assert trip["chapters"][1]["title"] == "我的章名"
