"""Studio trip handlers — re-export facade (ADR-010 D1)."""

from __future__ import annotations

from travelogue.web.studio_handlers.asset_media_handlers import handle_asset_media_class
from travelogue.web.studio_handlers.bookends_handlers import (
    handle_get_bookends,
    handle_post_repick_closing,
    handle_post_repick_opening,
    handle_post_resolve_closing,
    handle_post_resolve_opening,
    handle_post_restore_auto,
)
from travelogue.web.studio_handlers.trip_intent_handlers import (
    handle_get_cohort,
    handle_patch_cohort,
    handle_patch_copy_intent,
    handle_patch_intent,
    handle_patch_template,
    handle_post_cohort_refresh,
    handle_post_copy_telemetry,
)
from travelogue.web.studio_handlers.trip_list_handlers import (
    handle_aesthetic,
    handle_bento_preview,
    handle_chapter_layout,
    handle_delete_trip,
    handle_entry,
    handle_patch_stratum_preference,
    handle_trips,
)
from travelogue.web.studio_handlers.trip_moment_handlers import (
    handle_get_moment_curation,
    handle_patch_moment,
)
from travelogue.web.studio_handlers.trip_pipeline_handlers import (
    handle_patch_pipeline,
    handle_rerender,
    handle_trip_curate,
)
from travelogue.web.studio_handlers.layout_vibe_handlers import handle_layout_vibe
from travelogue.web.studio_handlers.trip_replan_handlers import handle_patch_screen_replan

__all__ = [
    "handle_asset_media_class",
    "handle_aesthetic",
    "handle_bento_preview",
    "handle_chapter_layout",
    "handle_delete_trip",
    "handle_entry",
    "handle_get_bookends",
    "handle_get_moment_curation",
    "handle_get_cohort",
    "handle_layout_vibe",
    "handle_patch_cohort",
    "handle_patch_copy_intent",
    "handle_patch_intent",
    "handle_patch_moment",
    "handle_patch_pipeline",
    "handle_patch_screen_replan",
    "handle_patch_stratum_preference",
    "handle_patch_template",
    "handle_post_cohort_refresh",
    "handle_post_copy_telemetry",
    "handle_post_repick_closing",
    "handle_post_repick_opening",
    "handle_post_resolve_closing",
    "handle_post_resolve_opening",
    "handle_post_restore_auto",
    "handle_rerender",
    "handle_trip_curate",
    "handle_trips",
]
