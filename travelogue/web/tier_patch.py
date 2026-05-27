"""G2 serve · promote assets to featured userTier (PRD-EXPERIENCE appendix A · P5)."""

from __future__ import annotations

from datetime import datetime, timezone

from travelogue.media.user_tier import promote_assets_to_featured


class TierPatchError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
