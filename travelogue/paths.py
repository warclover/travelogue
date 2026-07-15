"""Repository path helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "trip.schema.json"
FIXTURES_DIR = ROOT / "schemas" / "fixtures"
TEMPLATES_ROOT = ROOT / "templates"
MANIFEST_PATH = TEMPLATES_ROOT / "visual-journal" / "manifest.json"
TEMPLATE_VISUAL_JOURNAL = TEMPLATES_ROOT / "visual-journal"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def bundle_root() -> Path:
    if is_frozen() and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return ROOT


def exe_dir() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def default_trips_dir() -> Path:
    if is_frozen():
        return exe_dir() / "trips"
    return ROOT / "trips"


def user_data_dir(*, ensure: bool = False) -> Path:
    """Writable user data root for Desktop LLM secrets / overlays.

    Frozen: ``%LOCALAPPDATA%/TravelogueStudio`` (Windows) or ``~/.local/share/TravelogueStudio``.
    Override: ``TRAVELOGUE_USER_DATA``.
    Non-frozen default: ``ROOT/.travelogue-user`` (keeps repo root clean of secrets).
    """
    override = (os.environ.get("TRAVELOGUE_USER_DATA") or "").strip()
    if override:
        path = Path(override).expanduser().resolve()
    elif is_frozen():
        if os.name == "nt":
            base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
            root = Path(base) if base else Path.home() / "AppData" / "Local"
            path = (root / "TravelogueStudio").resolve()
        else:
            path = (Path.home() / ".local" / "share" / "TravelogueStudio").resolve()
    else:
        path = (ROOT / ".travelogue-user").resolve()
    if ensure:
        path.mkdir(parents=True, exist_ok=True)
    return path


def template_dir_for(template_id: str) -> Path:
    return TEMPLATES_ROOT / template_id


def manifest_path_for(template_id: str) -> Path:
    return TEMPLATES_ROOT / template_id / "manifest.json"
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
