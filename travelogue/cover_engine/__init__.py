"""Cover Style Engine · process-local registry for Web cover opening skins (V6)."""

from __future__ import annotations

# Ensure catalog is registered on first import.
from travelogue.cover_engine import catalog as _catalog  # noqa: F401
from travelogue.cover_engine.api import (
    ClosingConflictError,
    ClosingPendingError,
    maybe_resolve_closing_after_layout,
    repick_closing,
    repick_opening,
    resolve_bookends,
    resolve_closing,
    resolve_opening,
    restore_auto,
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
from travelogue.cover_engine.lock import (
    is_closing_locked,
    is_opening_locked,
    read_lock_state,
    set_closing_locked,
    set_opening_locked,
    sync_lock_mirrors,
    write_lock_state,
)
from travelogue.cover_engine.opening.title_safe import mark_title_safe
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
from travelogue.cover_engine.studio import (
    list_preview_matrix,
    render_preview_context,
    studio_style_options,
)
from travelogue.cover_engine.types import (
    BookendsDecision,
    BookendsLockState,
    CoverJointExplain,
    CoverStyleProfile,
    CoverStyleRecord,
    CoverStyleStatus,
)

__all__ = [
    "BookendsDecision",
    "BookendsLockState",
    "ClosingConflictError",
    "ClosingPendingError",
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
    "is_closing_locked",
    "is_opening_locked",
    "legacy_map",
    "list_assignable_styles",
    "list_preview_matrix",
    "list_styles",
    "mark_title_safe",
    "maybe_resolve_closing_after_layout",
    "pick_cover_style_and_asset",
    "read_lock_state",
    "render_preview_context",
    "repick_closing",
    "repick_cover_for_style",
    "repick_opening",
    "resolve_bookends",
    "resolve_closing",
    "resolve_cover_opening_style",
    "resolve_opening",
    "resolve_style_id",
    "restore_auto",
    "score_pair",
    "set_closing_locked",
    "set_opening_locked",
    "set_style_status",
    "set_style_weight",
    "studio_style_options",
    "style_avoid_penalty",
    "style_fit_below_threshold",
    "style_fit_score",
    "sync_lock_mirrors",
    "write_lock_state",
]
