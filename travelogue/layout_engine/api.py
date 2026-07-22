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
    drain_mosaic_capture,
    drain_mosaic_dropped,
    lse_enabled,
    plan_chapter_screens,
    resolve_pack,
)
from travelogue.layout_engine.mosaic.log import annotate_winner_plan_logs
from travelogue.layout_engine.mosaic.replan import (
    ReplanError,
    refresh_trip_displayed_assets,
    replan_screen,
)
from travelogue.layout_engine.mosaic.trip import compose_trip
from travelogue.layout_engine.planner.screen_planner import resolve_layout_engine

__all__ = [
    "LAYOUT_ENGINE_LEGACY",
    "LAYOUT_ENGINE_SCREENS",
    "LAYOUT_ENGINE_VERSION_SCREENS",
    "ChapterPlanRequest",
    "ReplanError",
    "annotate_winner_plan_logs",
    "attach_screens_to_chapters",
    "compose_trip",
    "drain_mosaic_capture",
    "drain_mosaic_dropped",
    "lse_enabled",
    "plan_chapter_screens",
    "refresh_trip_displayed_assets",
    "replan_screen",
    "resolve_layout_engine",
    "resolve_pack",
]
