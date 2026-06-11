"""Flickr-style justified row layout for portrait-heavy screens (P19 R-403, MIT)."""

from __future__ import annotations

from dataclasses import dataclass

from travelogue.curation.asset_subject import portrait_fit_for_asset
from travelogue.curation.layout_planner import AspectKind
from travelogue.curation.screen_planner import _is_std_portrait_id, _make_screen


@dataclass(frozen=True)
class JustifiedItem:
    asset_id: str
    width_ratio: float


@dataclass(frozen=True)
class JustifiedRow:
    height_ratio: float
    items: tuple[JustifiedItem, ...]


def _asset_aspect_ratio(asset: dict) -> float:
    try:
        w = float(asset.get("width") or asset.get("displayWidth") or 0)
        h = float(asset.get("height") or asset.get("displayHeight") or 0)
    except (TypeError, ValueError):
        w, h = 0.0, 0.0
    if w > 0 and h > 0:
        return max(w / h, 0.05)
    try:
        ar = float(asset.get("aspectRatio") or 0)
        if ar > 0:
            return ar
    except (TypeError, ValueError):
        pass
    return 0.75


def _normalize_row(
    row: list[tuple[str, float]],
    row_width: float,
    gap: float,
) -> tuple[JustifiedItem, ...]:
    if not row:
        return ()
    gaps = gap * max(len(row) - 1, 0)
    total = sum(w for _, w in row) + gaps
    scale = row_width / total if total > 0 else 1.0
    return tuple(
        JustifiedItem(asset_id=aid, width_ratio=w * scale) for aid, w in row
    )


def layout_justified_rows(
    asset_ids: list[str],
    assets_map: dict[str, dict],
    *,
    row_width: float = 1.0,
    target_row_height: float = 0.38,
    gap_ratio: float = 0.025,
) -> list[JustifiedRow]:
    """Pack assets into rows with variable widths at a shared row height."""
    if not asset_ids:
        return []
    gap = gap_ratio
    pending: list[tuple[str, float]] = []
    for aid in asset_ids:
        ar = _asset_aspect_ratio(assets_map.get(aid, {}))
        w_at_h = ar * target_row_height
        pending.append((aid, w_at_h))

    raw_rows: list[tuple[JustifiedItem, ...]] = []
    current: list[tuple[str, float]] = []
    current_sum = 0.0
    for aid, w_unit in pending:
        extra = gap if current else 0.0
        if current and current_sum + extra + w_unit > row_width:
            raw_rows.append(_normalize_row(current, row_width, gap))
            current = []
            current_sum = 0.0
            extra = 0.0
        current.append((aid, w_unit))
        current_sum += w_unit + extra
    if current:
        raw_rows.append(_normalize_row(current, row_width, gap))

    if not raw_rows:
        return []
    height_each = 1.0 / len(raw_rows)
    return [
        JustifiedRow(height_ratio=height_each, items=items) for items in raw_rows
    ]


def can_use_justified_row(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    *,
    min_portrait_ratio: float = 0.75,
) -> bool:
    if len(asset_ids) < 4:
        return False
    portraits = sum(1 for aid in asset_ids if _is_std_portrait_id(aid, aspects))
    return portraits / len(asset_ids) >= min_portrait_ratio


def build_justified_screen(
    pattern_id: str,
    ordered_ids: list[str],
    assets_map: dict[str, dict],
    *,
    screen_id: str = "",
) -> dict:
    rows = layout_justified_rows(ordered_ids, assets_map)
    flat_slots: list[dict] = []
    justified_rows: list[dict] = []
    slot_idx = 0
    for row in rows:
        row_items: list[dict] = []
        for item in row.items:
            fit = portrait_fit_for_asset(assets_map.get(item.asset_id, {}), default="cover")
            slot = {
                "assetId": item.asset_id,
                "slot": slot_idx,
                "role": "portrait",
                "fit": fit,
                "widthRatio": item.width_ratio,
            }
            flat_slots.append(slot)
            row_items.append(
                {
                    "assetId": item.asset_id,
                    "slot": slot_idx,
                    "widthRatio": item.width_ratio,
                    "role": "portrait",
                    "fit": fit,
                }
            )
            slot_idx += 1
        justified_rows.append(
            {
                "heightRatio": row.height_ratio,
                "items": row_items,
            }
        )
    screen = _make_screen(pattern_id, screen_id=screen_id, slots=flat_slots)
    screen["layoutKind"] = "justified"
    screen["justifiedRows"] = justified_rows
    return screen
