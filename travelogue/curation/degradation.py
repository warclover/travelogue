"""Degradation guard: force legacy layout when inputs are insufficient (ADR-002 D3)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DegradationAssessment:
    force_legacy: bool
    reason: str | None = None
    layout_eligible_count: int = 0
    aspect_kind_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "forceLegacy": self.force_legacy,
            "reason": self.reason,
            "layoutEligibleCount": self.layout_eligible_count,
            "aspectKindCount": self.aspect_kind_count,
        }


def assess_degradation(
    layout_assets: list[dict],
    aspects: dict[str, str],
    *,
    min_layout_eligible: int = 3,
    min_aspect_kinds: int = 1,
    structure_locked: bool = False,
    force_relayout: bool = False,
) -> DegradationAssessment:
    eligible = [
        a
        for a in layout_assets
        if a.get("layoutEligible", True) is not False
    ]
    kinds = {aspects.get(a["id"]) for a in eligible if a.get("id") and aspects.get(a["id"])}
    kinds.discard(None)

    if structure_locked and not force_relayout:
        return DegradationAssessment(
            force_legacy=True,
            reason="structure_locked",
            layout_eligible_count=len(eligible),
            aspect_kind_count=len(kinds),
        )
    if len(eligible) < min_layout_eligible:
        return DegradationAssessment(
            force_legacy=True,
            reason="insufficient_layout_eligible",
            layout_eligible_count=len(eligible),
            aspect_kind_count=len(kinds),
        )
    if len(kinds) < min_aspect_kinds:
        return DegradationAssessment(
            force_legacy=True,
            reason="insufficient_aspect_diversity",
            layout_eligible_count=len(eligible),
            aspect_kind_count=len(kinds),
        )
    return DegradationAssessment(
        force_legacy=False,
        layout_eligible_count=len(eligible),
        aspect_kind_count=len(kinds),
    )
