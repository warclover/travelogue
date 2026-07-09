"""Cover resolution helpers over trip.json (M-B1 / M-C4)."""

from __future__ import annotations

LAYOUT_ENGINE_SCREENS = "screens"


def layout_eligible_assets(trip: dict) -> list[dict]:
    """Assets usable for cover, chapters, and screens."""
    return [
        a
        for a in trip.get("assets") or []
        if a.get("type", "image") != "video" and a.get("layoutEligible", True) is not False
    ]


def resolve_cover_render_profile(
    export_layout: str,
    *,
    index_name: str = "index.html",
    layout_engine: str | None = None,
) -> str:
    """Map render surface to cover profile (mobile portrait vs web landscape)."""
    if export_layout in ("mobile", "web"):
        return export_layout
    if index_name in ("index-mobile.html",):
        return "mobile"
    if layout_engine == LAYOUT_ENGINE_SCREENS or index_name in (
        "index.html",
        "index-present.html",
    ):
        return "web"
    return "mobile"


def resolve_cover_asset_id(
    trip: dict,
    *,
    export_layout: str,
    index_name: str | None = None,
    layout_engine: str | None = None,
) -> str:
    """Resolve cover from curation.coverByLayout, then trip.coverAssetId."""
    assets = layout_eligible_assets(trip)
    if not assets:
        return ""
    profile = resolve_cover_render_profile(
        export_layout,
        index_name=index_name or "index.html",
        layout_engine=layout_engine or trip.get("layoutEngine"),
    )
    by_layout = (trip.get("curation") or {}).get("coverByLayout") or {}
    if isinstance(by_layout, dict) and profile in by_layout:
        cid = by_layout[profile]
        if cid and any(a.get("id") == cid for a in assets):
            return str(cid)
    fallback = str(trip.get("coverAssetId") or "")
    if fallback and any(a.get("id") == fallback for a in assets):
        return fallback
    return ""
