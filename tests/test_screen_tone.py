from travelogue.render.screen_tone import (
    build_chapter_separator_ticket,
    chapter_progress_dots,
    chapter_separator_style,
)


def test_chapter_progress_dots_fills_through_current() -> None:
    dots = chapter_progress_dots(3, 5)
    assert [d["active"] for d in dots] == [True, True, True, False, False]


def test_build_chapter_separator_ticket_meta_from_place_and_decor() -> None:
    ticket = build_chapter_separator_ticket(
        {"decorLine": "夜景"},
        2,
        5,
        meta={"title": "林芝 · 春"},
        divider={"dividerPlace": "林芝"},
    )
    assert ticket["chapterMeta"] == "林芝 · 夜景"
    assert ticket["hasDecorPull"] is False
    assert ticket["chapterProgressLabel"] == "02 / 05"


def test_build_chapter_separator_ticket_pull_for_long_decor() -> None:
    ticket = build_chapter_separator_ticket(
        {"decorLine": "夜景比白天安静。"},
        3,
        5,
        meta={"title": "林芝"},
        divider={"dividerPlace": "林芝"},
    )
    assert ticket["chapterMeta"] == "林芝"
    assert ticket["hasDecorPull"] is True
    assert ticket["decorPull"] == "夜景比白天安静。"


def test_chapter_meta_omits_album_title_without_divider_place() -> None:
    """G-LRG-09: no dividerPlace → do not show album meta.title on the ticket stub."""
    ticket = build_chapter_separator_ticket(
        {"decorLine": "夜景"},
        2,
        5,
        meta={"title": "张智慧精选2"},
        divider={},
    )
    assert ticket["chapterMeta"] == "夜景"
    assert "张智慧" not in ticket["chapterMeta"]


def test_chapter_meta_uses_divider_date_when_place_absent() -> None:
    ticket = build_chapter_separator_ticket(
        {},
        2,
        5,
        meta={"title": "雨后京都"},
        divider={"dividerDate": "04.28"},
    )
    assert ticket["chapterMeta"] == "04.28"


def test_chapter_separator_style_uses_dark_ink_on_light_tone() -> None:
    style = chapter_separator_style({"r": 232, "g": 228, "b": 223})
    assert "--chapter-separator-accent: #e8e4df;" in style
    assert "--chapter-separator-mode: light;" in style
    assert "--chapter-separator-ink: #1f1d1a;" in style
    assert "--chapter-separator-overlay-end: rgba(14, 18, 24, 0.08);" in style
    assert "--chapter-separator-title-shadow: none;" in style


def test_chapter_separator_style_uses_light_ink_on_dark_tone() -> None:
    style = chapter_separator_style({"r": 34, "g": 40, "b": 50})
    assert "--chapter-separator-accent: #222832;" in style
    assert "--chapter-separator-mode: dark;" in style
    assert "--chapter-separator-ink: #f5f2ea;" in style
    assert "--chapter-separator-overlay-end: rgba(14, 18, 24, 0.28);" in style
    assert "--chapter-separator-title-shadow: 0 1px 12px rgba(0, 0, 0, 0.22);" in style
"""screen_tone should not emit Pillow getdata deprecation."""

import warnings
from pathlib import Path

from PIL import Image

from travelogue.curation.screen_tone import sample_tone_from_path


def test_screen_tone_no_getdata_deprecation(tmp_path: Path) -> None:
    path = tmp_path / "tone.jpg"
    Image.new("RGB", (64, 64), (90, 110, 130)).save(path)
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        tone = sample_tone_from_path(path)
    assert tone is not None
    assert not any("getdata" in str(w.message).lower() for w in record)
