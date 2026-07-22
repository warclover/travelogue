"""Public Layout Engine API (CSC W2a · facade).

External packages (``curation`` / ``services`` / ``web``) should import from here
(or ``travelogue.layout_engine``) instead of ``planner.*`` / ``mosaic.*`` internals.
"""

from __future__ import annotations

from travelogue.layout_contract.engines import (
    LAYOUT_ENGINE_LEGACY,
    LAYOUT_ENGINE_SCREENS,
    LAYOUT_ENGINE_VERSION_SCREENS,
)
from travelogue.layout_engine.adapter import (
    ChapterPlanRequest,
    attach_screens_to_chapters,
    lse_enabled,
    plan_chapter_screens,
    resolve_pack,
)
from travelogue.layout_engine.mosaic.trip import compose_trip
from travelogue.layout_engine.planner.screen_planner import resolve_layout_engine

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
