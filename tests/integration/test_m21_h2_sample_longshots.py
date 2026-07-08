"""P5-H2 · sample longshot thumb assets (shared by v2 demo constants)."""



from __future__ import annotations
from tests._repo_root import repo_root

from pathlib import Path


def test_sample_longshot_thumb_assets_exist() -> None:
    root = repo_root(__file__) / "templates" / "studio" / "assets"
    assert (root / "sample-longshot.jpg").is_file()
    for key in ("kyoto", "iceland", "linzhi"):
        thumb = root / "sample-longshots" / f"{key}-thumb.jpg"
        assert thumb.is_file(), thumb
        assert thumb.stat().st_size > 1024


def test_constants_sample_thumbs_wired() -> None:
    js = (
        repo_root(__file__)
        / "templates"
        / "studio"
        / "js"
        / "constants.js"
    ).read_text(encoding="utf-8")
    assert "thumbSrc:" in js
    assert "sample-longshots/kyoto-thumb.jpg" in js
    assert "sample-longshots/iceland-thumb.jpg" in js
    assert "sample-longshots/linzhi-thumb.jpg" in js
