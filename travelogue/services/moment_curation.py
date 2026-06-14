"""Phase 23 · moment pool Studio API helpers."""

from __future__ import annotations

from typing import Any


def cover_ids_for_moment(trip: dict) -> set[str]:
    out: set[str] = set()
    primary = str(trip.get("coverAssetId") or "").strip()
    if primary:
        out.add(primary)
    by_layout = (trip.get("curation") or {}).get("coverByLayout") or {}
    if isinstance(by_layout, dict):
        for value in by_layout.values():
            aid = str(value or "").strip()
            if aid:
                out.add(aid)
    return out


def validate_moment_asset_id(trip: dict, asset_id: str, *, assets: dict[str, dict] | None = None) -> str | None:
    """Return error code (E_MOMENT_*) or None when valid."""
    aid = str(asset_id or "").strip()
    if not aid:
        return "E_MOMENT_MISSING_ID"
    asset_map = assets or {str(a.get("id")): a for a in trip.get("assets") or [] if a.get("id")}
    if aid not in asset_map:
        return "E_MOMENT_UNKNOWN_ASSET"
    if asset_map[aid].get("type") != "image":
        return "E_MOMENT_NOT_IMAGE"
    if aid in cover_ids_for_moment(trip):
        return "E_MOMENT_COVER_CONFLICT"
    pool = (trip.get("curation") or {}).get("momentPoolIds") or []
    if isinstance(pool, list) and pool and aid not in pool:
        return "E_MOMENT_NOT_IN_POOL"
    skipped = (trip.get("curation") or {}).get("momentSkipped")
    if skipped:
        return "E_MOMENT_SKIPPED"
    return None


def apply_moment_signature(trip: dict, asset_id: str) -> None:
    """Set signature moment and refresh secondary ids."""
    aid = str(asset_id).strip()
    curation = trip.setdefault("curation", {})
    pool = list(curation.get("momentPoolIds") or [])
    if aid not in pool:
        raise ValueError("E_MOMENT_NOT_IN_POOL")
    trip["momentAssetId"] = aid
    curation["momentSecondaryIds"] = [pid for pid in pool if pid != aid]


def build_moment_curation_payload(trip: dict) -> dict[str, Any]:
    """Studio pool strip + explain (GET /curation/moment)."""
    curation = trip.get("curation") or {}
    assets = {str(a.get("id")): a for a in trip.get("assets") or [] if a.get("id")}
    pool_ids = list(curation.get("momentPoolIds") or [])
    signature = str(trip.get("momentAssetId") or "").strip()
    strip: list[dict[str, Any]] = []
    for i, aid in enumerate(pool_ids):
        asset = assets.get(aid) or {}
        strip.append(
            {
                "assetId": aid,
                "rank": i + 1,
                "isSignature": aid == signature,
                "userTier": asset.get("userTier"),
                "takenAt": asset.get("takenAt"),
                "hasExif": bool(isinstance(asset.get("exif"), dict) and asset.get("exif")),
            }
        )
    return {
        "momentAssetId": signature or None,
        "momentPoolIds": pool_ids,
        "momentPoolSize": curation.get("momentPoolSize"),
        "momentSecondaryIds": list(curation.get("momentSecondaryIds") or []),
        "momentCandidates": list(curation.get("momentCandidates") or []),
        "momentExplain": list(curation.get("momentExplain") or []),
        "momentPosition": curation.get("momentPosition"),
        "momentSkipped": curation.get("momentSkipped"),
        "momentCollision": curation.get("momentCollision"),
        "poolStrip": strip,
        "hasMoment": bool(signature) and not curation.get("momentSkipped"),
    }
