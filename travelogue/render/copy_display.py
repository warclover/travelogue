"""Render-time copy visibility (export.copyDisplay).

Semantics (two paths):
- **draft** (workshop preview, copy-toggle toolbar): ``photos`` keeps narrative in the
  DOM; ``data-copy-display="photos"`` + ``copy-display.css`` hide blocks. Users can
  toggle back via ``copy-toggle.js``.
- **share** / non-draft export without inline toggle: ``photos`` strips hook, leads,
  captions, and epilogue from render context so they are omitted from HTML.
"""

from __future__ import annotations

from typing import Literal

CopyDisplay = Literal["full", "photos"]

COPY_DISPLAY_FULL: CopyDisplay = "full"
COPY_DISPLAY_PHOTOS: CopyDisplay = "photos"
VALID_COPY_DISPLAY = frozenset({COPY_DISPLAY_FULL, COPY_DISPLAY_PHOTOS})


def resolve_copy_display(trip: dict, *, override: str | None = None) -> CopyDisplay:
    """Resolve copy display mode; default full (show all narrative copy)."""
    raw = override
    if raw is None:
        raw = (trip.get("export") or {}).get("copyDisplay")
    if raw is None or raw == "":
        return COPY_DISPLAY_FULL
    val = str(raw).strip().lower()
    if val not in VALID_COPY_DISPLAY:
        return COPY_DISPLAY_FULL
    return val  # type: ignore[return-value]


def is_photos_only(copy_display: str) -> bool:
    return copy_display == COPY_DISPLAY_PHOTOS


def should_strip_narrative_copy(
    *,
    photos_only: bool,
    include_screenplay: bool,
    is_draft: bool,
) -> bool:
    """True when photos mode should omit narrative blocks at render time (share path)."""
    return photos_only and not include_screenplay and not is_draft
