"""Bundled Studio demo album (M11-2)."""

from __future__ import annotations

from pathlib import Path

from travelogue.demo.build import DemoError
from travelogue.desktop.bundle import bundle_root

DEMO_ALBUM_REL = Path("templates") / "studio" / "assets" / "demo-album"
DEMO_ALBUM_SENTINEL = "@bundled/demo-album"


def resolve_demo_album_dir() -> Path:
    album = (bundle_root() / DEMO_ALBUM_REL).resolve()
    if not album.is_dir():
        raise DemoError("E_DEMO_NOT_DIR", f"demo album missing: {album}")
    jpgs = list(album.glob("*.jpg")) + list(album.glob("*.jpeg"))
    if len(jpgs) < 4:
        raise DemoError("E_DEMO_TOO_FEW", f"demo album too few photos: {album}")
    return album


def is_demo_album_path(raw: str) -> bool:
    val = str(raw or "").strip().lower()
    return val in (DEMO_ALBUM_SENTINEL.lower(), "demo-album", "@demo-album")
