"""ClosingScorer v1 (PRD §6.2)."""

from __future__ import annotations

from travelogue.cover_engine.pairing.policy import pairing_soft_bonus
from travelogue.domain.closing_view import (
    _closing_curated_score,
    _read_dominant_tone,
    _tone_saturation,
    _trip_screen_asset_ids_newest_first,
    asset_is_landscape,
)


def _last_two_screen_ids(trip: dict) -> set[str]:
    ordered = _trip_screen_asset_ids_newest_first(trip)
    return set(ordered[:2])


def _avg_luma(asset: dict) -> float:
    for key in ("avgLuma", "lowerLuma", "luma"):
        raw = asset.get(key)
        if raw is None:
            continue
        try:
            return float(raw)
        except (TypeError, ValueError):
            continue
    # derive rough luma from dominant tone
    tone = _read_dominant_tone(asset)
    if not tone or len(tone) < 7:
        return 0.45
    try:
        r = int(tone[1:3], 16) / 255.0
        g = int(tone[3:5], 16) / 255.0
        b = int(tone[5:7], 16) / 255.0
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    except (TypeError, ValueError):
        return 0.45


def score_closing_candidate(
    trip: dict,
    asset_id: str,
    asset: dict,
    *,
    screen_used_ids: set[str],
    prefer_landscape: bool,
    cover: dict | None,
    soft_weight: float = 0.35,
    recency_index: int = 0,
    recency_count: int = 1,
) -> float:
    """Higher is better."""
    score = 0.0

    # unused_bonus
    if asset_id not in screen_used_ids:
        score += 1.20
    else:
        score -= 0.15

    # not_last_screens_penalty
    if asset_id in _last_two_screen_ids(trip):
        score -= 0.55

    # low_saturation (capped) — reuse curated score (lower sat better)
    curated = _closing_curated_score(asset)
    # curated is sat + evening(-); invert into bonus with cap
    sat = _tone_saturation(_read_dominant_tone(asset))
    score += min(0.45, max(0.0, 0.55 - sat))
    # evening already in curated as negative sat-like; give capped bonus
    if curated < sat - 0.05:
        score += 0.22

    # landscape_for_web — must dominate soft recency (align legacy heuristic)
    if prefer_landscape and asset_is_landscape(asset):
        score += 1.10
    elif prefer_landscape and not asset_is_landscape(asset):
        score -= 0.45

    # recency_soft — later assets slightly preferred
    if recency_count > 1:
        score += 0.15 * (recency_index / float(recency_count - 1))

    # pairing_contrast (PAIR-S*)
    score += pairing_soft_bonus(cover, asset, soft_weight=soft_weight)

    # title_safe_closing soft — mid lower luma preferred
    luma = _avg_luma(asset)
    if 0.22 <= luma <= 0.72:
        score += 0.18
    elif luma < 0.12:
        score -= 0.35  # dead_black_penalty
    elif luma > 0.88:
        score -= 0.15

    return round(score, 6)


def pick_best_closing_scored(
    trip: dict,
    candidates: list[str],
    assets: dict[str, dict],
    *,
    screen_used_ids: set[str],
    prefer_landscape: bool,
    cover: dict | None,
    soft_weight: float = 0.35,
) -> tuple[str | None, dict[str, float]]:
    if not candidates:
        return None, {}
    n = len(candidates)
    scores: dict[str, float] = {}
    best_id: str | None = None
    best_score = float("-inf")
    for i, aid in enumerate(candidates):
        asset = assets.get(aid)
        if not asset:
            continue
        # candidates are newest-first in unused+screen order; map index for soft recency
        s = score_closing_candidate(
            trip,
            aid,
            asset,
            screen_used_ids=screen_used_ids,
            prefer_landscape=prefer_landscape,
            cover=cover,
            soft_weight=soft_weight,
            recency_index=n - 1 - i,
            recency_count=n,
        )
        scores[aid] = s
        if s > best_score:
            best_score = s
            best_id = aid
    return best_id, scores
