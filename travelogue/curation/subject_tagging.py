"""Subject tagging placeholder for future person-cluster signals."""

from __future__ import annotations

from typing import Any

_CLIP_TO_BUCKET: dict[str, str] = {
    "person": "person",
    "landscape": "landscape",
    "architecture": "landscape",
    "street": "landscape",
    "temple": "landscape",
    "food": "food",
    "indoor": "general",
    "mixed": "general",
}

_CLIP_CONFIDENCE_FLOOR = 0.35


def _map_clip_to_bucket(subject_class: str) -> str:
    key = subject_class.lower().strip()
    return _CLIP_TO_BUCKET.get(key, "general")


def _heuristic_subject_class(asset: dict) -> str:
    tags = {str(t).lower() for t in (asset.get("tags") or []) if t}
    bucket = str(asset.get("subjectBucket") or "").lower()
    cur = asset.get("curation") or {}
    stags = cur.get("subjectTags") or subject_tags_for_asset(asset)
    if "has_face" in stags or tags & {"person", "face", "portrait"} or bucket in {
        "person",
        "portrait",
    }:
        return "person"
    if tags & {"landscape", "scenery", "mountain", "sea", "sky", "nature"} or bucket in {
        "landscape",
        "scenery",
        "temple",
        "street",
        "nature",
    }:
        return "landscape"
    if tags & {"food", "meal", "restaurant"} or bucket in {"food", "meal"}:
        return "food"
    return "general"


def subject_class_for_asset(asset: dict) -> str:
    """Coarse subject bucket for run scoring (Phase 3a / P9-E bridge)."""
    clip = str(asset.get("subjectClass") or "").lower().strip()
    if clip:
        conf = asset.get("subjectConfidence")
        if conf is None or float(conf) >= _CLIP_CONFIDENCE_FLOOR:
            return _map_clip_to_bucket(clip)
    return _heuristic_subject_class(asset)


def subject_tags_for_asset(asset: dict) -> list[str]:
    """P1: return subject tags; P0 returns hasFace boolean as tag."""
    tags: list[str] = []
    clip = str(asset.get("subjectClass") or "").strip()
    if clip:
        tags.append(f"clip:{clip.lower()}")
    faces = asset.get("faces") or []
    if faces:
        tags.append("has_face")
    heuristic = asset.get("tags") or []
    for t in heuristic:
        if isinstance(t, str) and t.startswith("person"):
            tags.append(t)
    return tags


def enrich_assets_subject_tags(assets: list[dict]) -> list[dict]:
    """Non-destructive copy with curation.subjectTags when missing."""
    out: list[dict] = []
    for a in assets:
        copy = dict(a)
        cur = dict(copy.get("curation") or {})
        if "subjectTags" not in cur:
            cur["subjectTags"] = subject_tags_for_asset(a)
        copy["curation"] = cur
        out.append(copy)
    return out
