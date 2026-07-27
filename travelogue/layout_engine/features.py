"""LayoutFeatures helpers · LSE-CAP-02 salient retention (§4.5.2).

Uses CSS-consistent cover windows (object-position percentage) and person-safe
face/protect containment via ``crop_solver``.
"""

from __future__ import annotations

from travelogue.layout_engine.crop_solver import (
    cover_window,
    crop_safety,
    faces_from_asset,
    protect_box_from_asset,
    solve_slot_focal,
)


def cover_focal_retention(
    slot_ar: float,
    asset_ar: float,
    *,
    focal_x: float = 0.5,
    focal_y: float = 0.45,
) -> float:
    """Focal point visible under object-fit:cover with CSS percentage positioning.

    Note: with percentage object-position the focal is *always* inside the
    visible window by construction. This helper remains for probe/legacy callers;
    person-safe scoring should use ``salient_retention_for_slot`` / face safety.
    """
    fx = max(0.0, min(1.0, focal_x))
    fy = max(0.0, min(1.0, focal_y))
    if slot_ar <= 0 or asset_ar <= 0:
        return 0.0
    win = cover_window(slot_ar, asset_ar, fx, fy)
    if win.axis == "none":
        return 1.0
    if win.axis == "y":
        if win.y0 - 1e-9 <= fy <= win.y1 + 1e-9:
            return 1.0
        dist = min(abs(fy - win.y0), abs(fy - win.y1))
        return max(0.0, 1.0 - dist * 4.0)
    if win.x0 - 1e-9 <= fx <= win.x1 + 1e-9:
        return 1.0
    dist = min(abs(fx - win.x0), abs(fx - win.x1))
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
    """salient_retention(slot, asset) ∈ [0,1] for cover-fit slots.

    Prefer person-safe solve: faceClipped → hard fail; else protect containment.
    Falls back to focal retention when no person evidence exists.
    """
    slot_ar = _slot_display_aspect(slot)
    asset_ar = _asset_aspect(asset)
    faces = faces_from_asset(asset)
    protect = protect_box_from_asset(asset)

    if faces or protect is not None:
        # Prefer already-solved cropFocal when present (MSA / prior pass).
        cf = slot.get("cropFocal")
        if isinstance(cf, dict) and cf.get("x") is not None and cf.get("y") is not None:
            try:
                fx = float(cf["x"])
                fy = float(cf["y"])
            except (TypeError, ValueError):
                fx, fy = 0.5, 0.45
            win = cover_window(slot_ar, asset_ar, fx, fy)
            safety = crop_safety(window=win, faces=faces, protect=protect)
        else:
            solved = solve_slot_focal(asset, slot_ar)
            safety = solved.safety
        if safety.face_clipped:
            return 0.0
        return max(0.0, min(1.0, float(safety.protect_containment)))

    fp = asset.get("focalPoint") or {}
    try:
        fx = float(fp.get("x", 0.5))
        fy = float(fp.get("y", 0.45))
    except (TypeError, ValueError):
        fx, fy = 0.5, 0.45
    return cover_focal_retention(slot_ar, asset_ar, focal_x=fx, focal_y=fy)


def salient_crop_penalty(screen: dict, assets_by_id: dict[str, dict]) -> float:
    """Penalty 0..1 — higher when cover slots clip faces / lose protect region."""
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
        # Hard bump when face is known-clipped (retention already 0, but keep explicit)
        cs = sl.get("cropSafety")
        if isinstance(cs, dict) and cs.get("faceClipped"):
            pen = max(pen, 1.0)
    return max(0.0, min(1.0, pen))
