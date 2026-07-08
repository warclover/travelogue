"""Helpers for preview-toolbar CSS tests (M-C5 split)."""

from __future__ import annotations

import re
from pathlib import Path


def read_preview_toolbar_css_bundle(studio_dir: Path) -> str:
    """Return entry CSS plus all @imported partials (for selector assertions)."""
    entry_path = studio_dir / "preview-toolbar.css"
    entry = entry_path.read_text(encoding="utf-8")
    if "@import" not in entry:
        return entry
    parts = [entry]
    for line in entry.splitlines():
        match = re.search(r'@import\s+url\(["\']?([^"\')]+)["\']?\)', line.strip())
        if not match:
            continue
        partial = studio_dir / Path(match.group(1))
        parts.append(partial.read_text(encoding="utf-8"))
    return "\n".join(parts)
