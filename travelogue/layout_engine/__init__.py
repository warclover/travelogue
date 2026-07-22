"""Layout Strategy Engine (LSE) · Phase 17.

Public surface: ``travelogue.layout_engine.api`` (also re-exported here).
Internal packages ``planner`` / ``mosaic`` are not a stable cross-package API.
"""

from __future__ import annotations

from travelogue.layout_engine.api import (
    LAYOUT_ENGINE_LEGACY,
    LAYOUT_ENGINE_SCREENS,
    LAYOUT_ENGINE_VERSION_SCREENS,
    ChapterPlanRequest,
    attach_screens_to_chapters,
    compose_trip,
    lse_enabled,
    plan_chapter_screens,
    resolve_layout_engine,
    resolve_pack,
)

__all__ = [
    "LAYOUT_ENGINE_LEGACY",
    "LAYOUT_ENGINE_SCREENS",
    "LAYOUT_ENGINE_VERSION_SCREENS",
    "ChapterPlanRequest",
    "attach_screens_to_chapters",
    "compose_trip",
    "lse_enabled",
    "plan_chapter_screens",
    "resolve_layout_engine",
    "resolve_pack",
]
