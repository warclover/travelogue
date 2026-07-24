"""Share-Face Purity · W0–W1 unit contracts."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.curation.bucket_planning import merge_weak_same_day_followups
from travelogue.domain.share_face_copy import is_unsafe_share_copy
from travelogue.domain.share_face_purity import (
    enforce_no_ordinal_face_titles,
    migrate_ordinal_chapter_titles,
    migrate_share_face_purity_on_open,
    sort_chapters_by_temporal_key,
    suppress_repeated_weak_captions,
)
from travelogue.domain.studio_events import ALLOWED_STUDIO_HOMEPAGE_EVENTS
from travelogue.domain.title_humanize import migrate_stale_display_title
from travelogue.services.narrative_validate import validate_narrative

ROOT = Path(__file__).resolve().parents[3]
SFP_FIXTURE = ROOT / "schemas" / "fixtures" / "trip.sfp_same_day_dirty_title.json"

SFP_EVENTS = (
    "sfp_chapter_title_sequence_pass",
    "sfp_display_title_migrated",
    "sfp_caption_echo_suppressed",
    "sfp_chapter_time_sort_applied",
    "sfp_xhs_copy_pack_copied",
)


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


def test_sfp_events_in_homepage_allowlist() -> None:
    for ev in SFP_EVENTS:
        assert ev in ALLOWED_STUDIO_HOMEPAGE_EVENTS, ev


def test_enforce_no_ordinal_face_titles() -> None:
    trip = {"chapters": [{"id": "c1", "title": "樱花 · 二"}]}
    updated = enforce_no_ordinal_face_titles(trip)
    assert updated == ["c1"]
    assert trip["chapters"][0]["title"] == "樱花"


def test_sfp_fixture_covers_dirty_ordinal_echo_and_order() -> None:
    """QA-SFP-08 · schemas fixture 一册覆盖同日序号 / 点号脏题名 / 回声 / 乱序。"""
    trip = json.loads(SFP_FIXTURE.read_text(encoding="utf-8"))
    assert any("· 三" in str(ch.get("title") or "") for ch in trip["chapters"])
    assert "24.1.20" in str(trip["meta"].get("displayTitle") or "")
    cap = trip["chapters"][0]["items"][0]["caption"]
    assert is_unsafe_share_copy(cap, title=trip["meta"]["title"], kind="caption")
    result = migrate_share_face_purity_on_open(trip)
    assert result["changed"] is True
    assert trip["meta"]["displayTitle"] == "夏睿彤年度精选"
    assert not any(
        "· 三" in str(ch.get("title") or "") or "·三" in str(ch.get("title") or "")
        for ch in trip["chapters"]
    )
    # 跨年补年后序仍保持 fixture 章序；时间 SSOT 由 sort 另测
    assert all("年" in str(ch.get("title") or "") for ch in trip["chapters"])
    sorted_chs, reordered = sort_chapters_by_temporal_key(
        trip["chapters"], trip["assets"]
    )
    assert reordered is True
    assert [c["id"] for c in sorted_chs] == ["ch-may-1", "ch-may-2", "ch-aug", "ch-jan"]


def test_open_migrate_dotted_display_and_cross_year_chapter() -> None:
    """D-SFP-04/08 · 点号脏题名软剥 + 跨年章名补年。"""
    trip = {
        "meta": {
            "title": "夏睿彤年度精选2",
            "displayTitle": "旅行 · 24.1.20–25.1.16",
            "places": ["武汉"],
            "dateStart": "2024-01-20",
            "dateEnd": "2025-01-16",
        },
        "assets": [
            {"id": "a", "takenAt": "2024-08-14T10:00:00"},
            {"id": "b", "takenAt": "2025-01-16T10:00:00"},
        ],
        "chapters": [
            {"id": "c1", "title": "8月14日", "items": [{"type": "media-card", "assetId": "a"}]},
            {"id": "c2", "title": "1月16日", "items": [{"type": "media-card", "assetId": "b"}]},
        ],
    }
    result = migrate_share_face_purity_on_open(trip)
    assert result["changed"] is True
    assert trip["meta"]["displayTitle"] == "夏睿彤年度精选"
    assert trip["chapters"][0]["title"] == "2024年8月14日"
    assert trip["chapters"][1]["title"] == "2025年1月16日"


def test_merge_weak_same_day_followups() -> None:
    assets = {
        "a": {"id": "a", "takenAt": "2026-05-27T10:00:00"},
        "b": {"id": "b", "takenAt": "2026-05-27T10:30:00"},
        "c": {"id": "c", "takenAt": "2026-05-27T11:00:00"},
        "d": {"id": "d", "takenAt": "2026-05-27T19:00:00"},
    }
    # Same morning daypart · tiny follow-up → merge
    out, _, _, merges = merge_weak_same_day_followups(
        [["a", "b"], ["c"]],
        ["", ""],
        [[], []],
        assets_by_id=assets,
    )
    assert len(out) == 1
    assert set(out[0]) == {"a", "b", "c"}
    assert merges == 1
    # Distinct evening daypart · keep
    out2, _, _, merges2 = merge_weak_same_day_followups(
        [["a", "b"], ["d"]],
        ["", ""],
        [[], []],
        assets_by_id=assets,
    )
    assert len(out2) == 2
    assert merges2 == 0
