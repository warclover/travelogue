"""Repository and desktop runtime path helpers.

Resource vs user-data roots are frozen by ADR-018 (Desktop Installer V1).
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

# Package / repo root as discovered from this file.
# In PyInstaller onedir this coincides with ``sys._MEIPASS`` (``_internal/``).
ROOT = Path(__file__).resolve().parents[1]

PORTABLE_FLAG_NAME = "portable.flag"
OWNERSHIP_MARKER_NAME = ".travelogue-ownership"
APP_DIRNAME = "Travelogue"
OWNERSHIP_MARKER_CONTENTS = "travelogue-ownership-v1\n"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def bundle_root() -> Path:
    """Read-only bundled resources (templates, schemas, datas)."""
    if is_frozen() and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return ROOT


def resource_root() -> Path:
    """Alias of :func:`bundle_root` (ADR-018)."""
    return bundle_root()


def exe_dir() -> Path:
    """Directory containing the frozen exe (portable sidecars live here)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return ROOT


def is_portable_mode() -> bool:
    """True only when frozen and ``portable.flag`` sits next to the exe.

    Environment variables never flip this bit (ADR-018 D3 / D-INS-12).
    """
    if not is_frozen():
        return False
    base = exe_dir()
    try:
        for child in base.iterdir():
            if child.is_file() and child.name.lower() == PORTABLE_FLAG_NAME:
                return True
    except OSError:
        return False
    return False


def user_data_dir() -> Path:
    """Writable user data root (trips / config / logs / cache).

    Priority:
    1. ``TRAVELOGUE_USER_DATA`` (path override only)
    2. Frozen portable → exe directory
    3. Frozen install → ``%LOCALAPPDATA%\\Travelogue``
    4. Dev → repository ``ROOT``
    """
    override = (os.environ.get("TRAVELOGUE_USER_DATA") or "").strip()
    if override:
        return Path(override).expanduser().resolve()
    if not is_frozen():
        return ROOT
    if is_portable_mode():
        return exe_dir()
    local = (os.environ.get("LOCALAPPDATA") or "").strip()
    if not local:
        local = str(Path.home() / "AppData" / "Local")
    return (Path(local) / APP_DIRNAME).resolve()


def default_trips_dir() -> Path:
    override = (os.environ.get("TRAVELOGUE_TRIPS_DIR") or "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return user_data_dir() / "trips"


def logs_dir() -> Path:
    return user_data_dir() / "logs"


def user_config_path() -> Path:
    return user_data_dir() / "config.yaml"


def bundled_config_example() -> Path:
    return resource_root() / "config.yaml.example"


def ownership_marker_path() -> Path:
    return user_data_dir() / OWNERSHIP_MARKER_NAME


def ensure_user_data_layout(*, bootstrap_config: bool = True) -> Path:
    """Create user-data directories, ownership marker, and optional first-run config.

    Intended for **frozen** Studio launches. Dev CLI should not call this
    (avoids writing ownership markers into the repo).
    """
    root = user_data_dir()
    root.mkdir(parents=True, exist_ok=True)
    for name in ("trips", "logs", "cache"):
        (root / name).mkdir(parents=True, exist_ok=True)

    marker = ownership_marker_path()
    if not marker.is_file():
        marker.write_text(OWNERSHIP_MARKER_CONTENTS, encoding="utf-8")

    if bootstrap_config:
        cfg = user_config_path()
        if not cfg.is_file():
            example = bundled_config_example()
            if example.is_file():
                shutil.copy2(example, cfg)
            else:
                cfg.write_text(
                    "# Travelogue Studio (auto-generated)\ntrips_dir: ./trips\n",
                    encoding="utf-8",
                )
    return root


# --- Bundled resource paths (always via resource_root / ROOT coincidence) ---
SCHEMA_PATH = ROOT / "schemas" / "trip.schema.json"
FIXTURES_DIR = ROOT / "schemas" / "fixtures"
TEMPLATES_ROOT = ROOT / "templates"
MANIFEST_PATH = TEMPLATES_ROOT / "visual-journal" / "manifest.json"
TEMPLATE_VISUAL_JOURNAL = TEMPLATES_ROOT / "visual-journal"


def template_dir_for(template_id: str) -> Path:
    return resource_root() / "templates" / template_id


def manifest_path_for(template_id: str) -> Path:
    return resource_root() / "templates" / template_id / "manifest.json"


GOLDEN_HTML = TEMPLATE_VISUAL_JOURNAL / "golden.html"
GOLDEN_TRIP_FIXTURE = FIXTURES_DIR / "trip.render_golden.json"
GOLDEN_REFERENCE_DIR_NAME = "_golden-reference"
GOLDEN_REFERENCE_TRIP_ID = "render-golden-demo"
DEMO_CONFIG_PATH = ROOT / "config.demo.yaml"
JOURNAL_CSS = TEMPLATE_VISUAL_JOURNAL / "journal.css"
JOURNAL_SCREENS_CSS = TEMPLATE_VISUAL_JOURNAL / "journal-screens.css"
LONGSHOT_JS = TEMPLATE_VISUAL_JOURNAL / "longshot.js"
LONGSHOT_CSS = TEMPLATE_VISUAL_JOURNAL / "longshot.css"
SHARE_JS = TEMPLATE_VISUAL_JOURNAL / "share.js"
SCREENPLAY_JS = TEMPLATE_VISUAL_JOURNAL / "screenplay.js"
SCREENPLAY_HASH_JS = TEMPLATE_VISUAL_JOURNAL / "screenplay-hash.js"
SCREENPLAY_BOOKMARKS_JS = TEMPLATE_VISUAL_JOURNAL / "screenplay-bookmarks.js"
SCREENPLAY_CSS = TEMPLATE_VISUAL_JOURNAL / "screenplay.css"
COPY_TOGGLE_JS = TEMPLATE_VISUAL_JOURNAL / "copy-toggle.js"
COPY_DISPLAY_CSS = TEMPLATE_VISUAL_JOURNAL / "copy-display.css"
LONGSHOT_BRIDGE_JS = TEMPLATE_VISUAL_JOURNAL / "longshot-bridge.js"
BREATH_JS = TEMPLATE_VISUAL_JOURNAL / "breath.js"
BREATH_CSS = TEMPLATE_VISUAL_JOURNAL / "breath.css"
BREATH_LENIS_JS = TEMPLATE_VISUAL_JOURNAL / "breath-lenis.js"
BREATH_GSAP_JS = TEMPLATE_VISUAL_JOURNAL / "breath-gsap.js"
BREATH_HIGHLIGHT_JS = TEMPLATE_VISUAL_JOURNAL / "breath-highlight.js"
BREATH_IMAGE_JS = TEMPLATE_VISUAL_JOURNAL / "breath-image.js"
SCROLL_NAV_JS = TEMPLATE_VISUAL_JOURNAL / "scroll-nav.js"
INLINE_EDIT_JS = TEMPLATE_VISUAL_JOURNAL / "inline-edit.js"
INLINE_EDIT_CSS = TEMPLATE_VISUAL_JOURNAL / "inline-edit.css"
HETANGYUESE_WOFF2 = TEMPLATE_VISUAL_JOURNAL / "assets" / "fonts" / "hetangyuese.woff2"
HTML2CANVAS_VENDOR = TEMPLATE_VISUAL_JOURNAL / "vendor" / "html2canvas.min.js"
STUDIO_TEMPLATE_DIR = ROOT / "templates" / "studio"
