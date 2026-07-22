"""Share-Face Integrity · field-level copy origin (BE-SFI-00 / D-SFI-03).

``user`` fields are never overwritten by copy refresh. Legacy ``edited: true``
maps to user for coarse protection until migrated.
"""

from __future__ import annotations

from typing import Any

ORIGIN_USER = "user"
ORIGIN_STUB = "stub"
ORIGIN_LLM = "llm"
VALID_ORIGINS = frozenset({ORIGIN_USER, ORIGIN_STUB, ORIGIN_LLM})


def normalize_origin(value: Any) -> str | None:
    raw = str(value or "").strip().lower()
    return raw if raw in VALID_ORIGINS else None


def get_field_origin(obj: dict | None, origin_key: str, *, edited_fallback: bool = True) -> str | None:
    """Return field origin; optionally treat legacy ``edited`` as user."""
    if not isinstance(obj, dict):
        return None
    origin = normalize_origin(obj.get(origin_key))
    if origin:
        return origin
    if edited_fallback and obj.get("edited"):
        return ORIGIN_USER
    return None


def is_user_protected(obj: dict | None, origin_key: str) -> bool:
    return get_field_origin(obj, origin_key) == ORIGIN_USER


def mark_origin(obj: dict, origin_key: str, origin: str = ORIGIN_USER) -> None:
    origin = normalize_origin(origin) or ORIGIN_USER
    obj[origin_key] = origin
    if origin == ORIGIN_USER:
        obj["edited"] = True


def migrate_edited_to_origin(trip: dict) -> list[str]:
    """Promote legacy ``edited`` flags into field-level origin=user (idempotent)."""
    touched: list[str] = []
    meta = trip.get("meta")
    if isinstance(meta, dict) and meta.get("edited"):
        if (meta.get("hook") or "").strip() and not normalize_origin(meta.get("hookOrigin")):
            meta["hookOrigin"] = ORIGIN_USER
            touched.append("meta.hookOrigin")
        if (trip.get("epilogue") or "").strip() and not normalize_origin(
            trip.get("epilogueOrigin")
        ):
            trip["epilogueOrigin"] = ORIGIN_USER
            touched.append("epilogueOrigin")

    for ch in trip.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        ch_id = str(ch.get("id") or "")
        if ch.get("edited"):
            if (ch.get("title") or "").strip() and not normalize_origin(ch.get("titleOrigin")):
                ch["titleOrigin"] = ORIGIN_USER
                touched.append(f"chapters.{ch_id}.titleOrigin")
            if (ch.get("lead") or "").strip() and not normalize_origin(ch.get("leadOrigin")):
                ch["leadOrigin"] = ORIGIN_USER
                touched.append(f"chapters.{ch_id}.leadOrigin")
            if (ch.get("decorLine") or "").strip() and not normalize_origin(
                ch.get("decorLineOrigin")
            ):
                ch["decorLineOrigin"] = ORIGIN_USER
                touched.append(f"chapters.{ch_id}.decorLineOrigin")
        for it in ch.get("items") or []:
            if not isinstance(it, dict) or it.get("type") != "media-card":
                continue
            if it.get("edited") and not normalize_origin(it.get("captionOrigin")):
                if (it.get("caption") or "").strip() or it.get("edited"):
                    it["captionOrigin"] = ORIGIN_USER
                    touched.append(f"items.{it.get('assetId')}.captionOrigin")
        for sc in ch.get("screens") or []:
            if isinstance(sc, dict) and sc.get("edited") and not sc.get("copyMeta"):
                # Screen copyMeta.kickerSource/bodySource already cover editorial paths;
                # keep edited for schema validity only.
                pass

    for asset in trip.get("assets") or []:
        if not isinstance(asset, dict):
            continue
        if asset.get("edited") and not normalize_origin(asset.get("captionOrigin")):
            if (asset.get("caption") or "").strip():
                asset["captionOrigin"] = ORIGIN_USER
                touched.append(f"assets.{asset.get('id')}.captionOrigin")

    return touched
