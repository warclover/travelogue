"""Trip meta constants shared across layers (avoid media → services imports)."""

from __future__ import annotations

# Private mutator signal — recognized by merge_pipeline_persist / TripService.update.
STAMP_RENDERED_REVISION = "_stampRenderedRevision"
