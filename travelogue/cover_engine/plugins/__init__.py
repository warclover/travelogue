"""Bookends optional plugins (B3)."""

from __future__ import annotations

from travelogue.cover_engine.plugins.vl import (
    apply_closing_vl_rerank,
    apply_opening_vl_rerank,
    closing_vl_enabled,
    opening_vl_enabled,
)

__all__ = [
    "apply_closing_vl_rerank",
    "apply_opening_vl_rerank",
    "closing_vl_enabled",
    "opening_vl_enabled",
]
