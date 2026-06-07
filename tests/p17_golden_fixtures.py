"""P17 layout golden fixture catalog (PRD §10.3)."""

from __future__ import annotations

P17_MIXED_FIXTURES = ("golden-mixed-scenes",)

P17_PORTRAIT_FIXTURES = (
    "golden-portrait-family",
    "golden-portrait-travel",
)

P17_LANDSCAPE_FIXTURES = (
    "golden-landscape-coast",
    "golden-landscape-mountain",
)

P17_CONTROLLED_PARITY_FIXTURES = (
    *P17_MIXED_FIXTURES,
    *P17_PORTRAIT_FIXTURES,
    *P17_LANDSCAPE_FIXTURES,
)
