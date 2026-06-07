"""Which mosaic / grid patternIds are allowed under current config.

Deprecated: logic lives in ``lte_adapter.mosaic_pattern_disabled`` (Phase 16 W4).
"""

from __future__ import annotations

from travelogue.curation.mosaic.lte_adapter import mosaic_pattern_disabled

__all__ = ["mosaic_pattern_disabled"]
