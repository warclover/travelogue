"""Person / face semantics for layout (tags from ingest vision)."""

from __future__ import annotations

from typing import Literal

LayoutFit = Literal["cover", "contain"]

PERSON_TAGS = frozenset({"person", "face", "people", "portrait-person"})


def asset_has_person(asset: dict | None) -> bool:
    if not asset:
        return False
    tags = asset.get("tags") or []
    return any(str(t).lower() in PERSON_TAGS for t in tags)


def asset_has_face(asset: dict | None) -> bool:
    if not asset:
        return False
    tags = {str(t).lower() for t in (asset.get("tags") or [])}
    return "face" in tags or "person" in tags


def portrait_fit_for_asset(
    asset: dict | None,
    *,
    default: LayoutFit = "cover",
) -> LayoutFit:
    """含人物/人脸的竖图优先完整展示，避免 cover 裁切。"""
    if asset_has_person(asset):
        return "contain"
    return default


def any_asset_has_person(asset_ids: list[str], assets_map: dict[str, dict]) -> bool:
    return any(asset_has_person(assets_map.get(aid)) for aid in asset_ids)
