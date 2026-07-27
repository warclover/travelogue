"""LTN C4 · takenAt-based coarse segments + signature routing.

Segments are planner memory only (not persisted as sceneId). Windows must not
cross segment boundaries. Signature ``(nP, nL, cohesive)`` narrows the pattern
whitelist; misses fall back to the full candidate set (never a silent empty).
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Iterable

from travelogue.domain.time_segments import asset_city
from travelogue.layout_contract.burst import parse_taken_ts
from travelogue.layout_contract.orientations import (
    AspectKind,
    is_std_landscape,
    is_std_portrait,
)
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_LANDSCAPE_4,
    PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO,
    PATTERN_MOSAIC_5_2P3L_PORTRAIT_HERO_RAIL,
    PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK,
    PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD,
    PATTERN_MOSAIC_5_HERO_3_2_PLUS_4,
    PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
    PATTERN_PORTRAIT_2_LANDSCAPE_2,
    PATTERN_PORTRAIT_4,
)
from travelogue.layout_engine.mosaic.pattern_catalog import MosaicPattern

# Summit D-04 · cohesive when takenAt span within the window is short.
COHESIVE_SPAN_S = 300.0
GAP_FLOOR_S = 120.0
GAP_CEIL_S = 1800.0
GAP_MEDIAN_MULT = 3.0

# Pattern ids kept as strings when not exported from constants.
PATTERN_MOSAIC_4_HERO = "screen-mosaic-4-hero-70-sidebar"
PATTERN_MOSAIC_4_2L2P_WEIGHTED = "screen-mosaic-4-2l2p-weighted"

# (nP, nL, cohesive) → whitelist. Unknown keys → keep input set (signature_fallback).
# 2P2L includes contract-extra weighted so TC+signature still exercises clone gate.
SIGNATURE_WHITELIST: dict[tuple[int, int, bool], frozenset[str]] = {
    (0, 4, True): frozenset({PATTERN_LANDSCAPE_4, PATTERN_MOSAIC_4_HERO}),
    (0, 4, False): frozenset({PATTERN_LANDSCAPE_4}),
    (4, 0, True): frozenset({PATTERN_PORTRAIT_4}),
    (4, 0, False): frozenset({PATTERN_PORTRAIT_4}),
    (2, 2, True): frozenset(
        {PATTERN_PORTRAIT_2_LANDSCAPE_2, PATTERN_MOSAIC_4_2L2P_WEIGHTED}
    ),
    (2, 2, False): frozenset(
        {PATTERN_PORTRAIT_2_LANDSCAPE_2, PATTERN_MOSAIC_4_2L2P_WEIGHTED}
    ),
    # Summit / MTSO: (1,4) → 横主 + 竖主双分支；(2,3) → 主从继任（experimental）
    (1, 4, True): frozenset(
        {
            PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
            PATTERN_MOSAIC_5_HERO_3_2_PLUS_4,
            PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO,
        }
    ),
    (1, 4, False): frozenset(
        {
            PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
            PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO,
        }
    ),
    (2, 3, True): frozenset({PATTERN_MOSAIC_5_2P3L_PORTRAIT_HERO_RAIL}),
    (2, 3, False): frozenset({PATTERN_MOSAIC_5_2P3L_PORTRAIT_HERO_RAIL}),
    # 3P2L · left portrait-hero quad / lp-stack soft family
    (3, 2, True): frozenset(
        {
            PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD,
            PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK,
        }
    ),
    (3, 2, False): frozenset(
        {
            PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD,
            PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK,
        }
    ),
}


@dataclass(frozen=True)
class CoarseSegment:
    """Inclusive start / exclusive end into chapter ``ids`` order."""

    start: int
    end: int

    @property
    def size(self) -> int:
        return self.end - self.start


def _gap_threshold_s(gaps: list[float]) -> float:
    if not gaps:
        return GAP_FLOOR_S
    return min(GAP_CEIL_S, max(GAP_FLOOR_S, GAP_MEDIAN_MULT * float(median(gaps))))


def build_coarse_segments(
    ids: list[str],
    assets_map: dict[str, dict],
) -> list[CoarseSegment]:
    """Split a takenAt-sorted chapter id list into coarse time/city segments.

    Rules (R-C4):
    - Primary signal = ``takenAt`` (not degenerate burstGroupId).
    - Split when gap > min(1800, max(120, 3×median_gap)) or city changes.
    - Missing timestamps stick to the previous segment.
    """
    if not ids:
        return []
    ts_list: list[float | None] = [
        parse_taken_ts(assets_map.get(aid, {}) or {}) for aid in ids
    ]
    gaps: list[float] = []
    for i in range(1, len(ids)):
        a, b = ts_list[i - 1], ts_list[i]
        if a is not None and b is not None and b >= a:
            gaps.append(b - a)
    threshold = _gap_threshold_s(gaps)

    segments: list[CoarseSegment] = []
    seg_start = 0
    for i in range(1, len(ids)):
        prev_ts, cur_ts = ts_list[i - 1], ts_list[i]
        # Missing timestamp → stick to previous segment (no split).
        if cur_ts is None or prev_ts is None:
            continue
        gap = cur_ts - prev_ts
        prev_city = asset_city(assets_map.get(ids[i - 1], {}) or {})
        cur_city = asset_city(assets_map.get(ids[i], {}) or {})
        city_change = (
            prev_city is not None
            and cur_city is not None
            and prev_city != cur_city
        )
        if gap > threshold or city_change:
            segments.append(CoarseSegment(seg_start, i))
            seg_start = i
    segments.append(CoarseSegment(seg_start, len(ids)))
    return segments


def max_window_size_in_segment(
    segments: list[CoarseSegment] | list[tuple[int, int]] | None,
    start: int,
) -> int:
    """Largest window that stays inside the segment containing ``start``.

    Empty / missing segments → no clamp (legacy callers).
    """
    if not segments:
        return 10**9
    for seg in segments:
        s = seg.start if isinstance(seg, CoarseSegment) else int(seg[0])
        e = seg.end if isinstance(seg, CoarseSegment) else int(seg[1])
        if s <= start < e:
            return e - start
    return 10**9


def window_crosses_segment(
    segments: list[CoarseSegment] | list[tuple[int, int]] | None,
    start: int,
    size: int,
) -> bool:
    if not segments or size <= 0:
        return False
    return size > max_window_size_in_segment(segments, start)


def count_portrait_landscape(
    asset_ids: Iterable[str],
    aspects: dict[str, AspectKind],
) -> tuple[int, int]:
    n_p = 0
    n_l = 0
    for aid in asset_ids:
        kind = aspects.get(aid, "square")
        if is_std_portrait(kind):
            n_p += 1
        elif is_std_landscape(kind):
            n_l += 1
    return n_p, n_l


def window_is_cohesive(
    asset_ids: list[str],
    assets_map: dict[str, dict],
    *,
    span_s: float = COHESIVE_SPAN_S,
) -> bool:
    stamps = [
        t
        for aid in asset_ids
        if (t := parse_taken_ts(assets_map.get(aid, {}) or {})) is not None
    ]
    if len(stamps) < 2:
        return False
    return (max(stamps) - min(stamps)) <= span_s


def signature_key(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
) -> tuple[int, int, bool]:
    n_p, n_l = count_portrait_landscape(asset_ids, aspects)
    return n_p, n_l, window_is_cohesive(asset_ids, assets_map)


def apply_signature_route(
    patterns: list[MosaicPattern],
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
) -> tuple[list[MosaicPattern], str]:
    """Narrow patterns by signature whitelist.

    Miss (unknown key or empty intersection) → keep the input set and return
    ``signature_fallback`` (never a silent empty). Callers on the TC path should
    prefer the prior contract source when logging a miss.
    """
    if not patterns:
        return patterns, "signature_fallback"
    key = signature_key(asset_ids, aspects, assets_map)
    whitelist = SIGNATURE_WHITELIST.get(key)
    if whitelist is None:
        return patterns, "signature_fallback"
    narrowed = [p for p in patterns if p.pattern_id in whitelist]
    if not narrowed:
        return patterns, "signature_fallback"
    return narrowed, "signature"
