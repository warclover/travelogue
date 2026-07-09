"""Enrich mosaic window logs with LTE template metadata (AC-P16-08)."""

from __future__ import annotations

from typing import Any

from travelogue.config import get_config
from travelogue.layout_engine.mosaic.log import MosaicWindowLog


def _slot_ar_match_score(screen: dict[str, Any], assets_map: dict[str, dict]) -> float | None:
    distances: list[float] = []
    for slot in screen.get("slots") or []:
        target = slot.get("displayAspect")
        aid = slot.get("assetId", "")
        asset = assets_map.get(aid) if aid else None
        if target is None or asset is None:
            continue
        try:
            target_f = float(target)
        except (TypeError, ValueError):
            continue
        w = int(asset.get("width") or asset.get("nativeWidth") or 0)
        h = int(asset.get("height") or asset.get("nativeHeight") or 0)
        if w <= 0 or h <= 0:
            continue
        asset_ar = w / h
        distances.append(abs(target_f - asset_ar) / max(target_f, asset_ar, 1e-6))
    if not distances:
        return None
    return round(sum(distances) / len(distances), 4)


def enrich_mosaic_log_from_screen(
    log: MosaicWindowLog,
    screen: dict[str, Any] | None,
    *,
    assets_map: dict[str, dict] | None = None,
) -> None:
    if not screen:
        return
    geo = screen.get("layoutGeometry") or {}
    if geo.get("templateVersion") is not None:
        log.template_version = int(geo["templateVersion"])
    te = getattr(get_config().layout, "template_engine", None)
    if te is not None:
        log.template_registry_version = str(getattr(te, "registry_version", "") or "")
    if assets_map:
        score = _slot_ar_match_score(screen, assets_map)
        if score is not None:
            log.slot_ar_match_score = score
