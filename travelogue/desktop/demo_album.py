"""Bundled Studio demo album (M11-2)."""

from __future__ import annotations

from pathlib import Path

from travelogue.demo.build import DemoError
from travelogue.desktop.bundle import bundle_root
from travelogue.paths import DEMO_ALBUM_SENTINEL, is_demo_album_path

DEMO_ALBUM_REL = Path("templates") / "studio" / "assets" / "demo-album"
# PMX D1 · 示例册读者面展示名（禁止「示例游记」）
DEMO_ALBUM_DISPLAY_TITLE = "斯里兰卡见闻录"

__all__ = [
    "DEMO_ALBUM_DISPLAY_TITLE",
    "DEMO_ALBUM_REL",
    "DEMO_ALBUM_SENTINEL",
    "is_demo_album_path",
    "resolve_demo_album_dir",
]


def resolve_demo_album_dir() -> Path:
    album = (bundle_root() / DEMO_ALBUM_REL).resolve()
    if not album.is_dir():
        raise DemoError("E_DEMO_NOT_DIR", f"demo album missing: {album}")
    jpgs = list(album.glob("*.jpg")) + list(album.glob("*.jpeg"))
    if len(jpgs) < 4:
        raise DemoError("E_DEMO_TOO_FEW", f"demo album too few photos: {album}")
    return album

