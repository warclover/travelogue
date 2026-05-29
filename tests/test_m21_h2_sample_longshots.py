"""P5-H2 · sample longshot thumbs on empty-state gallery."""

from __future__ import annotations

from pathlib import Path

from tests._studio_js import read_studio_js


def test_sample_longshot_thumb_assets_exist() -> None:
    root = Path(__file__).resolve().parents[1] / "templates" / "studio" / "assets"
    assert (root / "sample-longshot.jpg").is_file()
    for key in ("kyoto", "iceland", "linzhi"):
        thumb = root / "sample-longshots" / f"{key}-thumb.jpg"
        assert thumb.is_file(), thumb
        assert thumb.stat().st_size > 1024


def test_studio_js_uses_real_sample_thumbs() -> None:
    js = read_studio_js()
    assert "thumbSrc:" in js
    assert "buildSampleThumb" in js
    assert "sample-longshots/kyoto-thumb.jpg" in js
