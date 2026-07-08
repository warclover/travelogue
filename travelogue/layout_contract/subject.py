"""Person / face semantics for layout (tags from ingest vision · layout kernel)."""

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


def full_frame_fit_for_asset(
    asset: dict | None,
    *,
    default: LayoutFit = "cover",
    face_ratio_contain: float = 0.15,
) -> LayoutFit:
    """full-frame 沉浸优先：横图风景 cover；竖图人物或人脸占比高时 contain。"""
    if not asset:
        return default
    if not asset_has_person(asset):
        return default
    w = int(asset.get("nativeWidth") or asset.get("width") or 0)
    h = int(asset.get("nativeHeight") or asset.get("height") or 0)
    if h > w > 0:
        return "contain"
    quality = asset.get("quality") or {}
    try:
        face_ratio = float(quality.get("faceRatio") or 0)
    except (TypeError, ValueError):
        face_ratio = 0.0
    if face_ratio >= face_ratio_contain:
        return "contain"
    return default


def any_asset_has_person(asset_ids: list[str], assets_map: dict[str, dict]) -> bool:
    return any(asset_has_person(assets_map.get(aid)) for aid in asset_ids)
