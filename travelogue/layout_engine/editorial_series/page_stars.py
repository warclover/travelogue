"""Compiled face-star snapshot for portfolio cousin / upgrade.

Source: docs/templates/reserve/stars.yaml
Synced: 2026-08-27
Do not import docs.templates.reserve (ISO-05 / D-TDV-09).
Unlisted face = 0. Mirror ids do not inherit. 3 = best.
"""

from __future__ import annotations

FACE_STARS: dict[str, int] = {
    "page-1-hero-land-right": 3,
    "page-1-hero-land-wide": 3,
    "page-1-hero-port": 3,
    "page-10-grid-port": 3,
    "page-2-1l1p-wide": 3,
    "page-2-1p1l-wide": 3,
    "page-2-pair-land": 3,
    "page-2-pair-port": 3,
    "page-3-2l1p-left": 3,
    "page-3-2l1p-right": 3,
    "page-3-2l1p-hero-right": 3,
    "page-3-2l1p-wide-left": 3,
    "page-3-2l1p-wide-right": 3,
    "page-3-land": 3,
    "page-3-port": 3,
    "page-4-1p3l-wide-left": 3,
    "page-4-1p3l-wide-right": 3,
    "page-4-2p2l-cross": 3,
    "page-4-grid-land": 3,
    "page-4-grid-land-wide": 3,
    "page-4-port": 3,
    "page-5-3p2l-center": 3,
    "page-5-3p2l-center-flip": 3,
    "page-6-1l5l-wide-left": 3,
    "page-6-2l4p-wide": 3,
    "page-6-2l4p-wide-flip": 3,
    "page-6-grid-land": 3,
    "page-7-1p6l-center": 3,
    "page-8-2l6p": 3,
    "page-8-grid-land": 3,
    "page-8-grid-port": 3,
    "page-9-grid-land-wide": 3,
    "page-4-1l3l-left": 2,
    "page-4-1l3l-right": 2,
    "page-4-1l3l-wide-left": 2,
    "page-4-1l3l-wide-right": 2,
    "page-5-1p4l-center": 2,
    "page-5-3p2l-left": 2,
    "page-5-3p2l-right": 2,
    "page-5-3p2l-stack-center": 2,
    "page-5-3p2l-stack-right": 2,
    "page-6-1l5l-wide-right": 2,
    "page-6-2l4p-left": 2,
    "page-6-2l4p-right": 2,
    "page-7-1p6l-left": 2,
    "page-7-1p6l-right": 2,
    "page-4-1p3l-left": 1,
}

DISABLED_FACES: frozenset[str] = frozenset(
    {
        "page-4-2p2p",
        "page-6-4l2p",
    }
)


def star_of(tid: str) -> int:
    """0–3. Unlisted or junk → 0."""
    try:
        n = int(FACE_STARS.get(str(tid or "").strip(), 0))
    except (TypeError, ValueError):
        return 0
    if n < 0:
        return 0
    if n > 3:
        return 3
    return n


def is_disabled(tid: str) -> bool:
    return str(tid or "").strip() in DISABLED_FACES
