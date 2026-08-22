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

# Bundled demo album sentinels (media may check without importing desktop).
DEMO_ALBUM_SENTINEL = "@bundled/demo-album"


def is_demo_album_path(raw: str) -> bool:
    val = str(raw or "").strip().lower()
    return val in (DEMO_ALBUM_SENTINEL.lower(), "demo-album", "@demo-album")


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


def user_data_dir(*, ensure: bool = False) -> Path:
    """Writable user data root (trips / config / logs / cache / LLM secrets).

    Priority:
    1. ``TRAVELOGUE_USER_DATA`` (path override only)
    2. Frozen portable -> exe directory
    3. Frozen install -> ``%LOCALAPPDATA%\\Travelogue``
    4. Dev -> repository ``ROOT``

    ``ensure=True`` creates the directory (Desktop LLM Setup / launcher).
    """
    override = (os.environ.get("TRAVELOGUE_USER_DATA") or "").strip()
    if override:
        path = Path(override).expanduser().resolve()
    elif not is_frozen():
        path = ROOT
    elif is_portable_mode():
        path = exe_dir()
    else:
        local = (os.environ.get("LOCALAPPDATA") or "").strip()
        if not local:
            local = str(Path.home() / "AppData" / "Local")
        path = (Path(local) / APP_DIRNAME).resolve()
    if ensure:
        path.mkdir(parents=True, exist_ok=True)
    return path

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
                    "# Travelogue Studio (auto-generated)\n"
                    "trips_dir: ./trips\n"
                    "llm:\n"
                    "  provider: stub\n",
                    encoding="utf-8",
                )
            _force_bootstrap_llm_provider_stub(cfg)
            _force_bootstrap_vision_disabled(cfg)
    return root


def _force_bootstrap_vision_disabled(cfg_path: Path) -> None:
    """First-run desktop: vision.enabled=false (D-FTUE-04 / AC-FTUE-06)."""
    try:
        text = cfg_path.read_text(encoding="utf-8")
    except OSError:
        return
    lines = text.splitlines(keepends=True)
    if not lines:
        return
    out: list[str] = []
    in_vision = False
    replaced = False
    for line in lines:
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]
        if stripped.startswith("vision:") and not indent.strip("\t"):
            in_vision = True
            out.append(line)
            continue
        if in_vision:
            if stripped and not stripped.startswith("#") and indent == "":
                in_vision = False
            elif not replaced and stripped.startswith("enabled:"):
                nl = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
                out.append(
                    f"{indent}enabled: false  # desktop L0 / FTUE default{nl}"
                )
                replaced = True
                continue
        out.append(line)
    if not replaced:
        if out and not out[-1].endswith("\n"):
            out[-1] = out[-1] + "\n"
        out.append("\nvision:\n  enabled: false  # desktop L0 / FTUE default\n")
    try:
        cfg_path.write_text("".join(out), encoding="utf-8")
    except OSError:
        return


def _force_bootstrap_llm_provider_stub(cfg_path: Path) -> None:
    """First-run desktop config must default to stub (D-L0G-02 / BE-04).

    Preserves comments where possible by rewriting only the ``provider:`` line
    inside the top-level ``llm:`` block.
    """
    try:
        text = cfg_path.read_text(encoding="utf-8")
    except OSError:
        return
    lines = text.splitlines(keepends=True)
    if not lines:
        return
    out: list[str] = []
    in_llm = False
    replaced = False
    for line in lines:
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]
        if stripped.startswith("llm:") and not indent.strip("\t"):
            in_llm = True
            out.append(line)
            continue
        if in_llm:
            # Left the llm block (next top-level key).
            if stripped and not stripped.startswith("#") and indent == "":
                in_llm = False
            elif not replaced and stripped.startswith("provider:"):
                nl = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
                out.append(
                    f"{indent}provider: stub  # desktop L0 default; upgrade via Settings{nl}"
                )
                replaced = True
                continue
        out.append(line)
    if not replaced:
        # No llm.provider line ? append a stub block.
        if out and not out[-1].endswith("\n"):
            out[-1] = out[-1] + "\n"
        out.append("\nllm:\n  provider: stub  # desktop L0 default; upgrade via Settings\n")
    try:
        cfg_path.write_text("".join(out), encoding="utf-8")
    except OSError:
        return


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
PORTFOLIO_PAGES_CSS = TEMPLATE_VISUAL_JOURNAL / "portfolio-pages.css"
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
