"""Compatibility shim · prefer travelogue.domain.stage_hints."""

from __future__ import annotations

from travelogue.domain.stage_hints import (  # noqa: F401
    EXPORT_READY,
    LAYOUT_PREVIEW_READY,
    PREPARING_BROWSER,
    PREPARING_HD,
    PREPARING_VISION,
    PROCESSING_PHOTOS,
    STAGE_HINT_COPY,
    VISION_WARMUP,
    preparing_hd_text,
    stage_hint_text,
)

__all__ = [
    "EXPORT_READY",
    "LAYOUT_PREVIEW_READY",
    "PREPARING_BROWSER",
    "PREPARING_HD",
    "PREPARING_VISION",
    "PROCESSING_PHOTOS",
    "STAGE_HINT_COPY",
    "VISION_WARMUP",
    "preparing_hd_text",
    "stage_hint_text",
]
