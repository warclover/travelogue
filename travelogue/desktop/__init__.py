"""Windows desktop helpers (Phase 2 M11 · PyInstaller exe)."""

from travelogue.desktop.bundle import bundle_root, default_trips_dir, is_frozen
from travelogue.desktop.demo_album import resolve_demo_album_dir
from travelogue.desktop.folder_dialog import pick_folder

__all__ = [
    "bundle_root",
    "default_trips_dir",
    "is_frozen",
    "pick_folder",
    "resolve_demo_album_dir",
]
