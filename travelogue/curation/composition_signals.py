"""Composition helpers shared by cover scoring and aesthetic synthesis (no curation deps)."""

from __future__ import annotations

_THIRD_LINES = (1.0 / 3.0, 2.0 / 3.0)


def subject_center_norm(asset: dict) -> tuple[float, float]:
    box = asset.get("salientBox")
    if isinstance(box, dict):
        x = float(box.get("x", 0.5))
        y = float(box.get("y", 0.5))
        w = float(box.get("w", 0.0))
        h = float(box.get("h", 0.0))
        return (
            min(1.0, max(0.0, x + w / 2.0)),
            min(1.0, max(0.0, y + h / 2.0)),
        )
    fp = asset.get("focalPoint") or {}
    return float(fp.get("x", 0.5)), float(fp.get("y", 0.45))


def nearest_third_distance(coord: float) -> float:
    return min(abs(coord - line) for line in _THIRD_LINES)


def axis_rule_of_thirds_score(coord: float) -> float:
    dist = nearest_third_distance(coord)
    return max(0.0, 1.0 - dist / 0.25)


def mean_thirds_score(asset: dict) -> float:
    cx, cy = subject_center_norm(asset)
    return (axis_rule_of_thirds_score(cx) + axis_rule_of_thirds_score(cy)) / 2.0
