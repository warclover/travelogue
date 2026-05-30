"""Pipeline status constants shared across curation, vision, and web layers."""

from __future__ import annotations

PIPELINE_LOCKED_STATUSES: frozenset[str] = frozenset(
    {"structure_locked", "copy_draft", "copy_locked", "rendered", "exported"}
)
