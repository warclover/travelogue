"""Backward-compatible re-export — prefer pattern_catalog (Phase 16 T7)."""

from travelogue.curation.mosaic.pattern_catalog import (
    AspectProfile,
    MosaicPattern,
    default_registry,
    patterns_for_window_size,
)

__all__ = [
    "AspectProfile",
    "MosaicPattern",
    "default_registry",
    "patterns_for_window_size",
]
