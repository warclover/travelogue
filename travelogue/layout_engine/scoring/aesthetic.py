"""Aesthetic score adapter."""

from __future__ import annotations


def aesthetic_overall(asset: dict) -> float | None:
    from travelogue.layout_engine.scoring.aesthetic import aesthetic_overall as _fn

    return _fn(asset)
