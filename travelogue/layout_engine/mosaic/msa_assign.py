"""MSA · aux assignment refine — flattest slot protection (S-MSA-03 / AC-07)."""

from __future__ import annotations

from typing import Any, Mapping

from travelogue.layout_engine.mosaic.msa_fit import crop_risk_for_pair


def _is_landscape_asset(asset: Mapping[str, Any] | None) -> bool:
    if not asset:
        return False
    kind = str(asset.get("aspectKind") or asset.get("aspect_kind") or "").lower()
    if kind == "landscape":
        return True
    if kind in ("portrait", "square", "tall", "panorama"):
        return False
    try:
        w = float(asset.get("width"))
        h = float(asset.get("height"))
    except (TypeError, ValueError):
        return False
    return w > h * 1.05


def refine_aux_assignment(
    screen: dict[str, Any],
    *,
    assets_map: Mapping[str, Any] | None = None,
) -> bool:
    """Ensure the flattest aux slot does not hold the highest-crop_risk landscape.

    Main slot assignment is never swapped. Returns True if a swap occurred.
    """
    assets_map = assets_map or {}
    slots = list(screen.get("slots") or [])
    aux_idxs = [
        i for i, slot in enumerate(slots) if str(slot.get("role") or "") != "main"
    ]
    if len(aux_idxs) < 2:
        return False

    def _da(i: int) -> float:
        try:
            return float(slots[i].get("displayAspect") or 0.0)
        except (TypeError, ValueError):
            return 0.0

    # Flattest aux = highest displayAspect (wide / short cell)
    flat_idx = max(aux_idxs, key=_da)
    flat_da = _da(flat_idx)
    if flat_da <= 0:
        return False

    land_aux: list[tuple[int, float]] = []
    for i in aux_idxs:
        aid = slots[i].get("assetId")
        asset = assets_map.get(aid) if aid else None
        if not _is_landscape_asset(asset if isinstance(asset, Mapping) else None):
            continue
        risk = crop_risk_for_pair(
            asset if isinstance(asset, Mapping) else None, flat_da
        )
        land_aux.append((i, risk))

    if len(land_aux) < 2:
        return False

    worst_idx, worst_risk = max(land_aux, key=lambda t: (t[1], -t[0]))
    if worst_idx != flat_idx:
        return False

    donors = [(i, r) for i, r in land_aux if i != flat_idx]
    if not donors:
        return False
    donor_idx, donor_risk = min(donors, key=lambda t: (t[1], t[0]))
    if donor_risk >= worst_risk - 1e-9:
        return False

    a_flat = slots[flat_idx].get("assetId")
    a_donor = slots[donor_idx].get("assetId")
    slots[flat_idx]["assetId"] = a_donor
    slots[donor_idx]["assetId"] = a_flat
    screen["slots"] = slots
    return True
