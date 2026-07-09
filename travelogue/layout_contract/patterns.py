"""Pure layout pattern helpers."""

from __future__ import annotations

EDITORIAL_COMPOSITE_PATTERN_PREFIX = "screen-editorial-"


def is_editorial_composite_pattern(pattern_id: str | None) -> bool:
    return str(pattern_id or "").strip().startswith(EDITORIAL_COMPOSITE_PATTERN_PREFIX)
