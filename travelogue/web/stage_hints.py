"""Compatibility shim · prefer travelogue.domain.stage_hints."""

from __future__ import annotations

from travelogue.domain.stage_hints import (  # noqa: F401
    PREPARING_BROWSER,
    PREPARING_VISION,
    PROCESSING_PHOTOS,
    STAGE_HINT_COPY,
    stage_hint_text,
)

__all__ = [
    "PREPARING_BROWSER",
    "PREPARING_VISION",
    "PROCESSING_PHOTOS",
    "STAGE_HINT_COPY",
    "stage_hint_text",
]
