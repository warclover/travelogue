"""PMX D6 · 同日章名禁止（N），改用 ·二/·三。"""

from travelogue.curation.chapter_titles import _same_day_followup_title, chapter_titles


def test_same_day_followup_prefers_daypart_then_ordinal() -> None:
    used = ["5月27日"]
    assert (
        _same_day_followup_title(
            "5月27日", 1, daypart="晚上", segment_label=None, used=used
        )
        == "5月27日 · 晚上"
    )
    used.append("5月27日 · 晚上")
    assert (
        _same_day_followup_title(
            "5月27日", 2, daypart="晚上", segment_label=None, used=used
        )
        == "5月27日 · 三"
    )


def test_chapter_titles_no_paren_ordinal_for_same_day() -> None:
    assets = [
        {"id": "a", "takenAt": "2026-05-27T10:00:00"},
        {"id": "b", "takenAt": "2026-05-27T10:30:00"},
        {"id": "c", "takenAt": "2026-05-27T11:00:00"},
    ]
    titles = chapter_titles([["a"], ["b"], ["c"]], assets, {"places": ["京都"]})
    assert titles[0] == "5月27日"
    assert all("（" not in t and "）" not in t for t in titles)
    assert titles[1] != titles[0]
    # 同时段撞车 → ·二
    assert "·二" in titles[1] or "上午" in titles[1]
