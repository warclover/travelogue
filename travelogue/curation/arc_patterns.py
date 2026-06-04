"""Adaptive narrative arc: flat / moderate / dynamic (Phase 3a)."""

from __future__ import annotations

import statistics
from typing import Any

ARC_OPEN = "open"
ARC_RISE = "rise"
ARC_PEAK = "peak"
ARC_FALL = "fall"
ARC_CLOSE = "close"
ARC_MOMENT = "moment"

ArcProfile = str  # flat | moderate | dynamic

FIVE_BEAT_SEQUENCE = (ARC_OPEN, ARC_RISE, ARC_PEAK, ARC_FALL, ARC_CLOSE)

_PEAK_PATTERNS = frozenset(
    {
        "screen-mosaic-5-main-portrait-3land",
        "screen-mosaic-5-main-landscape-2portrait-2land",
        "screen-mosaic-5-2portrait-3land-balanced",
        "screen-mosaic-5-3portrait-2land-balanced",
        "screen-mosaic-5-main-hero-plus-4",
        "screen-portrait-grid-8",
        "screen-landscape-4",
    }
)

_ARC_PATTERN_PREFERENCES: dict[str, frozenset[str]] = {
    ARC_OPEN: frozenset(
        {
            "screen-portrait-1",
            "screen-landscape-1",
            "screen-portrait-3",
        }
    ),
    ARC_RISE: frozenset(
        {
            "screen-portrait-3",
            "screen-landscape-2",
            "screen-landscape-3",
        }
    ),
    ARC_PEAK: frozenset(_PEAK_PATTERNS),
    ARC_FALL: frozenset(
        {
            "screen-landscape-2",
            "screen-portrait-2",
            "screen-portrait-1-landscape-2",
        }
    ),
    ARC_CLOSE: frozenset(
        {
            "screen-portrait-1",
            "screen-landscape-1",
            "screen-portrait-2",
        }
    ),
    ARC_MOMENT: frozenset(
        {
            "screen-portrait-2",
            "screen-landscape-2",
            "screen-portrait-3",
            "screen-landscape-1",
        }
    ),
}


def _coefficient_of_variation(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = statistics.fmean(values)
    if mean <= 1e-9:
        return 0.0
    stdev = statistics.pstdev(values)
    return stdev / mean


def infer_arc_profile(
    layout_assets: list[dict],
    buckets: list[list[str]],
    *,
    flat_threshold: float = 0.08,
) -> ArcProfile:
    """
    Infer trip narrative energy from quality/tag variance.
    flat → 3-beat calm; moderate → 4-beat; dynamic → full 5-beat.
    """
    from travelogue.curation.asset_quality import asset_sharpness
    from travelogue.curation.curate_scoring import hero_score, median_sharpness

    if not layout_assets:
        return "flat"

    assets_by_id = {a["id"]: a for a in layout_assets if a.get("id")}
    med = median_sharpness(layout_assets)
    hero_vals = [hero_score(a, median_sharp=med) for a in layout_assets]
    sharp_vals = [asset_sharpness(a) for a in layout_assets if asset_sharpness(a) > 0]

    hero_cv = _coefficient_of_variation([v for v in hero_vals if v > 0])
    sharp_cv = _coefficient_of_variation(sharp_vals)

    tag_richness: list[float] = []
    for bucket in buckets:
        if not bucket:
            continue
        tag_sets = [set((assets_by_id.get(aid) or {}).get("tags") or []) for aid in bucket]
        uniq = len({t for ts in tag_sets for t in ts})
        tag_richness.append(uniq / max(len(bucket), 1))

    tag_cv = _coefficient_of_variation(tag_richness) if len(tag_richness) > 1 else 0.0
    combined = max(hero_cv, sharp_cv * 0.6, tag_cv * 0.4)

    if combined < flat_threshold:
        return "flat"
    if combined < flat_threshold * 2.5:
        return "moderate"
    return "dynamic"


def arc_segments_for_trip(total: int, profile: ArcProfile) -> list[str]:
    """Return arc segment label per chapter index (1-based length == total)."""
    if total <= 0:
        return []
    if profile == "flat":
        if total == 1:
            return [ARC_OPEN]
        if total == 2:
            return [ARC_OPEN, ARC_CLOSE]
        return [ARC_OPEN] + [ARC_MOMENT] * (total - 2) + [ARC_CLOSE]

    if profile == "moderate":
        peak_idx = (total + 1) // 2
        segs: list[str] = []
        for i in range(1, total + 1):
            if i == 1:
                segs.append(ARC_OPEN)
            elif i == total:
                segs.append(ARC_CLOSE)
            elif i == peak_idx:
                segs.append(ARC_PEAK)
            elif i == 2 and total > 3:
                segs.append(ARC_RISE)
            elif i == total - 1 and total > 4:
                segs.append(ARC_FALL)
            else:
                segs.append(ARC_MOMENT)
        return segs

    # dynamic: legacy five-beat stretch
    return [arc_segment_for_chapter(i + 1, total, profile="dynamic") for i in range(total)]


def arc_segment_for_chapter(
    index: int,
    total: int,
    *,
    profile: ArcProfile = "dynamic",
) -> str:
    if profile != "dynamic":
        segs = arc_segments_for_trip(total, profile)
        if 1 <= index <= len(segs):
            return segs[index - 1]
    if total <= 0:
        return ARC_OPEN
    if total == 1:
        return ARC_OPEN
    if total == 2:
        return ARC_OPEN if index == 1 else ARC_CLOSE
    if total == 3:
        return {1: ARC_OPEN, 2: ARC_PEAK, 3: ARC_CLOSE}.get(index, ARC_RISE)
    if total == 4:
        return {1: ARC_OPEN, 2: ARC_RISE, 3: ARC_FALL, 4: ARC_CLOSE}.get(index, ARC_RISE)
    if index == 1:
        return ARC_OPEN
    if index == total:
        return ARC_CLOSE
    if index == 2:
        return ARC_RISE
    if index == total - 1:
        return ARC_FALL
    if index == 3 or (total >= 6 and index == total // 2):
        return ARC_PEAK
    return ARC_RISE if index < total // 2 else ARC_FALL


def arc_pattern_bonus(
    pattern_id: str,
    arc_segment: str,
    *,
    profile: ArcProfile = "dynamic",
) -> float:
    if profile == "flat" and pattern_id in _PEAK_PATTERNS:
        return 0.5
    prefs = _ARC_PATTERN_PREFERENCES.get(arc_segment)
    if not prefs:
        return 0.5
    if pattern_id in prefs:
        return 1.0
    return 0.3


def arc_pattern_hint_for_bucket(
    index: int,
    total: int,
    *,
    profile: ArcProfile = "dynamic",
) -> str | None:
    seg = arc_segment_for_chapter(index, total, profile=profile)
    if seg == ARC_OPEN:
        return "open"
    if seg == ARC_CLOSE:
        return "close"
    return None


def arc_profile_to_dict(profile: ArcProfile) -> dict[str, Any]:
    return {"profile": profile, "beats": {"flat": 3, "moderate": 4, "dynamic": 5}.get(profile, 5)}
