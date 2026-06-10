"""Shared aspect-ratio ladder constants (P16 §4.4 · R-MAIN-AR-01).

Kept separate from validator to avoid circular imports when mosaic code
reads template policy during registry bootstrap.
"""

from __future__ import annotations

# Conventional AR ladder (width/height)
AR_LADDER: tuple[float, ...] = (
    2 / 3,
    3 / 4,
    1.0,
    4 / 3,
    3 / 2,
    16 / 9,
)
AR_LADDER_TOL = 0.08

PORTRAIT_AR_MIN = 0.55
PORTRAIT_AR_MAX = 0.95
PORTRAIT_AR_BLOCK_LOW = 0.5
PORTRAIT_AR_BLOCK_HIGH = 1.0
LANDSCAPE_AR_MIN = 1.25
LANDSCAPE_AR_MAX = 2.2
LANDSCAPE_AR_BLOCK_HIGH = 2.5
