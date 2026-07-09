"""Pure media-class readers for layout contracts."""

from __future__ import annotations


def is_collage_asset(asset: dict | None) -> bool:
    return str((asset or {}).get("mediaClass") or "") == "collage"
