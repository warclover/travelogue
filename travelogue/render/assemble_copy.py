"""Share-face hook / epilogue sanitizer. Does not read edition."""

from __future__ import annotations


def apply_share_face_copy(
    *,
    hook: str,
    epilogue: str,
    meta_title: str,
    meta_edited: bool,
    is_draft: bool,
    trip_id: str,
) -> tuple[str, str]:
    """Run hook and epilogue through the share-face funnel. Caller decides skip."""
    from travelogue.domain.share_face_copy import (
        record_stub_hit,
        sanitize_share_copy_tracked,
    )

    hook, hook_blanked = sanitize_share_copy_tracked(
        hook, title=meta_title, kind="lead", edited=meta_edited
    )
    if hook_blanked:
        record_stub_hit(
            surface="draft" if is_draft else "share",
            field="hook",
            trip_id=trip_id or None,
        )
    epilogue, epi_blanked = sanitize_share_copy_tracked(
        epilogue, title=meta_title, kind="lead", edited=meta_edited
    )
    if epi_blanked:
        record_stub_hit(
            surface="draft" if is_draft else "share",
            field="epilogue",
            trip_id=trip_id or None,
        )
    return hook, epilogue
