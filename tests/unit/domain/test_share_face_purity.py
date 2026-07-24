"""Share-Face Purity · W0–W1 unit contracts."""

from __future__ import annotations

from travelogue.curation.bucket_planning import merge_weak_same_day_followups
from travelogue.domain.share_face_purity import (
    migrate_ordinal_chapter_titles,
    migrate_share_face_purity_on_open,
    sort_chapters_by_temporal_key,
    suppress_repeated_weak_captions,
)
from travelogue.domain.title_humanize import migrate_stale_display_title
from travelogue.services.narrative_validate import validate_narrative


def test_migrate_ordinal_skips_user_title() -> None:
    trip = {
        "chapters": [
            {"id": "c1", "title": "5月27日 · 三", "titleOrigin": "user"},
            {"id": "c2", "title": "5月27日 · 二"},
        ]
    }
    updated = migrate_ordinal_chapter_titles(trip)
    assert "c1" not in updated
    assert trip["chapters"][0]["title"] == "5月27日 · 三"
    assert "c2" in updated
    assert trip["chapters"][1]["title"] == "5月27日"


def test_open_migrate_display_and_ordinal() -> None:
    trip = {
        "meta": {
            "title": "武大樱花",
            "displayTitle": "旅行 · 24 1 20–25 1 16",
            "places": ["武汉"],
        },
        "chapters": [{"id": "c1", "title": "5月27日 · 三"}],
    }
    result = migrate_share_face_purity_on_open(trip)
    assert result["changed"] is True
    assert trip["meta"]["displayTitle"] == "武大樱花"
    assert trip["chapters"][0]["title"] == "5月27日"


def test_migrate_display_skips_title_origin_user() -> None:
    meta = {
        "title": "武大樱花",
        "displayTitle": "旅行 · 24 1 20–25 1 16",
        "titleOrigin": "user",
        "places": ["武汉"],
    }
    assert migrate_stale_display_title(meta) is False
    assert meta["displayTitle"] == "旅行 · 24 1 20–25 1 16"


def test_narrative_validate_bans_ordinal_title() -> None:
    issues = validate_narrative({"chapters": [{"title": "5月27日 · 三", "items": []}]})
    assert any("ordinal chapter title" in msg for msg in issues)


def test_sort_chapters_by_temporal_key() -> None:
    assets = [
        {"id": "a", "takenAt": "2025-08-01T10:00:00"},
        {"id": "b", "takenAt": "2025-01-15T10:00:00"},
        {"id": "c", "takenAt": "2024-12-01T10:00:00"},
    ]
    chapters = [
        {"id": "aug", "items": [{"type": "media-card", "assetId": "a"}]},
        {"id": "jan", "items": [{"type": "media-card", "assetId": "b"}]},
        {
            "id": "app",
            "curation": {"isAppendix": True},
            "items": [{"type": "media-card", "assetId": "c"}],
        },
    ]
    sorted_chs, reordered = sort_chapters_by_temporal_key(chapters, assets)
    assert reordered is True
    assert [c["id"] for c in sorted_chs] == ["jan", "aug", "app"]


def test_suppress_repeated_weak_captions() -> None:
    caps = {"a": "黄昏", "b": "黄昏", "c": "黄昏", "d": "京都"}
    out = suppress_repeated_weak_captions(caps, max_same=3)
    assert out["a"] == out["b"] == out["c"] == ""
    assert out["d"] == "京都"


def test_merge_weak_same_day_followups() -> None:
    assets = {
        "a": {"id": "a", "takenAt": "2026-05-27T10:00:00"},
        "b": {"id": "b", "takenAt": "2026-05-27T10:30:00"},
        "c": {"id": "c", "takenAt": "2026-05-27T11:00:00"},
        "d": {"id": "d", "takenAt": "2026-05-27T19:00:00"},
    }
    # Same morning daypart · tiny follow-up → merge
    out, _, _ = merge_weak_same_day_followups(
        [["a", "b"], ["c"]],
        ["", ""],
        [[], []],
        assets_by_id=assets,
    )
    assert len(out) == 1
    assert set(out[0]) == {"a", "b", "c"}
    # Distinct evening daypart · keep
    out2, _, _ = merge_weak_same_day_followups(
        [["a", "b"], ["d"]],
        ["", ""],
        [[], []],
        assets_by_id=assets,
    )
    assert len(out2) == 2
