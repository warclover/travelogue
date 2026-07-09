"""Person / face semantics for layout (shim → layout_contract.subject)."""

from __future__ import annotations

from travelogue.layout_contract.subject import (
    PERSON_TAGS,
    LayoutFit,
    any_asset_has_person,
    asset_has_face,
    asset_has_person,
    full_frame_fit_for_asset,
    portrait_fit_for_asset,
)

__all__ = [
    "LayoutFit",
    "PERSON_TAGS",
    "any_asset_has_person",
    "asset_has_face",
    "asset_has_person",
    "full_frame_fit_for_asset",
    "portrait_fit_for_asset",
]
