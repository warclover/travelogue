"""M10 stub captions (F-NAR-P2-04) and hook templates (F-NAR-P2-02)."""

from __future__ import annotations

from travelogue.services.narrate import run_narrate
from travelogue.services.narrative_scope import SCOPE_FRAME


def _sample_trip() -> dict:
    return {
        "meta": {
            "title": "雨后京都",
            "dateStart": "2025-04-02",
            "dateEnd": "2025-04-06",
            "places": ["京都"],
            "tone": "relaxed",
        },
        "coverAssetId": "a1",
        "assets": [
            {
                "id": "a1",
                "type": "image",
                "place": {"city": "京都"},
                "aspectKind": "portrait",
                "takenAt": "2025-04-02T10:00:00Z",
            },
            {
                "id": "a2",
                "type": "image",
                "place": {"city": "祇园"},
                "aspectKind": "landscape",
                "takenAt": "2025-04-03T15:00:00Z",
            },
            {
                "id": "a3",
                "type": "image",
                "place": {"city": "岚山"},
                "aspectKind": "square",
            },
        ],
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "title": "4月2日",
                "items": [{"type": "media-card", "assetId": "a1"}],
            },
            {
                "id": "ch-02",
                "index": 2,
                "title": "4月3日",
                "items": [
                    {"type": "media-card", "assetId": "a2"},
                    {"type": "media-card", "assetId": "a3"},
                ],
            },
        ],
        "pipeline": {"status": "structure_locked", "locks": {"structure": True, "copy": False}},
    }


def test_stub_writes_cover_and_chapter_captions() -> None:
    trip = _sample_trip()
    result = run_narrate(trip, provider="stub", scope=SCOPE_FRAME, regenerate=True)
    assert any("assets.a1.caption" == f for f in result.fields_updated)
    assert any(f.startswith("assets.a2.caption") for f in result.fields_updated)
    assert trip["assets"][0].get("caption")
    assert trip["assets"][1].get("caption")


def test_stub_hook_uses_day_template() -> None:
    trip = _sample_trip()
    run_narrate(trip, provider="stub", scope=SCOPE_FRAME, regenerate=True)
    hook = trip["meta"]["hook"]
    assert "京都" in hook
    assert "天" in hook or "帧" in hook or "翻" in hook
