"""G2 serve · promote/demote assets userTier (PRD-EXPERIENCE appendix A · Feedback Loop M2)."""

from __future__ import annotations

from travelogue.errors import CodeError
from travelogue.media.user_tier import demote_assets_from_featured, promote_assets_to_featured
from travelogue.util.datetime_ import utc_now_iso as _utc_now_iso


class TierPatchError(CodeError):
    pass


def apply_tier_promotions(trip: dict, asset_ids: list[str]) -> list[str]:
    if not asset_ids:
        raise TierPatchError("E_TIER_PATCH", "assetIds required")
    known = {str(a.get("id") or "") for a in trip.get("assets") or [] if a.get("id")}
    missing = [aid for aid in asset_ids if aid not in known]
    if missing:
        raise TierPatchError("E_TIER_PATCH", f"unknown asset ids: {', '.join(missing)}")
    promoted = promote_assets_to_featured(trip, asset_ids)
    if promoted:
        trip["updatedAt"] = _utc_now_iso()
    return promoted


def apply_tier_demotions(trip: dict, asset_ids: list[str]) -> list[str]:
    if not asset_ids:
        raise TierPatchError("E_TIER_PATCH", "assetIds required")
    known = {str(a.get("id") or "") for a in trip.get("assets") or [] if a.get("id")}
    missing = [aid for aid in asset_ids if aid not in known]
    if missing:
        raise TierPatchError("E_TIER_PATCH", f"unknown asset ids: {', '.join(missing)}")
    demoted = demote_assets_from_featured(trip, asset_ids)
    if demoted:
        trip["updatedAt"] = _utc_now_iso()
    return demoted
