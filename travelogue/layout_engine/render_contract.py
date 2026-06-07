"""Render input isolation for LSE observability fields (AC-P17-31 · §4.10.2)."""

from __future__ import annotations

from typing import Any

# C 端渲染 / quick_share golden hash 不得纳入的可观测字段
RENDER_ISOLATED_CURATION_KEYS = frozenset(
    {
        "layoutStrategy",
        "layoutDecisionLog",
        "mosaicDecisionLog",
        "editorialHints",
    }
)

RENDER_ISOLATED_TRIP_KEYS = frozenset(
    {
        "capability_flags",
        "weightsHash",
    }
)


def curation_for_render_contract(curation: dict[str, Any] | None) -> dict[str, Any]:
    """Strip LSE observability keys before render fingerprinting."""
    if not isinstance(curation, dict):
        return {}
    return {k: v for k, v in curation.items() if k not in RENDER_ISOLATED_CURATION_KEYS}
