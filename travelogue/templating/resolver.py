"""Single entry for effective template id (PRD §6.4 · P13-PR-09)."""

from __future__ import annotations

import logging

from travelogue.templates.registry import DEFAULT_TEMPLATE_ID

_log = logging.getLogger(__name__)


def is_template_locked(trip: dict) -> bool:
    """Aggregate business lock → template_locked (PRD §5.6)."""
    sel = trip.get("templateSelection") or {}
    if sel.get("locked") is True:
        return True
    pipeline = trip.get("pipeline") or {}
    locks = pipeline.get("locks") or {}
    if locks.get("copy") is True:
        return True
    if trip.get("copy_locked") is True:
        return True
    return False


def resolve_effective_template(trip: dict) -> str:
    """Authoritative template id for render / validate / export."""
    sel = trip.get("templateSelection") or {}
    resolved = sel.get("resolvedTemplateId")
    if isinstance(resolved, str) and resolved.strip():
        return resolved.strip()
    legacy = trip.get("templateId")
    if isinstance(legacy, str) and legacy.strip():
        return legacy.strip()
    return DEFAULT_TEMPLATE_ID


def sync_template_id_mirror(trip: dict) -> None:
    """Keep compatibility mirror aligned with resolved template (TripService writer)."""
    effective = resolve_effective_template(trip)
    legacy = trip.get("templateId")
    if isinstance(legacy, str) and legacy.strip() and legacy.strip() != effective:
        sel = trip.setdefault("templateSelection", {})
        sel["mirrorMismatch"] = True
        _log.warning(
            "templateId mirror mismatch trip=%s legacy=%s resolved=%s",
            trip.get("tripId"),
            legacy.strip(),
            effective,
        )
        from travelogue.templating.metrics import record_template_metric

        record_template_metric(
            "template.mirror.mismatch",
            tripId=trip.get("tripId"),
            legacy=legacy.strip(),
            resolved=effective,
        )
    trip["templateId"] = effective
