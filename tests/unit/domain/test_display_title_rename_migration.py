"""Dogfood UX Fixpack M2 · D2 displayTitle dual-write + stale migration."""

from __future__ import annotations

from travelogue.domain.title_humanize import migrate_stale_display_title, resolve_display_title
from travelogue.services.trip import apply_intent


def test_apply_intent_dual_writes_display_title() -> None:
    trip: dict = {"meta": {"places": ["京都"]}}
    apply_intent(trip, title="雨后京都")
    assert trip["meta"]["title"] == "雨后京都"
    assert trip["meta"]["displayTitle"] == "雨后京都"
    assert resolve_display_title(trip["meta"]) == "雨后京都"


def test_apply_intent_rename_overwrites_stale_display_title() -> None:
    trip: dict = {
        "meta": {
            "title": "旧名残留",
            "displayTitle": "旅行 · 7月1日",
            "places": ["京都"],
            "dateStart": "2026-07-01",
        }
    }
    apply_intent(trip, title="雨后京都")
    assert trip["meta"]["title"] == "雨后京都"
    assert trip["meta"]["displayTitle"] == "雨后京都"
    assert resolve_display_title(trip["meta"]) == "雨后京都"


def test_migrate_stale_display_title_positive() -> None:
    meta = {
        "title": "雨后京都",
        "displayTitle": "旅行 · 7月1日",
        "places": ["京都"],
    }
    assert migrate_stale_display_title(meta) is True
    assert meta["displayTitle"] == "雨后京都"
    assert migrate_stale_display_title(meta) is False  # idempotent


def test_migrate_stale_display_title_rejects_noise_title() -> None:
    meta = {
        "title": "王丹昙华林2",
        "displayTitle": "武汉 · 7月1日",
        "places": ["武汉"],
    }
    assert migrate_stale_display_title(meta) is False
    assert meta["displayTitle"] == "武汉 · 7月1日"


def test_notes_only_save_migrates_stale_display_title() -> None:
    trip: dict = {
        "meta": {
            "title": "雨后京都",
            "displayTitle": "旅行 · 7月1日",
            "places": ["京都"],
        }
    }
    apply_intent(trip, user_notes="带娃慢走")
    assert trip["meta"]["displayTitle"] == "雨后京都"
    assert trip["userNotes"] == "带娃慢走"
