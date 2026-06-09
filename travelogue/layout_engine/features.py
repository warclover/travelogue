"""LayoutFeatures helpers · LSE-CAP-02 salient retention (§4.5.2)."""

from __future__ import annotations


def cover_focal_retention(
    slot_ar: float,
    asset_ar: float,
    *,
    focal_x: float = 0.5,
    focal_y: float = 0.45,
) -> float:
    """Focal point visible under object-fit cover (center crop proxy)."""
    fx = max(0.0, min(1.0, focal_x))
    fy = max(0.0, min(1.0, focal_y))
    if slot_ar <= 0 or asset_ar <= 0:
        return 0.0
    if slot_ar >= asset_ar:
        visible_h = asset_ar / slot_ar
        y0 = (1.0 - visible_h) / 2.0
        y1 = y0 + visible_h
        if y0 <= fy <= y1:
            return 1.0
        dist = min(abs(fy - y0), abs(fy - y1))
        return max(0.0, 1.0 - dist * 4.0)
    visible_w = slot_ar / asset_ar
    x0 = (1.0 - visible_w) / 2.0
    x1 = x0 + visible_w
    if x0 <= fx <= x1:
        return 1.0
    dist = min(abs(fx - x0), abs(fx - x1))
    return max(0.0, 1.0 - dist * 4.0)


def _slot_display_aspect(slot: dict) -> float:
    da = slot.get("displayAspect")
    if da is not None:
        try:
            return float(da)
        except (TypeError, ValueError):
            pass
    return 1.0


def _asset_aspect(asset: dict) -> float:
    w = asset.get("width") or asset.get("w")
    h = asset.get("height") or asset.get("h")
    try:
        wf, hf = float(w), float(h)
        if wf > 0 and hf > 0:
            return wf / hf
    except (TypeError, ValueError):
        pass
    return 1.0


def salient_retention_for_slot(slot: dict, asset: dict) -> float:
    """salient_retention(slot, asset) ∈ [0,1] for cover-fit slots."""
    fp = asset.get("focalPoint") or {}
    try:
        fx = float(fp.get("x", 0.5))
        fy = float(fp.get("y", 0.45))
    except (TypeError, ValueError):
        fx, fy = 0.5, 0.45
    retention = cover_focal_retention(
        _slot_display_aspect(slot),
        _asset_aspect(asset),
        focal_x=fx,
        focal_y=fy,
    )
    tags = asset.get("tags") or []
    if any(str(t).lower() in ("person", "people", "face") for t in tags) and retention < 0.75:
        retention *= 0.85
    return max(0.0, min(1.0, retention))


def salient_crop_penalty(screen: dict, assets_by_id: dict[str, dict]) -> float:
    """Penalty 0..1 — higher when cover slots lose salient/focal retention."""
    pen = 0.0
    for sl in screen.get("slots") or []:
        if str(sl.get("fit") or "cover").lower() != "cover":
            continue
        aid = sl.get("assetId")
        if not aid:
            continue
        asset = assets_by_id.get(str(aid)) or {}
        retention = salient_retention_for_slot(sl, asset)
        if retention < 0.55:
            pen = max(pen, 1.0 - retention)
        elif retention < 0.75:
            pen = max(pen, (0.75 - retention) * 2.0)
    return max(0.0, min(1.0, pen))
