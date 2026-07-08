"""Editorial portrait row (screen-portrait-3-editorial) · planner/MCS hook."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Literal

from travelogue.layout_contract.subject import asset_has_person

if TYPE_CHECKING:
    from travelogue.config import AppConfig

LayoutFit = Literal["cover", "contain"]

PATTERN_PORTRAIT_3 = "screen-portrait-3"
PATTERN_PORTRAIT_3_EDITORIAL = "screen-portrait-3-editorial"
LAYOUT_HINT_PORTRAIT_ROW_EDITORIAL = "portrait-row-editorial"
EditorialScope = str  # all | person | scenery

DEFAULT_EDITORIAL_ROW_WIDTH_PX = 960.0
DEFAULT_EDITORIAL_ROW_GAP_PX = 36.0


def editorial_row_fit_mode(
    *,
    trip_id: str,
    screen_id: str,
    asset_ids: tuple[str, ...],
) -> LayoutFit:
    """Deterministic pseudo-random cover/contain (PRD §4.4 · no builtin hash())."""
    key = f"{trip_id}:{screen_id}:{','.join(sorted(asset_ids))}"
    digest = hashlib.sha256(key.encode()).hexdigest()
    return "cover" if int(digest[:8], 16) % 2 == 0 else "contain"


def editorial_row_screen_has_person(
    screen: dict,
    assets_map: dict[str, dict],
) -> bool:
    return any(
        asset_has_person(assets_map.get(str(s.get("assetId") or ""), {}))
        for s in screen.get("slots") or []
    )


def resolve_editorial_row_uniform_fit(
    screen: dict,
    assets_map: dict[str, dict],
    *,
    trip: dict | None = None,
) -> LayoutFit:
    if editorial_row_screen_has_person(screen, assets_map):
        return "contain"
    asset_ids = tuple(
        str(s.get("assetId") or "")
        for s in screen.get("slots") or []
        if s.get("assetId")
    )
    screen_id = str(screen.get("screenId") or "").strip()
    if not screen_id or not asset_ids:
        return "contain"
    trip_id = str((trip or {}).get("tripId") or "")
    return editorial_row_fit_mode(
        trip_id=trip_id,
        screen_id=screen_id,
        asset_ids=asset_ids,
    )


def apply_editorial_row_slot_fits(
    screen: dict,
    assets_map: dict[str, dict],
    *,
    trip: dict | None = None,
) -> dict:
    """Set uniform screen-level fit on editorial rows (after ``screenId`` is stable)."""
    if str(screen.get("patternId") or "") != PATTERN_PORTRAIT_3_EDITORIAL:
        return screen
    slots = screen.get("slots") or []
    if not slots:
        return screen
    fit = resolve_editorial_row_uniform_fit(screen, assets_map, trip=trip)
    screen["slots"] = [{**dict(s), "fit": fit} for s in slots]
    return screen


def editorial_row_column_width_px(
    *,
    row_width_px: float = DEFAULT_EDITORIAL_ROW_WIDTH_PX,
    gap_px: float = DEFAULT_EDITORIAL_ROW_GAP_PX,
) -> float:
    return (row_width_px - 2 * gap_px) / 3.0


def editorial_row_ar_from_assets(
    asset_ids: list[str],
    assets_map: dict[str, dict],
    *,
    row_width_px: float = DEFAULT_EDITORIAL_ROW_WIDTH_PX,
    gap_px: float = DEFAULT_EDITORIAL_ROW_GAP_PX,
) -> float:
    """Column width / max scaled height (PRD §3.5 · cover row ``--editorial-row-ar``)."""
    col_w = editorial_row_column_width_px(row_width_px=row_width_px, gap_px=gap_px)
    heights: list[float] = []
    for aid in asset_ids:
        asset = assets_map.get(aid) or {}
        w = int(asset.get("nativeWidth") or asset.get("width") or 0)
        h = int(asset.get("nativeHeight") or asset.get("height") or 0)
        if w <= 0 or h <= 0:
            continue
        heights.append(col_w * h / w)
    if not heights:
        return 9 / 16
    return col_w / max(heights)


def editorial_portrait_row_config(cfg: AppConfig | None = None):
    from travelogue.config import get_config

    app = cfg or get_config()
    return app.layout.editorial_portrait_row


def is_editorial_portrait_row_enabled(
    trip: dict | None,
    cfg: AppConfig | None = None,
) -> bool:
    """trip.export.editorialPortraitRow > trip_allowlist > global enabled."""
    epr = editorial_portrait_row_config(cfg)
    if trip:
        export = trip.get("export") or {}
        override = export.get("editorialPortraitRow")
        if override is not None:
            return bool(override)
        trip_id = str(trip.get("tripId") or "").strip()
        if trip_id and trip_id in epr.trip_allowlist:
            return True
    return bool(epr.enabled)


def editorial_scope_matches(
    scope: EditorialScope,
    asset_ids: list[str],
    assets_map: dict[str, dict],
) -> bool:
    if not asset_ids:
        return False
    has_person = any(asset_has_person(assets_map.get(aid, {})) for aid in asset_ids)
    all_person = all(asset_has_person(assets_map.get(aid, {})) for aid in asset_ids)
    if scope == "person":
        return all_person
    if scope == "scenery":
        return not has_person
    return True  # all


def maybe_editorial_portrait_row(
    pattern_id: str,
    asset_ids: list[str],
    assets_map: dict[str, dict],
    *,
    trip: dict | None = None,
    cfg: AppConfig | None = None,
) -> tuple[str, str | None]:
    """Return (pattern_id, layout_hint). hint None = leave existing hint unchanged."""
    if pattern_id != PATTERN_PORTRAIT_3:
        return pattern_id, None
    epr = editorial_portrait_row_config(cfg)
    if not is_editorial_portrait_row_enabled(trip, cfg):
        return pattern_id, None
    if PATTERN_PORTRAIT_3 not in epr.replace_patterns:
        return pattern_id, None
    if not editorial_scope_matches(epr.scope, asset_ids, assets_map):
        return pattern_id, None
    return PATTERN_PORTRAIT_3_EDITORIAL, LAYOUT_HINT_PORTRAIT_ROW_EDITORIAL


def apply_editorial_portrait_row_to_screen(
    screen: dict,
    assets_map: dict[str, dict],
    *,
    trip: dict | None = None,
    cfg: AppConfig | None = None,
) -> dict:
    pid = str(screen.get("patternId") or "")
    if pid != PATTERN_PORTRAIT_3:
        return screen
    asset_ids = [
        str(s.get("assetId") or "")
        for s in screen.get("slots") or []
        if s.get("assetId")
    ]
    new_pid, new_hint = maybe_editorial_portrait_row(
        pid, asset_ids, assets_map, trip=trip, cfg=cfg
    )
    if new_pid == pid:
        return screen
    out = dict(screen)
    out["patternId"] = new_pid
    out["layoutHint"] = new_hint
    return out
