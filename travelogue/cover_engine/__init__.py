"""Cover Style Engine · process-local registry for Web cover opening skins (V6)."""

from __future__ import annotations

from travelogue.cover_engine.registry import (
    get_default_style_id,
    get_profile,
    get_registry,
    get_style,
    is_assignable,
    list_assignable_styles,
    list_styles,
    set_style_status,
    set_style_weight,
)
from travelogue.cover_engine.resolve import (
    assignable_style_ids,
    legacy_map,
    resolve_cover_opening_style,
    resolve_style_id,
)
from travelogue.cover_engine.fit import (
    style_avoid_penalty,
    style_fit_below_threshold,
    style_fit_score,
)
from travelogue.cover_engine.joint import (
    apply_joint_pick,
    apply_style_keep_cover,
    hash_fallback_pick,
    pick_cover_style_and_asset,
    repick_cover_for_style,
    score_pair,
)
from travelogue.cover_engine.studio import (
    list_preview_matrix,
    render_preview_context,
    studio_style_options,
)
from travelogue.cover_engine.types import (
    CoverJointExplain,
    CoverStyleProfile,
    CoverStyleRecord,
    CoverStyleStatus,
)

# Ensure catalog is registered on first import.
from travelogue.cover_engine import catalog as _catalog  # noqa: F401

__all__ = [
    "CoverJointExplain",
    "CoverStyleProfile",
    "CoverStyleRecord",
    "CoverStyleStatus",
    "assignable_style_ids",
    "apply_joint_pick",
    "apply_style_keep_cover",
    "get_default_style_id",
    "get_profile",
    "get_registry",
    "get_style",
    "hash_fallback_pick",
    "is_assignable",
    "legacy_map",
    "list_assignable_styles",
    "list_preview_matrix",
    "list_styles",
    "pick_cover_style_and_asset",
    "render_preview_context",
    "repick_cover_for_style",
    "resolve_cover_opening_style",
    "resolve_style_id",
    "score_pair",
    "set_style_status",
    "set_style_weight",
    "studio_style_options",
    "style_avoid_penalty",
    "style_fit_below_threshold",
    "style_fit_score",
]
