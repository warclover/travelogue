"""Resolve cover opening style ids (API-CSE-04/05, render path)."""

from __future__ import annotations

from travelogue.cover_engine.catalog import legacy_map_table
from travelogue.cover_engine.registry import get_default_style_id, get_style, list_assignable_styles


def legacy_map(raw: str) -> str | None:
    """Map a V5 id to V6; return None if no mapping."""
    key = (raw or "").strip()
    if not key:
        return None
    return legacy_map_table().get(key)


def resolve_style_id(raw: str | None) -> str:
    """
    Empty/illegal → default.
    V5 alias → mapped V6 id.
    Known active/retired id → unchanged (retired still renders).
    """
    default = get_default_style_id()
    key = (raw or "").strip()
    if not key:
        return default

    mapped = legacy_map(key)
    if mapped is not None:
        return mapped

    rec = get_style(key)
    if rec is not None:
        return rec.id
    return default


def resolve_cover_opening_style(trip: dict) -> str:
    """Thin trip wrapper → resolve_style_id(meta.coverOpeningStyle)."""
    raw = (trip.get("meta") or {}).get("coverOpeningStyle")
    return resolve_style_id(None if raw is None else str(raw))


def assignable_style_ids() -> tuple[str, ...]:
    return tuple(r.id for r in list_assignable_styles())
