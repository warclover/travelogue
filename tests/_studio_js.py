"""Shared helper for studio JS assertions (P5-A1).

M21 retired templates/studio/studio.js; scan v2 homepage + shared js modules.
"""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_STUDIO = _ROOT / "templates" / "studio"


def read_studio_js() -> str:
    """Concatenate active Studio JS entry points and shared modules."""
    parts: list[str] = []
    candidates = [
        _STUDIO / "legacy-freeze" / "studio.classic.js",
        _STUDIO / "homepage-v2" / "import-run.js",
        _STUDIO / "homepage-v2" / "import-sheet.js",
        _STUDIO / "homepage-v2" / "advanced-options.js",
    ]
    for path in candidates:
        if path.is_file():
            parts.append(path.read_text(encoding="utf-8"))
    js_dir = _STUDIO / "js"
    if js_dir.is_dir():
        for p in sorted(js_dir.glob("*.js")):
            parts.append(p.read_text(encoding="utf-8"))
    v2_dir = _STUDIO / "homepage-v2"
    if v2_dir.is_dir():
        for p in sorted(v2_dir.glob("*.js")):
            if p.name not in {"import-run.js", "import-sheet.js", "advanced-options.js"}:
                parts.append(p.read_text(encoding="utf-8"))
    return "\n".join(parts)


def read_preview_toolbar_js() -> str:
    """Read preview toolbar implementation (bootstrap + templates + store)."""
    pt = _STUDIO / "preview-toolbar"
    parts: list[str] = []
    for name in (
        "store.js",
        "templates.js",
        "toolbar-ui.js",
        "pending.js",
        "export-state.js",
        "export-drawer.js",
        "export-popover.js",
        "export-run.js",
        "menu.js",
        "stale-sync.js",
        "shell.js",
        "share-mode.js",
        "drawer-support.js",
        "drawers.js",
        "narrate.js",
        "mode-reader.js",
        "mode-edit.js",
        "bootstrap.js",
    ):
        path = pt / name
        if path.is_file():
            parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)
