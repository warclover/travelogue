"""Studio · PA aesthetic explain payload (PA-T10).

Read-only helpers over ``trip.json`` assets — never mutates the trip.
"""

from __future__ import annotations

from typing import Any

from travelogue.curation.aesthetic_score import asset_aesthetic, build_aesthetic_explain


def displayed_asset_ids(trip: dict) -> list[str]:
    """Asset ids referenced by chapter screens, in document order (deduped)."""
    ids: list[str] = []
    seen: set[str] = set()
    for chapter in trip.get("chapters") or []:
        for screen in chapter.get("screens") or []:
            for slot in screen.get("slots") or []:
                aid = slot.get("assetId")
                if not aid:
                    continue
                key = str(aid)
                if key in seen:
                    continue
                seen.add(key)
                ids.append(key)
    return ids


def build_asset_aesthetic_studio_row(
    asset: dict,
    *,
    limit: int = 3,
) -> dict[str, Any] | None:
    """One asset row for Studio (overall + top dimensions)."""
    ae = asset_aesthetic(asset)
    if not ae:
        return None
    aid = asset.get("id")
    if not aid:
        return None
    explain = build_aesthetic_explain(asset, limit=limit)
    row: dict[str, Any] = {
        "id": str(aid),
        "displayFile": asset.get("displayFile"),
        "overall": ae.get("overall"),
        "confidence": ae.get("confidence"),
        "source": ae.get("source"),
        "explain": explain,
    }
    dims = ae.get("dims")
    if isinstance(dims, dict) and dims:
        row["dims"] = dims
    return row


def _aesthetic_stale_hint(*, enabled: bool, image_count: int, scored_count: int) -> str | None:
    if enabled and image_count > 0 and scored_count == 0:
        return "审美评分未生成，请重新导入照片以应用封面/排版优化"
    return None


def build_aesthetic_entry_summary(trip: dict, *, enabled: bool) -> dict[str, Any]:
    """Compact counts for ``GET …/entry`` (no per-asset explain)."""
    assets = trip.get("assets") or []
    images = [a for a in assets if a.get("type", "image") != "video" and a.get("id")]
    scored = sum(1 for a in images if asset_aesthetic(a))
    displayed = displayed_asset_ids(trip)
    displayed_scored = 0
    if displayed:
        by_id = {str(a["id"]): a for a in images}
        displayed_scored = sum(
            1 for aid in displayed if asset_aesthetic(by_id.get(aid) or {})
        )
    stale = enabled and len(images) > 0 and scored == 0
    return {
        "enabled": enabled,
        "scoredCount": scored,
        "displayedCount": len(displayed),
        "displayedScoredCount": displayed_scored,
        "stale": stale,
        "staleHint": _aesthetic_stale_hint(
            enabled=enabled,
            image_count=len(images),
            scored_count=scored,
        ),
    }


def build_aesthetic_studio_payload(
    trip: dict,
    *,
    enabled: bool = True,
    asset_ids: list[str] | None = None,
    limit: int = 3,
) -> dict[str, Any]:
    """GET /trips/{id}/aesthetic response body (without ``ok`` wrapper)."""
    assets = trip.get("assets") or []
    by_id = {str(a["id"]): a for a in assets if a.get("id")}
    want = asset_ids if asset_ids is not None else displayed_asset_ids(trip)
    if not want:
        want = list(by_id.keys())

    rows: list[dict[str, Any]] = []
    for aid in want:
        asset = by_id.get(str(aid))
        if not asset or asset.get("type") == "video":
            continue
        row = build_asset_aesthetic_studio_row(asset, limit=limit)
        if row:
            rows.append(row)

    cover_explain = (trip.get("curation") or {}).get("coverExplain") or []
    images = [a for a in assets if a.get("type", "image") != "video" and a.get("id")]
    scored_count = sum(1 for a in images if asset_aesthetic(a))
    stale = enabled and len(images) > 0 and scored_count == 0
    return {
        "enabled": enabled,
        "scoredCount": scored_count,
        "stale": stale,
        "staleHint": _aesthetic_stale_hint(
            enabled=enabled,
            image_count=len(images),
            scored_count=scored_count,
        ),
        "assets": rows,
        "coverExplain": cover_explain if isinstance(cover_explain, list) else [],
    }
