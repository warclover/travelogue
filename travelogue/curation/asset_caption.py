"""Per-asset captions for screens / longshot surfaces."""

from __future__ import annotations

from travelogue.curation.chapter_items import collect_screen_asset_ids


def chapter_caption_asset_ids(chapter: dict) -> list[str]:
    """Asset ids that may carry per-photo captions in this chapter."""
    if chapter.get("screens"):
        return collect_screen_asset_ids(chapter)
    ids: list[str] = []
    for item in chapter.get("items") or []:
        if item.get("type") == "media-card" and item.get("assetId"):
            ids.append(item["assetId"])
    return ids


def asset_caption(asset: dict | None) -> str:
    if not asset:
        return ""
    return (asset.get("caption") or "").strip()


def item_caption(item: dict | None) -> str:
    if not item:
        return ""
    return (item.get("caption") or "").strip()


def asset_skips_caption(asset: dict | None) -> bool:
    return bool(asset and asset.get("skipCaption"))


def resolve_caption(item: dict | None, asset: dict | None) -> str:
    """Display precedence: item caption, then asset caption; skipCaption wins."""
    if asset_skips_caption(asset):
        return ""
    return item_caption(item) or asset_caption(asset)


def find_item_for_asset(chapter: dict, asset_id: str) -> dict | None:
    for item in chapter.get("items") or []:
        if item.get("type") == "media-card" and item.get("assetId") == asset_id:
            return item
        if item.get("type") in ("media-row", "media-scroll"):
            if asset_id in (item.get("assetIds") or []):
                return item
    return None


def set_asset_caption(trip: dict, asset_id: str, caption: str, *, skip: bool | None = None) -> bool:
    for asset in trip.get("assets") or []:
        if asset.get("id") == asset_id:
            if skip or not (caption or "").strip():
                asset.pop("caption", None)
                asset["skipCaption"] = True
            else:
                asset["caption"] = caption
                asset.pop("skipCaption", None)
            return True
    return False


def apply_caption_to_trip(trip: dict, asset_id: str, caption: str) -> list[str]:
    """
    Write caption to assets[].caption and matching chapter items[] when present.
    Empty caption sets skipCaption on the asset.
    Returns log labels.
    """
    updated: list[str] = []
    cap = (caption or "").strip()
    if set_asset_caption(trip, asset_id, cap):
        updated.append(
            f"assets.{asset_id}.skipCaption" if not cap else f"assets.{asset_id}.caption"
        )
    for ch in trip.get("chapters") or []:
        item = find_item_for_asset(ch, asset_id)
        if item and item.get("type") == "media-card":
            if cap:
                item["caption"] = cap
            else:
                item.pop("caption", None)
            updated.append(f"chapters.{ch.get('id')}.items.{asset_id}.caption")
            break
    return updated


def migrate_captions_to_assets(trip: dict) -> list[str]:
    """
    Copy item-level captions onto assets when the asset has none.
    media-card items only (row/scroll captions stay block-level).
    """
    assets = {a.get("id"): a for a in trip.get("assets") or [] if a.get("id")}
    migrated: list[str] = []
    for ch in trip.get("chapters") or []:
        for item in ch.get("items") or []:
            if item.get("type") != "media-card":
                continue
            aid = item.get("assetId")
            cap = item_caption(item)
            if not aid or not cap:
                continue
            asset = assets.get(aid)
            if not asset or asset_caption(asset):
                continue
            asset["caption"] = cap
            migrated.append(aid)
    return migrated
