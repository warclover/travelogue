"""Shared helper for studio JS assertions (P5-A1).

studio.js is now an ESM entry that delegates to focused modules under
templates/studio/js/. Tests that assert on controller internals should scan
the aggregated text of the entry + every module rather than studio.js alone.
"""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_STUDIO = _ROOT / "templates" / "studio"


def read_studio_js() -> str:
    """Concatenate the studio.js entry and all js/*.js modules."""
    parts = [(_STUDIO / "studio.js").read_text(encoding="utf-8")]
    js_dir = _STUDIO / "js"
    if js_dir.is_dir():
        for p in sorted(js_dir.glob("*.js")):
            parts.append(p.read_text(encoding="utf-8"))
    return "\n".join(parts)
