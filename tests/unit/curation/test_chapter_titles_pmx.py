"""SFP D-SFP-01 · 同日章名：时段 → segment → 同名日期；禁止 ·二/·三 与（N）。"""

from travelogue.curation.chapter_titles import (
    _same_day_followup_title,
    chapter_titles,
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
    # SNR · 无地点时日期±时段优先于裸日期
    assert titles[0] in {"5月27日", "5月27日 · 上午"}
    assert all("（" not in t and "）" not in t for t in titles)
    assert all("·二" not in t and "·三" not in t for t in titles)
    # 后续仍以日期族起步；撞车后允许同名
    assert titles[1].startswith("5月27日")


def test_strip_ordinal_face_title() -> None:
    assert strip_ordinal_face_title("5月27日 · 三") == "5月27日"
    assert strip_ordinal_face_title("4月2日 ·二") == "4月2日"
    assert strip_ordinal_face_title("5月27日 · 晚上") == "5月27日 · 晚上"
