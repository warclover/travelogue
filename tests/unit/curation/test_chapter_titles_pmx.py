"""SFP D-SFP-01 · 同日章名：时段 → segment → 同名日期；禁止 ·二/·三 与（N）。"""

from travelogue.curation.chapter_titles import (
    _same_day_followup_title,
    chapter_titles,
    scene_short_from_segment_label,
    strip_ordinal_face_title,
)


def test_same_day_followup_prefers_daypart_then_same_date() -> None:
    used = ["5月27日"]
    assert (
        _same_day_followup_title(
            "5月27日", 1, daypart="晚上", segment_label=None, used=used
        )
        == "5月27日 · 晚上"
    )
    used.append("5月27日 · 晚上")
    # 同时段已占用 → 允许与首章同名日期（靠章号区分），不再出 ·三
    assert (
        _same_day_followup_title(
            "5月27日", 2, daypart="晚上", segment_label=None, used=used
        )
        == "5月27日"
    )


def test_chapter_titles_no_paren_or_ordinal_for_same_day() -> None:
    assets = [
        {"id": "a", "takenAt": "2026-05-27T10:00:00"},
        {"id": "b", "takenAt": "2026-05-27T10:30:00"},
        {"id": "c", "takenAt": "2026-05-27T11:00:00"},
    ]
    titles = chapter_titles([["a"], ["b"], ["c"]], assets, {"places": ["京都"]})
    # 有地点时地点±时段优先；日期只作退路
    assert titles[0] in {"京都", "京都 · 上午"}
    assert all("（" not in t and "）" not in t for t in titles)
    assert all("·二" not in t and "·三" not in t for t in titles)
    assert not any(t.startswith("5月27日") for t in titles)


def test_strip_ordinal_face_title() -> None:
    assert strip_ordinal_face_title("5月27日 · 三") == "5月27日"
    assert strip_ordinal_face_title("4月2日 ·二") == "4月2日"
    assert strip_ordinal_face_title("5月27日 · 晚上") == "5月27日 · 晚上"


def test_scene_short_rejects_unauthorized_overseas_place() -> None:
    assert (
        scene_short_from_segment_label(
            "7月22日·京都雨季漫游",
            allowed_places={"斯里兰卡"},
        )
        is None
    )
    assert (
        scene_short_from_segment_label(
            "7月22日·京都雨季漫游",
            allowed_places={"京都"},
        )
        == "京都雨季漫游"
    )


def test_chapter_titles_ignore_polluted_kyoto_segment_on_sri_lanka_trip() -> None:
    assets = [
        {"id": "a1", "takenAt": "2018-07-22T15:00:00"},
        {"id": "a2", "takenAt": "2018-07-22T16:00:00"},
    ]
    titles = chapter_titles(
        [["a1", "a2"]],
        assets,
        {"places": ["斯里兰卡"], "title": "斯里兰卡见闻录"},
        bucket_segment_ids=["seg-01"],
        segment_labels={"seg-01": "7月22日·京都雨季漫游"},
    )
    assert titles
    assert "京都" not in titles[0]
    assert titles[0].startswith("斯里兰卡")


def test_chapter_titles_ordinal_leg_before_bare_date() -> None:
    assets = [
        {"id": "a", "takenAt": "2026-05-27T10:00:00"},
        {"id": "b", "takenAt": "2026-05-27T15:00:00"},
    ]
    titles = chapter_titles([["a"], ["b"]], assets, {})
    assert titles[0] in {"第一程", "第一程 · 上午"}
    assert titles[1] in {"第二程", "第二程 · 下午"}
