"""Pairing package."""

from __future__ import annotations

from travelogue.cover_engine.pairing.explain import build_closing_explain, closing_user_one_liner
from travelogue.cover_engine.pairing.policy import (
    filter_pairing_hard,
    pairing_hard_violations,
    pairing_soft_bonus,
)

__all__ = [
    "build_closing_explain",
    "closing_user_one_liner",
    "filter_pairing_hard",
    "pairing_hard_violations",
    "pairing_soft_bonus",
]
