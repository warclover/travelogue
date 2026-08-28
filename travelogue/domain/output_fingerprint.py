"""Output Ledger fingerprints (OLT M1). Pure functions; stdlib only.

``structure_fp`` must not include any ``trip.export`` options (BLK-OLT-05).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

_SEPARATORS = (",", ":")


def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=_SEPARATORS)


def _hex8(payload: Any, prefix: str) -> str:
    digest = hashlib.sha256(_canon(payload).encode("utf-8")).hexdigest()[:8]
    return f"{prefix}{digest}"


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _studio(trip: dict[str, Any] | None) -> dict[str, Any]:
    return _as_dict((_as_dict(trip).get("studio")))


def _meta(trip: dict[str, Any] | None) -> dict[str, Any]:
    return _as_dict((_as_dict(trip).get("meta")))


def _export(trip: dict[str, Any] | None) -> dict[str, Any]:
    return _as_dict((_as_dict(trip).get("export")))


def _item_asset_ids(item: dict[str, Any]) -> list[str]:
    out: list[str] = []
    aid = item.get("assetId")
    if aid:
        out.append(str(aid))
    for extra in item.get("assetIds") or []:
        if extra:
            out.append(str(extra))
    return out


def _screen_projection(chapter: dict[str, Any]) -> list[dict[str, Any]]:
    screens = chapter.get("screens")
    if isinstance(screens, list) and screens:
        projected: list[dict[str, Any]] = []
        for screen in screens:
            if not isinstance(screen, dict):
                continue
            slots: list[str] = []
            for slot in screen.get("slots") or []:
                if isinstance(slot, dict) and slot.get("assetId"):
                    slots.append(str(slot["assetId"]))
            projected.append(
                {
                    "patternId": str(screen.get("patternId") or ""),
                    "assetIds": slots,
                }
            )
        return projected
    asset_ids: list[str] = []
    for item in chapter.get("items") or []:
        if isinstance(item, dict):
            asset_ids.extend(_item_asset_ids(item))
    return [
        {
            "patternId": str(chapter.get("patternId") or ""),
            "assetIds": asset_ids,
        }
    ]


def structure_payload(trip: dict[str, Any] | None) -> dict[str, Any]:
    """Canonical structure projection. No ``export`` options (BLK-OLT-05)."""
    trip = _as_dict(trip)
    studio = _studio(trip)
    folio = _as_dict(studio.get("portfolio"))
    chapters: list[dict[str, Any]] = []
    for chapter in trip.get("chapters") or []:
        if not isinstance(chapter, dict):
            continue
        chapters.append(
            {
                "chapterId": str(chapter.get("id") or chapter.get("chapterId") or ""),
                "screens": _screen_projection(chapter),
            }
        )
    return {
        "edition": str(studio.get("edition") or "journal"),
        "pageCount": folio.get("pageCount"),
        "coverAssetId": str(trip.get("coverAssetId") or ""),
        "coverStyleId": str(_meta(trip).get("coverOpeningStyle") or ""),
        "chapters": chapters,
    }


def _captions(trip: dict[str, Any]) -> list[str]:
    captions: list[str] = []
    for chapter in trip.get("chapters") or []:
        if not isinstance(chapter, dict):
            continue
        for item in chapter.get("items") or []:
            if isinstance(item, dict) and "caption" in item:
                captions.append(str(item.get("caption") or ""))
        for screen in chapter.get("screens") or []:
            if not isinstance(screen, dict):
                continue
            for slot in screen.get("slots") or []:
                if isinstance(slot, dict) and "caption" in slot:
                    captions.append(str(slot.get("caption") or ""))
    return captions


def copy_payload(trip: dict[str, Any] | None) -> dict[str, Any]:
    trip = _as_dict(trip)
    meta = _meta(trip)
    chapters: list[dict[str, Any]] = []
    for chapter in trip.get("chapters") or []:
        if not isinstance(chapter, dict):
            continue
        chapters.append(
            {
                "chapterId": str(chapter.get("id") or chapter.get("chapterId") or ""),
                "hook": str(chapter.get("hook") or ""),
                "lead": str(chapter.get("lead") or ""),
            }
        )
    return {
        "title": str(meta.get("title") or ""),
        "subtitle": str(meta.get("subtitle") or ""),
        "chapters": chapters,
        "captions": _captions(trip),
    }


def structure_fp(trip: dict[str, Any] | None) -> str:
    return _hex8(structure_payload(trip), "st:")


def copy_fp(trip: dict[str, Any] | None) -> str:
    return _hex8(copy_payload(trip), "cp:")


def options_fp(
    trip: dict[str, Any] | None,
    keys: list[str] | tuple[str, ...] | None,
) -> str | None:
    """Hash the declared ``trip.export`` subset. Empty keys → never mismatches."""
    if not keys:
        return None
    export = _export(trip)
    subset = {str(key): export.get(key) for key in keys}
    return _hex8(subset, "op:")


def source_snapshot(
    trip: dict[str, Any] | None,
    *,
    bundle_fp: str,
    stale_options: list[str] | tuple[str, ...] | None = None,
) -> dict[str, str | None]:
    return {
        "structureFp": structure_fp(trip),
        "copyFp": copy_fp(trip),
        "bundleFp": str(bundle_fp or ""),
        "optionsFp": options_fp(trip, stale_options),
    }
