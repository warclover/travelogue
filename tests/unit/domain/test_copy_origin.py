"""BE-SFI-00 · field-level copy origin."""

from __future__ import annotations

from travelogue.domain.copy_origin import (
    ORIGIN_USER,
    is_user_protected,
    mark_origin,
    migrate_edited_to_origin,
)
from travelogue.web.copy_patch import apply_copy_patch


def test_mark_origin_sets_user_and_edited() -> None:
    ch: dict = {}
    mark_origin(ch, "leadOrigin")
    assert ch["leadOrigin"] == ORIGIN_USER
    assert ch["edited"] is True
    assert is_user_protected(ch, "leadOrigin")


def test_migrate_edited_to_origin() -> None:
    trip = {
        "meta": {"edited": True, "hook": "手改开头"},
        "epilogue": "手改结尾",
        "chapters": [
            {
                "id": "c1",
                "edited": True,
                "title": "手改章",
                "lead": "手改导语",
                "items": [],
            }
        ],
        "assets": [],
    }
    touched = migrate_edited_to_origin(trip)
    assert "meta.hookOrigin" in touched
    assert trip["meta"]["hookOrigin"] == ORIGIN_USER
    assert trip["epilogueOrigin"] == ORIGIN_USER
    assert trip["chapters"][0]["leadOrigin"] == ORIGIN_USER
    assert trip["chapters"][0]["titleOrigin"] == ORIGIN_USER


def test_copy_patch_sets_field_origin() -> None:
    trip = {
        "meta": {"title": "t", "dateStart": "2024-01-01", "dateEnd": "2024-01-02", "places": ["x"], "tone": "relaxed"},
        "chapters": [{"id": "c1", "index": 1, "patternId": "open", "title": "旧", "items": []}],
        "assets": [],
    }
    apply_copy_patch(trip, "chapters.c1.lead", "新的开头一句")
    assert trip["chapters"][0]["leadOrigin"] == ORIGIN_USER
    apply_copy_patch(trip, "chapters.c1.title", "新章名")
    assert trip["chapters"][0]["titleOrigin"] == ORIGIN_USER
