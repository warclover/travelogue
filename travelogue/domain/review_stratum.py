"""Pure review-stratum classification shared by config and curation."""

from __future__ import annotations

from typing import Literal

from travelogue.layout_contract.orientations import aspect_kind_for_asset
from travelogue.layout_contract.subject_tagging import (
    semantic_category_for_asset,
    subject_class_for_asset,
)

ReviewStratum = Literal["person", "landscape", "food", "group", "general"]


def _face_count(asset: dict) -> int:
    """Face count for review stratum only; stale aggregate counts can be false positives."""
    faces = asset.get("faces")
    if isinstance(faces, list) and len(faces) > 0:
        return len(faces)
    return 0


def _is_portraitish_tags(asset: dict) -> bool:
    tags = {str(t).lower() for t in (asset.get("tags") or []) if t}
    return bool(tags & {"selfie", "portrait", "合影", "人像"})


def review_stratum_for_asset(asset: dict) -> ReviewStratum:
    """Coarse stratum for stratified blind-review sampling."""
    faces = _face_count(asset)
    if faces > 1:
        return "group"
    if faces == 1:
        return "person"

    aspect = aspect_kind_for_asset(asset)
    if aspect in ("landscape", "panorama") and not _is_portraitish_tags(asset):
        return "landscape"

    bucket = subject_class_for_asset(asset)
    if bucket == "person":
        return "person"
    category = semantic_category_for_asset(asset)
    if category == "food" or bucket == "food":
        return "food"
    if category in {"landscape", "nature", "architecture", "temple", "street", "mountain", "sea"}:
        return "landscape"
    if bucket == "landscape":
        return "landscape"
    return "general"
