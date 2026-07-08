"""Person / face semantics for layout (shim → layout_contract.subject)."""

from __future__ import annotations

import importlib

_mod = importlib.import_module("travelogue.layout_contract.subject")
__all__ = [
    "LayoutFit",
    "PERSON_TAGS",
    "any_asset_has_person",
    "asset_has_face",
    "asset_has_person",
    "full_frame_fit_for_asset",
    "portrait_fit_for_asset",
]
for _name in __all__:
    globals()[_name] = getattr(_mod, _name)
