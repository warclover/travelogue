from travelogue.render.screen_tone import chapter_separator_style


def test_chapter_separator_style_uses_dark_ink_on_light_tone() -> None:
    style = chapter_separator_style({"r": 232, "g": 228, "b": 223})
    assert "background: #e8e4df;" in style
    assert "--chapter-separator-ink: #1f1d1a;" in style
    assert "--chapter-separator-overlay-end: rgba(14, 18, 24, 0.08);" in style
    assert "--chapter-separator-title-shadow: none;" in style


def test_chapter_separator_style_uses_light_ink_on_dark_tone() -> None:
    style = chapter_separator_style({"r": 34, "g": 40, "b": 50})
    assert "background: #222832;" in style
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
