"""Longshot screen helpers (layout kernel)."""

from __future__ import annotations

from travelogue.layout_contract.rhythm import BREATH_PATTERN


def is_breath_screen(screen: dict) -> bool:
    return screen.get("patternId") == BREATH_PATTERN


def screen_layout_kind(screen: dict) -> str:
    slots = screen.get("slots") or []
    aids = [s.get("assetId") for s in slots if s.get("assetId")]
    return "hero" if len(aids) <= 1 else "grid"
