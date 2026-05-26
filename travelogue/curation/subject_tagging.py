"""Subject tagging placeholder for future person-cluster signals."""

from __future__ import annotations

from typing import Any


def subject_class_for_asset(asset: dict) -> str:
    """Coarse subject bucket for run scoring (Phase 3a)."""
    tags = {str(t).lower() for t in (asset.get("tags") or []) if t}
    cur = asset.get("curation") or {}
    stags = cur.get("subjectTags") or subject_tags_for_asset(asset)
    if "has_face" in stags or tags & {"person", "face", "portrait"}:
        return "person"
    if tags & {"landscape", "scenery", "mountain", "sea", "sky", "nature"}:
        return "landscape"
    if tags & {"food", "meal", "restaurant"}:
        return "food"
    return "general"


def subject_tags_for_asset(asset: dict) -> list[str]:
    """P1: return subject tags; P0 returns hasFace boolean as tag."""
    tags: list[str] = []
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
