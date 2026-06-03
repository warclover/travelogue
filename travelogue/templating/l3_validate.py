"""L3: template capabilities vs trip assets (PRD §5.4)."""

from __future__ import annotations

from travelogue.templates.registry import get_registry
from travelogue.templating.resolver import resolve_effective_template


def _asset_has_geo(asset: dict) -> bool:
    loc = asset.get("location") or asset.get("geo") or {}
    if isinstance(loc, dict):
        if loc.get("lat") is not None and loc.get("lng") is not None:
            return True
        if loc.get("latitude") is not None and loc.get("longitude") is not None:
            return True
    return bool(asset.get("place") or asset.get("city"))


def _trip_has_route_signal(trip: dict) -> bool:
    meta = trip.get("meta") or {}
    if meta.get("routePolyline") or meta.get("route"):
        return True
    assets = trip.get("assets") or []
    geo_count = sum(1 for a in assets if _asset_has_geo(a))
    return geo_count >= max(2, len(assets) // 4)


def validate_template_capabilities(trip: dict, *, template_id: str | None = None) -> list[str]:
    """Return hard errors (no WARN prefix). Empty = OK."""
    tid = template_id or resolve_effective_template(trip)
    try:
        rec = get_registry().get(tid)
    except Exception as exc:
        return [f"unknown template: {exc}"]

    caps = {str(c).lower() for c in (rec.capabilities or ())}
    errors: list[str] = []

    if "map" in caps or "route" in caps:
        if (trip.get("assets") or []) and not _trip_has_route_signal(trip):
            errors.append(f"WARN: L3: template {tid} lacks geo/route signal for map-heavy layout")

    if "event" in caps:
        videos = [a for a in (trip.get("assets") or []) if str(a.get("type") or "").lower() == "video"]
        if not videos and len(trip.get("assets") or []) > 0:
            errors.append(f"L3: template {tid} is event-oriented but trip has no video assets")

    return errors
