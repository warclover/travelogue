"""screen_tone should not emit Pillow getdata deprecation."""

from __future__ import annotations

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
