"""Studio trip handlers — re-export facade (ADR-010 D1)."""

from __future__ import annotations

from travelogue.web.studio_handlers.asset_media_handlers import handle_asset_media_class
from travelogue.web.studio_handlers.trip_intent_handlers import (
    handle_get_cohort,
    handle_patch_cohort,
    handle_patch_copy_intent,
    handle_patch_intent,
    handle_patch_template,
    handle_post_cohort_refresh,
)
from travelogue.web.studio_handlers.trip_list_handlers import (
    handle_aesthetic,
    handle_bento_preview,
    handle_chapter_layout,
    handle_delete_trip,
    handle_entry,
    handle_trips,
)
from travelogue.web.studio_handlers.trip_pipeline_handlers import (
    handle_patch_pipeline,
    handle_rerender,
    handle_trip_curate,
)
from travelogue.web.studio_handlers.trip_replan_handlers import handle_patch_screen_replan

__all__ = [
    "handle_asset_media_class",
    "handle_aesthetic",
    "handle_bento_preview",
    "handle_chapter_layout",
    "handle_delete_trip",
    "handle_entry",
    "handle_get_cohort",
    "handle_patch_cohort",
    "handle_patch_copy_intent",
    "handle_patch_intent",
    "handle_patch_pipeline",
    "handle_patch_screen_replan",
    "handle_patch_template",
    "handle_post_cohort_refresh",
    "handle_rerender",
    "handle_trip_curate",
    "handle_trips",
]
