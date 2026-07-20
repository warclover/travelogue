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

# Finished stack-3 patterns that may count toward the AC-C-01 numerator.
STACK3_PATTERNS = frozenset(
    {
        "screen-portrait-3",
        "screen-portrait-3-editorial",
        "screen-landscape-3",
        "screen-portrait-1-landscape-2",
    }
)

# Parity / portrait-tiler explicit triples — PRD excludes these from the numerator.
_TILER_PARITY_LAYOUT_HINTS = frozenset(
    {
        "person-triple",
        "portrait-row-editorial",
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
            hard = [c for c in bundle.candidates if c.hard_valid]
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


def is_tiler_or_parity_stack(screen: dict[str, Any]) -> bool:
    """True when stack-3 came from parity / portrait tiler (excluded from AC-C-01)."""
    hint = str(screen.get("layoutHint") or "").strip()
    return hint in _TILER_PARITY_LAYOUT_HINTS


def _ordered_asset_ids(trip: dict[str, Any], assets_map: dict[str, dict]) -> list[str]:
    from travelogue.curation.burst_utils import parse_taken_ts

    cur = trip.get("curation") if isinstance(trip.get("curation"), dict) else {}
    ordered = [
        str(x) for x in (cur.get("displayedAssetIds") or []) if str(x) in assets_map
    ]
    if ordered:
        return ordered
    return sorted(
        assets_map,
        key=lambda i: parse_taken_ts(assets_map[i]) or 0.0,
    )


def portrait3_after_failed_mcs5_rate_strict(
    chapters: list[dict[str, Any]],
    *,
    ordered_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    cfg: MosaicConfig | None = None,
    failed: list[IsolationFailedWindow] | None = None,
) -> float | None:
    """AC-C-01 strict rate. None when denominator is 0.

    Numerator: stack-3 screens that share ≥1 assetId with a failed window **and**
    are reading-order adjacent to other placements of that window's assets.
    Tiler / parity triples (layoutHint person-triple / portrait-row-editorial) excluded.
    """
    failed_windows = (
        failed
        if failed is not None
        else isolation_failed_mcs_windows(
            ordered_ids, aspects, assets_map, cfg=cfg
        )
    )
    if not failed_windows:
        return None

    screens = _content_screens(chapters)
    aid_to_idx: dict[str, list[int]] = {}
    for i, sc in enumerate(screens):
        for aid in _screen_aids(sc):
            aid_to_idx.setdefault(aid, []).append(i)

    hits = 0
    for fw in failed_windows:
        win_aids = set(fw.asset_ids)
        hit = False
        for i, sc in enumerate(screens):
            pid = str(sc.get("patternId") or "")
            if pid not in STACK3_PATTERNS:
                continue
            if is_tiler_or_parity_stack(sc):
                continue
            sc_aids = _screen_aids(sc)
            if not (win_aids & sc_aids):
                continue
            # Adjacency vs *other* screens that hold window assets (exclude self).
            # Sharing alone must not imply adjacency — far reuse must not count.
            # Empty other_idxs ⇒ shared assets only finished on this stack (post-fail
            # placement); count once tiler/parity already filtered out.
            other_idxs = {
                j
                for aid in win_aids
                for j in aid_to_idx.get(aid, [])
                if j != i
            }
            if not other_idxs or any(abs(i - j) <= 1 for j in other_idxs):
                hit = True
                break
        if hit:
            hits += 1
    return round(hits / len(failed_windows), 6)


def compare_ac_c01_to_baseline(
    rate: float | None,
    baseline_rate: float | None,
    *,
    reduce_factor: float = 0.5,
) -> dict[str, Any]:
    """Relative AC-C-01 gate: current ≤ baseline × reduce_factor (default ↓≥50%)."""
    if rate is None or baseline_rate is None:
        return {
            "ok": None,
            "deltaRatio": None,
            "baselineRate": baseline_rate,
            "currentRate": rate,
            "targetMax": None,
        }
    if baseline_rate <= 0:
        # No positive baseline → cannot claim relative reduction; treat null ok.
        return {
            "ok": None,
            "deltaRatio": None,
            "baselineRate": baseline_rate,
            "currentRate": rate,
            "targetMax": 0.0,
        }
    target = baseline_rate * reduce_factor
    return {
        "ok": rate <= target + 1e-9,
        "deltaRatio": round(rate / baseline_rate, 6),
        "baselineRate": baseline_rate,
        "currentRate": rate,
        "targetMax": round(target, 6),
    }


def compute_ac_c01_on_trip(
    trip: dict[str, Any],
    *,
    baseline_rate: float | None = None,
    cfg: MosaicConfig | None = None,
) -> dict[str, Any]:
    """Convenience: strict AC-C-01 from a trip dict (chapters + assets)."""
    from travelogue.curation.layout_planner import aspect_kind_for_asset

    assets = trip.get("assets") or []
    assets_map = {str(a["id"]): a for a in assets if a.get("id")}
    aspects: dict[str, AspectKind] = {
        aid: aspect_kind_for_asset(a) for aid, a in assets_map.items()  # type: ignore[misc]
    }
    ordered = _ordered_asset_ids(trip, assets_map)
    failed = isolation_failed_mcs_windows(
        ordered, aspects, assets_map, cfg=cfg
    )
    rate = portrait3_after_failed_mcs5_rate_strict(
        list(trip.get("chapters") or []),
        ordered_ids=ordered,
        aspects=aspects,
        assets_map=assets_map,
        cfg=cfg,
        failed=failed,
    )
    relative = compare_ac_c01_to_baseline(rate, baseline_rate)
    return {
        "ac": "AC-C-01",
        "rate": rate,
        "failedWindowCount": len(failed),
        # Absolute band is observational only — not the PRD AC gate.
        "withinAbsoluteBand": rate is None or rate <= 0.5,
        "baseline": relative,
        "ok": relative["ok"],
    }
