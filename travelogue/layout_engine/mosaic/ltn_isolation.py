"""LTN AC-C-01 · isolation replay for portrait3_after_failed_mcs5_rate.

Quota / rhythm / density budget are ignored — only MCS hard_valid → winner.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from travelogue.config import MosaicConfig
from travelogue.layout_contract.orientations import AspectKind
from travelogue.layout_engine.mosaic.candidates import (
    generate_window_candidates_with_rejections,
)
from travelogue.layout_engine.mosaic.compose import pick_best_window

_STACK3_PATTERNS = frozenset(
    {
        "screen-portrait-3",
        "screen-portrait-3-editorial",
        "screen-landscape-3",
        "screen-portrait-1-landscape-2",
    }
)


@dataclass(frozen=True)
class IsolationFailedWindow:
    start: int
    size: int
    asset_ids: tuple[str, ...]


def isolation_failed_mcs_windows(
    ordered_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    cfg: MosaicConfig | None = None,
    sizes: tuple[int, ...] = (4, 5, 6),
) -> list[IsolationFailedWindow]:
    """Windows with ≥1 hard_valid candidate but no MCS winner (layout_state=None)."""
    mosaic_cfg = cfg or MosaicConfig(enabled=True, min_candidate_score=0.35)
    failed: list[IsolationFailedWindow] = []
    n = len(ordered_ids)
    for size in sizes:
        if size < 4 or n < size:
            continue
        for start in range(0, n - size + 1):
            window = ordered_ids[start : start + size]
            bundle = generate_window_candidates_with_rejections(
                window,
                aspects,
                assets_map,
                cfg=mosaic_cfg,
            )
            hard = [c for c in bundle.candidates if getattr(c, "hard_valid", True)]
            if not hard:
                continue
            pick = pick_best_window(
                window,
                aspects,
                assets_map,
                cfg=mosaic_cfg,
                window_size=size,
                layout_state=None,
                window_start=start,
            )
            if pick.screen is None or pick.used_legacy:
                failed.append(
                    IsolationFailedWindow(
                        start=start,
                        size=size,
                        asset_ids=tuple(window),
                    )
                )
    return failed


def _content_screens(chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for ch in chapters or []:
        if not isinstance(ch, dict):
            continue
        for sc in ch.get("screens") or []:
            if not isinstance(sc, dict):
                continue
            if "breath" in str(sc.get("patternId") or ""):
                continue
            out.append(sc)
    return out


def _screen_aids(screen: dict[str, Any]) -> set[str]:
    return {
        str(sl.get("assetId"))
        for sl in (screen.get("slots") or [])
        if isinstance(sl, dict) and sl.get("assetId")
    }


def portrait3_after_failed_mcs5_rate_strict(
    chapters: list[dict[str, Any]],
    *,
    ordered_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    cfg: MosaicConfig | None = None,
) -> float | None:
    """AC-C-01 strict rate. None when denominator is 0."""
    failed = isolation_failed_mcs_windows(
        ordered_ids, aspects, assets_map, cfg=cfg
    )
    if not failed:
        return None

    screens = _content_screens(chapters)
    # Map assetId → content screen indices (for adjacency).
    aid_to_idx: dict[str, list[int]] = {}
    for i, sc in enumerate(screens):
        for aid in _screen_aids(sc):
            aid_to_idx.setdefault(aid, []).append(i)

    hits = 0
    for fw in failed:
        win_aids = set(fw.asset_ids)
        hit = False
        for i, sc in enumerate(screens):
            pid = str(sc.get("patternId") or "")
            if pid not in _STACK3_PATTERNS:
                continue
            sc_aids = _screen_aids(sc)
            if not (win_aids & sc_aids):
                continue
            # Adjacent in reading order: any shared asset's screen neighbors the stack,
            # or stack index is next to a screen that holds other window assets.
            neighbor_idxs = set()
            for aid in win_aids:
                for j in aid_to_idx.get(aid, []):
                    neighbor_idxs.add(j)
                    neighbor_idxs.add(j - 1)
                    neighbor_idxs.add(j + 1)
            if i in neighbor_idxs or any(abs(i - j) <= 1 for j in neighbor_idxs):
                hit = True
                break
        if hit:
            hits += 1
    return round(hits / len(failed), 6)


def compute_ac_c01_on_trip(trip: dict[str, Any]) -> dict[str, Any]:
    """Convenience: strict AC-C-01 from a trip dict (chapters + assets)."""
    from travelogue.curation.layout_planner import aspect_kind_for_asset

    assets = trip.get("assets") or []
    assets_map = {str(a["id"]): a for a in assets if a.get("id")}
    aspects: dict[str, AspectKind] = {
        aid: aspect_kind_for_asset(a) for aid, a in assets_map.items()  # type: ignore[misc]
    }
    cur = trip.get("curation") if isinstance(trip.get("curation"), dict) else {}
    ordered = [str(x) for x in (cur.get("displayedAssetIds") or []) if str(x) in assets_map]
    if not ordered:
        ordered = list(assets_map.keys())
    rate = portrait3_after_failed_mcs5_rate_strict(
        list(trip.get("chapters") or []),
        ordered_ids=ordered,
        aspects=aspects,
        assets_map=assets_map,
    )
    failed = isolation_failed_mcs_windows(ordered, aspects, assets_map)
    return {
        "ac": "AC-C-01",
        "rate": rate,
        "failedWindowCount": len(failed),
        "ok": rate is None or rate <= 0.5,  # absolute health band when no baseline
    }
