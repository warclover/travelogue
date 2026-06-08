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


def trip_render_fingerprint_payload(trip: dict[str, Any]) -> dict[str, Any]:
    """Subset of trip.json used for render hash / quick_share golden (AC-P17-31)."""
    body = {
        "assets": trip.get("assets") or [],
        "chapters": trip.get("chapters") or [],
        "exportLayout": trip.get("exportLayout"),
        "layoutEngine": trip.get("layoutEngine"),
        "meta": trip.get("meta") or {},
    }
    cur = trip.get("curation")
    if isinstance(cur, dict):
        body["curation"] = curation_for_render_contract(cur)
    intent = trip.get("intent")
    if isinstance(intent, dict):
        body["intent"] = {k: v for k, v in intent.items() if k != "layoutStrategy"}
    return body
