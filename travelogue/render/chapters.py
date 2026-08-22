"""Stable import name for the journal chapter builder (DPI W2 · IE-DPI-09).

Identity dispatch lives only in assemble.py. This module is a re-export only.
"""

from __future__ import annotations

from travelogue.render.journal_chapters import (
    ChaptersRenderBundle,
    build_journal_chapters,
)

build_chapters_render_context = build_journal_chapters

__all__ = [
    "ChaptersRenderBundle",
    "build_chapters_render_context",
    "build_journal_chapters",
]
