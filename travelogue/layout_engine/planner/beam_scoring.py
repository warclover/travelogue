"""Beam / screen-plan scoring (layout_engine)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from travelogue.layout_contract.orientations import AspectKind
from travelogue.layout_contract.scoring import (
    FEATURED_BEAM_BONUS_PER_ASSET,
    FEATURED_HERO_SEPARATION_HALVED,
    IncrementalScoreState,
    ScoreBreakdown,
    ScoringWeights,
    moment_secondary_plan_bonus,
    screen_dominant_tone,
)

def _plan_screen_key(screens: list[dict]) -> tuple[Any, ...]:
    return tuple(
        (
            screen.get("patternId"),
            tuple(
                (slot.get("assetId"), slot.get("role"))
                for slot in (screen.get("slots") or [])
            ),
        )
        for screen in screens
    )


def _weights_cache_fingerprint(weights: ScoringWeights) -> tuple[float, ...]:
    w = weights.normalized()
    return (
        round(w.aspect_match, 6),
        round(w.sharpness, 6),
        round(w.hero_separation, 6),
        round(w.temporal_coherence, 6),
        round(w.diversity, 6),
        round(w.arc_fit, 6),
        round(w.burst_integrity, 6),
        round(w.luminance_continuity, 6),
        round(w.subject_run, 6),
        round(w.tone_continuity, 6),
        round(w.layout_rhythm, 6),
        round(w.gravity_balance, 6),
        round(w.category_coherence, 6),
        round(w.cohort_coherence, 6),
    )


def _incremental_cache_key(
    screens: list[dict],
    *,
    weights: ScoringWeights,
    arc_segment: str | None,
    arc_profile: str,
    hero_asset_ids: set[str] | None,
    intent_arc_boost: float,
    featured_beam: bool,
    subject_run_tolerance: int,
    enable_gravity_balance: bool,
) -> tuple[Any, ...]:
    """P7-D2 cache key: screen plan + scoring context (beam may vary arc/hero per eval)."""
    return (
        _plan_screen_key(screens),
        _weights_cache_fingerprint(weights),
        arc_segment,
        arc_profile,
        frozenset(hero_asset_ids) if hero_asset_ids else None,
        round(intent_arc_boost, 6),
        featured_beam,
        subject_run_tolerance,
        enable_gravity_balance,
    )


def _aspect_kind_for_slot(slot: dict, aspects: Mapping[str, AspectKind]) -> AspectKind | None:
    aid = slot.get("assetId")
    if not aid:
        return None
    return aspects.get(aid)


def score_aspect_match(screen: dict, aspects: Mapping[str, AspectKind]) -> float:
    """1.0 when slot roles match asset aspect kinds; partial credit per slot."""
    slots = screen.get("slots") or []
    if not slots:
        return 0.0
    hits = 0
    counted = 0
    for slot in slots:
        kind = _aspect_kind_for_slot(slot, aspects)
        if kind is None:
            # Slot has no assetId or unknown aspect: exclude from the denominator
            # so empty/dangling slots don't drag the match rate toward 0.
            continue
        counted += 1
        role = (slot.get("role") or "").lower()
        if role == "portrait" and kind in ("portrait", "tall"):
            hits += 1
        elif role == "landscape" and kind in ("landscape", "panorama"):
            hits += 1
        elif role == "main" and kind in ("landscape", "panorama"):
            hits += 1
        elif role in ("", "any", "fill") or not role:
            hits += 1
        elif role == "square" and kind == "square":
            hits += 1
    return hits / counted if counted else 0.0


def score_sharpness(screen: dict, assets_by_id: Mapping[str, dict]) -> float:
    slots = screen.get("slots") or []
    scores: list[float] = []
    for slot in slots:
        aid = slot.get("assetId")
        if not aid:
            continue
        asset = assets_by_id.get(aid) or {}
        q = (asset.get("quality") or {}).get("sharpness")
        if q is None:
            scores.append(0.5)
        else:
            scores.append(min(1.0, max(0.0, float(q))))
    return sum(scores) / len(scores) if scores else 0.5


def score_temporal_coherence(screen: dict, assets_by_id: Mapping[str, dict]) -> float:
    from datetime import datetime

    slots = screen.get("slots") or []
    times: list[datetime] = []
    for slot in slots:
        aid = slot.get("assetId")
        if not aid:
            continue
        taken = (assets_by_id.get(aid) or {}).get("takenAt")
        if not taken:
            continue
        try:
            times.append(datetime.fromisoformat(str(taken).replace("Z", "+00:00")))
        except ValueError:
            continue
    if len(times) < 2:
        return 1.0
    span = (max(times) - min(times)).total_seconds()
    if span <= 60:
        return 1.0
    if span <= 3600:
        return 0.8
    if span <= 86400:
        return 0.5
    return 0.2


def score_burst_integrity(screens: list[dict], assets_by_id: Mapping[str, dict]) -> float:
    """Fraction of ingest burst groups kept intact within a single screen."""
    from travelogue.layout_contract.burst import ingest_burst_group_id

    groups: dict[str, list[str]] = {}
    for screen in screens:
        for slot in screen.get("slots") or []:
            aid = slot.get("assetId")
            if not aid:
                continue
            gid = ingest_burst_group_id(assets_by_id.get(aid) or {})
            if gid:
                groups.setdefault(gid, []).append(aid)

    if not groups:
        return 1.0

    preserved = 0
    for _gid, aids in groups.items():
        screen_ids: set[int] = set()
        for si, screen in enumerate(screens):
            slot_aids = {s.get("assetId") for s in (screen.get("slots") or [])}
            if set(aids) & slot_aids:
                screen_ids.add(si)
        if len(screen_ids) <= 1:
            preserved += 1
    return preserved / len(groups)


def asset_mean_luma(asset: dict) -> float:
    """Mean luminance in [0,1]; uses quality.meanLuma or tag heuristics."""
    q = asset.get("quality") or {}
    raw = q.get("meanLuma")
    if raw is not None:
        return min(1.0, max(0.0, float(raw)))
    tags = {str(t).lower() for t in (asset.get("tags") or []) if t}
    if tags & {"night", "dark", "indoor"}:
        return 0.22
    if tags & {"sunset", "golden", "dusk"}:
        return 0.55
    if tags & {"snow", "bright", "beach", "sky"}:
        return 0.82
    return 0.5


def screen_mean_luma(screen: dict, assets_by_id: Mapping[str, dict]) -> float:
    values: list[float] = []
    for slot in screen.get("slots") or []:
        aid = slot.get("assetId")
        if aid and aid in assets_by_id:
            values.append(asset_mean_luma(assets_by_id[aid]))
    return sum(values) / len(values) if values else 0.5


def score_luminance_continuity(
    screens: list[dict],
    assets_by_id: Mapping[str, dict],
    *,
    l_max: float = 0.35,
) -> float:
    """Adjacent-screen mean luminance smoothness (Phase 3a spread guard)."""
    from travelogue.layout_contract.longshot import is_breath_screen as _is_breath_screen

    screens = [
        s
        for s in screens
        if not _is_breath_screen(s)
        and any(slot.get("assetId") for slot in (s.get("slots") or []))
    ]
    if len(screens) < 2:
        return 1.0
    lumas = [screen_mean_luma(s, assets_by_id) for s in screens]
    penalties: list[float] = []
    for i in range(len(lumas) - 1):
        delta = abs(lumas[i + 1] - lumas[i])
        penalties.append(min(1.0, max(0.0, delta / l_max)))
    return 1.0 - sum(penalties) / len(penalties)


def score_tone_continuity(
    screens: list[dict],
    assets_by_id: Mapping[str, dict],
) -> float:
    """Adjacent-screen ΔE (CIE76) triangular window [10, 40], peak 25."""
    from travelogue.layout_contract.longshot import is_breath_screen as _is_breath_screen
    from travelogue.media.color_metrics import delta_e_cie76, triangular_score

    screens = [
        s
        for s in screens
        if not _is_breath_screen(s)
        and any(slot.get("assetId") for slot in (s.get("slots") or []))
    ]
    if len(screens) < 2:
        return 1.0
    scores: list[float] = []
    for i in range(len(screens) - 1):
        ta = screen_dominant_tone(screens[i], assets_by_id)
        tb = screen_dominant_tone(screens[i + 1], assets_by_id)
        if not ta or not tb:
            continue
        de = delta_e_cie76(ta, tb)
        scores.append(triangular_score(de, low=10.0, peak=25.0, high=40.0))
    if not scores:
        return 0.5
    return sum(scores) / len(scores)


def score_subject_run_soft(
    asset_ids: list[str],
    assets_by_id: Mapping[str, dict],
    *,
    target_run: int = 3,
    tolerance: int = 1,
) -> float:
    """Soft subject runs: allow up to `tolerance` outlier shots inside a run."""
    from travelogue.layout_contract.subject_tagging import subject_class_for_asset

    if len(asset_ids) < 2:
        return 1.0
    classes = [subject_class_for_asset(assets_by_id.get(aid) or {}) for aid in asset_ids]
    runs: list[tuple[str, int, int]] = []
    i = 0
    while i < len(classes):
        cls = classes[i]
        j = i + 1
        outliers = 0
        while j < len(classes):
            if classes[j] == cls:
                j += 1
                continue
            if outliers < tolerance:
                outliers += 1
                j += 1
                continue
            break
        effective = (j - i) - outliers * 0.5
        runs.append((cls, int(effective), outliers))
        i = j if j > i else i + 1

    if not runs:
        return 0.5
    scores = [min(1.0, eff / target_run) for _cls, eff, _out in runs if eff > 0]
    return sum(scores) / len(scores) if scores else 0.5


def score_category_coherence(
    asset_ids: list[str],
    assets_by_id: Mapping[str, dict],
) -> float:
    """Phase 12 · reward adjacent semantic category continuity."""
    from travelogue.layout_contract.subject_tagging import semantic_category_for_asset

    if len(asset_ids) < 2:
        return 1.0
    cats = [semantic_category_for_asset(assets_by_id.get(aid) or {}) for aid in asset_ids]
    scores: list[float] = []
    for i in range(len(cats) - 1):
        a, b = cats[i], cats[i + 1]
        if a == b:
            scores.append(1.0)
        elif "general" in (a, b):
            scores.append(0.5)
        else:
            scores.append(0.0)
    return sum(scores) / len(scores) if scores else 0.5


def score_cohort_coherence(
    asset_ids: list[str],
    assets_by_id: Mapping[str, dict],
) -> float:
    from travelogue.layout_engine.scoring.cohort import score_cohort_coherence as _score

    return _score(asset_ids, assets_by_id)


def _asset_order_from_screens(screens: list[dict]) -> list[str]:
    order: list[str] = []
    for screen in screens:
        for slot in screen.get("slots") or []:
            aid = slot.get("assetId")
            if aid and aid not in order:
                order.append(aid)
    return order


def _asset_visual_center(asset: dict) -> tuple[float, float]:
    box = asset.get("salientBox")
    if isinstance(box, dict):
        x = float(box.get("x", 0.5))
        y = float(box.get("y", 0.5))
        w = float(box.get("w", 0.0))
        h = float(box.get("h", 0.0))
        return (
            min(1.0, max(0.0, x + w / 2.0)),
            min(1.0, max(0.0, y + h / 2.0)),
        )
    fp = asset.get("focalPoint") or {}
    return float(fp.get("x", 0.5)), float(fp.get("y", 0.45))


def screen_visual_center(screen: dict, assets_by_id: Mapping[str, dict]) -> tuple[float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for slot in screen.get("slots") or []:
        aid = slot.get("assetId")
        if not aid:
            continue
        cx, cy = _asset_visual_center(assets_by_id.get(aid) or {})
        xs.append(cx)
        ys.append(cy)
    if not xs:
        return 0.5, 0.45
    return sum(xs) / len(xs), sum(ys) / len(ys)


def score_gravity_balance(
    screens: list[dict],
    assets_by_id: Mapping[str, dict],
    *,
    max_delta: float = 0.35,
) -> float:
    """P6-D1 · adjacent-screen focal center continuity (higher = smoother flow)."""
    from travelogue.layout_contract.longshot import is_breath_screen as _is_breath_screen

    centers: list[tuple[float, float]] = []
    for screen in screens:
        if _is_breath_screen(screen):
            continue
        if not any(s.get("assetId") for s in (screen.get("slots") or [])):
            continue
        centers.append(screen_visual_center(screen, assets_by_id))
    if len(centers) < 2:
        return 1.0
    penalties: list[float] = []
    for i in range(len(centers) - 1):
        dx = centers[i + 1][0] - centers[i][0]
        dy = centers[i + 1][1] - centers[i][1]
        delta = (dx * dx + dy * dy) ** 0.5
        penalties.append(min(1.0, max(0.0, delta / max_delta)))
    return 1.0 - sum(penalties) / len(penalties)


def score_layout_rhythm(screens: list[dict]) -> float:
    """P5-R1 · penalize consecutive same layout; reward hero/grid alternation."""
    from travelogue.layout_contract.longshot import (
        is_breath_screen as _is_breath_screen,
        screen_layout_kind as _screen_kind,
    )

    scores: list[float] = []
    prev_kind: str | None = None
    prev_pid: str | None = None
    for screen in screens:
        if _is_breath_screen(screen):
            continue
        slots = screen.get("slots") or []
        if not any(s.get("assetId") for s in slots):
            continue
        kind = _screen_kind(screen)
        pid = str(screen.get("patternId") or "")
        if prev_kind is None:
            prev_kind, prev_pid = kind, pid
            continue
        if pid and pid == prev_pid:
            scores.append(0.0)
        elif kind == prev_kind:
            scores.append(0.35)
        else:
            scores.append(1.0)
        prev_kind, prev_pid = kind, pid
    if not scores:
        return 1.0
    return sum(scores) / len(scores)


def score_screen(
    screen: dict,
    *,
    aspects: Mapping[str, AspectKind],
    assets_by_id: Mapping[str, dict],
    weights: ScoringWeights,
    arc_segment: str | None = None,
    arc_profile: str = "dynamic",
    hero_asset_ids: set[str] | None = None,
    prior_pattern_ids: list[str] | None = None,
    featured_beam: bool = False,
    intent_arc_boost: float = 0.0,
) -> ScoreBreakdown:
    """Per-screen base score (aspect, sharpness, hero, temporal, diversity, arc).

    ``ScoreBreakdown.total`` here covers only single-screen dimensions. Cross-screen
    terms (burst_integrity, luminance/tone continuity, subject_run) are aggregated in
    ``score_screen_plan`` only.
    """
    bd = ScoreBreakdown()
    bd.aspect_match = score_aspect_match(screen, aspects)
    bd.sharpness = score_sharpness(screen, assets_by_id)
    bd.temporal_coherence = score_temporal_coherence(screen, assets_by_id)
    if hero_asset_ids:
        slot_ids = {s.get("assetId") for s in (screen.get("slots") or []) if s.get("assetId")}
        overlap = slot_ids & hero_asset_ids
        if overlap:
            if featured_beam and any(
                (assets_by_id.get(aid) or {}).get("userTier") == "featured" for aid in overlap
            ):
                bd.hero_separation = FEATURED_HERO_SEPARATION_HALVED
            else:
                bd.hero_separation = 0.0
        else:
            bd.hero_separation = 1.0
    else:
        bd.hero_separation = 1.0
    pid = screen.get("patternId")
    if prior_pattern_ids and pid:
        bd.diversity = 0.0 if pid in prior_pattern_ids[-2:] else 1.0
    else:
        bd.diversity = 1.0
    if arc_segment:
        from travelogue.layout_contract.arc import arc_pattern_bonus

        bd.arc_fit = arc_pattern_bonus(pid or "", arc_segment, profile=arc_profile)
        if intent_arc_boost > 0:
            bd.arc_fit = min(1.0, bd.arc_fit + intent_arc_boost)
    else:
        bd.arc_fit = 0.5
    bd.total = (
        weights.aspect_match * bd.aspect_match
        + weights.sharpness * bd.sharpness
        + weights.hero_separation * bd.hero_separation
        + weights.temporal_coherence * bd.temporal_coherence
        + weights.diversity * bd.diversity
        + weights.arc_fit * bd.arc_fit
    )
    return bd


def _finalize_plan_score(
    parts: list[ScoreBreakdown],
    screens: list[dict],
    *,
    assets_by_id: Mapping[str, dict],
    weights: ScoringWeights,
    subject_run_tolerance: int,
    featured_beam: bool,
    enable_gravity_balance: bool,
) -> ScoreBreakdown:
    if not parts:
        return ScoreBreakdown()
    weights = weights.normalized()
    burst = score_burst_integrity(screens, assets_by_id)
    luma = score_luminance_continuity(screens, assets_by_id)
    tone = score_tone_continuity(screens, assets_by_id)
    subject = score_subject_run_soft(
        _asset_order_from_screens(screens),
        assets_by_id,
        tolerance=subject_run_tolerance,
    )
    coherence = score_category_coherence(_asset_order_from_screens(screens), assets_by_id)
    cohort = score_cohort_coherence(_asset_order_from_screens(screens), assets_by_id)
    rhythm = score_layout_rhythm(screens)
    gravity = score_gravity_balance(screens, assets_by_id) if enable_gravity_balance else 1.0
    avg = ScoreBreakdown()
    n = len(parts)
    for bd in parts:
        avg.aspect_match += bd.aspect_match / n
        avg.sharpness += bd.sharpness / n
        avg.hero_separation += bd.hero_separation / n
        avg.temporal_coherence += bd.temporal_coherence / n
        avg.diversity += bd.diversity / n
        avg.arc_fit += bd.arc_fit / n
    avg.burst_integrity = burst
    avg.luminance_continuity = luma
    avg.tone_continuity = tone
    avg.subject_run = subject
    avg.category_coherence = coherence
    avg.cohort_coherence = cohort
    avg.layout_rhythm = rhythm
    avg.gravity_balance = gravity
    avg.total = (
        weights.aspect_match * avg.aspect_match
        + weights.sharpness * avg.sharpness
        + weights.hero_separation * avg.hero_separation
        + weights.temporal_coherence * avg.temporal_coherence
        + weights.diversity * avg.diversity
        + weights.arc_fit * avg.arc_fit
        + weights.burst_integrity * avg.burst_integrity
        + weights.luminance_continuity * avg.luminance_continuity
        + weights.tone_continuity * avg.tone_continuity
        + weights.subject_run * avg.subject_run
        + weights.layout_rhythm * avg.layout_rhythm
        + weights.gravity_balance * avg.gravity_balance
        + weights.category_coherence * avg.category_coherence
        + weights.cohort_coherence * avg.cohort_coherence
    )
    if featured_beam:
        featured_n = 0
        for screen in screens:
            for slot in screen.get("slots") or []:
                aid = slot.get("assetId")
                if aid and (assets_by_id.get(aid) or {}).get("userTier") == "featured":
                    featured_n += 1
        avg.total += featured_n * FEATURED_BEAM_BONUS_PER_ASSET
    return avg


def _build_plan_screen_parts(
    screens: list[dict],
    *,
    aspects: Mapping[str, AspectKind],
    assets_by_id: Mapping[str, dict],
    weights: ScoringWeights,
    arc_segment: str | None,
    arc_profile: str,
    hero_asset_ids: set[str] | None,
    featured_beam: bool,
    intent_arc_boost: float,
    start_index: int = 0,
    initial_parts: list[ScoreBreakdown] | None = None,
    initial_prior: list[str] | None = None,
) -> tuple[list[ScoreBreakdown], list[str]]:
    weights = weights.normalized()
    parts = list(initial_parts or [])
    prior = list(initial_prior or [])
    for screen in screens[start_index:]:
        bd = score_screen(
            screen,
            aspects=aspects,
            assets_by_id=assets_by_id,
            weights=weights,
            arc_segment=arc_segment,
            arc_profile=arc_profile,
            hero_asset_ids=hero_asset_ids,
            prior_pattern_ids=prior,
            featured_beam=featured_beam,
            intent_arc_boost=intent_arc_boost,
        )
        parts.append(bd)
        prior.append(screen.get("patternId") or "")
    return parts, prior


def score_screen_plan(
    screens: list[dict],
    *,
    aspects: Mapping[str, AspectKind],
    assets_by_id: Mapping[str, dict],
    weights: ScoringWeights,
    arc_segment: str | None = None,
    arc_profile: str = "dynamic",
    hero_asset_ids: set[str] | None = None,
    subject_run_tolerance: int = 1,
    featured_beam: bool = False,
    intent_arc_boost: float = 0.0,
    enable_gravity_balance: bool = True,
    incremental: bool = False,
    incremental_state: IncrementalScoreState | None = None,
    moment_secondary_ids: set[str] | frozenset[str] | None = None,
    moment_secondary_boost: float = 0.0,
) -> ScoreBreakdown:
    """Aggregate score for a full screen sequence in one day bucket / chapter."""
    if not screens:
        return ScoreBreakdown()
    if incremental:
        state = incremental_state or IncrementalScoreState()
        ctx_kwargs = dict(
            weights=weights,
            arc_segment=arc_segment,
            arc_profile=arc_profile,
            hero_asset_ids=hero_asset_ids,
            intent_arc_boost=intent_arc_boost,
            featured_beam=featured_beam,
            subject_run_tolerance=subject_run_tolerance,
            enable_gravity_balance=enable_gravity_balance,
        )
        plan_key = _incremental_cache_key(screens, **ctx_kwargs)
        cached = state.prefix_parts.get(plan_key)
        if cached is not None:
            parts, prior = cached
            result = _finalize_plan_score(
                parts,
                screens,
                assets_by_id=assets_by_id,
                weights=weights,
                subject_run_tolerance=subject_run_tolerance,
                featured_beam=featured_beam,
                enable_gravity_balance=enable_gravity_balance,
            )
            result.total += moment_secondary_plan_bonus(
                screens,
                arc_segment=arc_segment,
                secondary_ids=moment_secondary_ids or set(),
                boost=moment_secondary_boost,
            )
            return result
        start_index = 0
        parts: list[ScoreBreakdown] = []
        prior: list[str] = []
        for length in range(len(screens) - 1, 0, -1):
            prefix_key = _incremental_cache_key(screens[:length], **ctx_kwargs)
            hit = state.prefix_parts.get(prefix_key)
            if hit is not None:
                parts, prior = list(hit[0]), list(hit[1])
                start_index = length
                break
        parts, prior = _build_plan_screen_parts(
            screens,
            aspects=aspects,
            assets_by_id=assets_by_id,
            weights=weights,
            arc_segment=arc_segment,
            arc_profile=arc_profile,
            hero_asset_ids=hero_asset_ids,
            featured_beam=featured_beam,
            intent_arc_boost=intent_arc_boost,
            start_index=start_index,
            initial_parts=parts,
            initial_prior=prior,
        )
        state.prefix_parts[plan_key] = (list(parts), list(prior))
        result = _finalize_plan_score(
            parts,
            screens,
            assets_by_id=assets_by_id,
            weights=weights,
            subject_run_tolerance=subject_run_tolerance,
            featured_beam=featured_beam,
            enable_gravity_balance=enable_gravity_balance,
        )
        result.total += moment_secondary_plan_bonus(
            screens,
            arc_segment=arc_segment,
            secondary_ids=moment_secondary_ids or set(),
            boost=moment_secondary_boost,
        )
        return result

    parts, prior = _build_plan_screen_parts(
        screens,
        aspects=aspects,
        assets_by_id=assets_by_id,
        weights=weights,
        arc_segment=arc_segment,
        arc_profile=arc_profile,
        hero_asset_ids=hero_asset_ids,
        featured_beam=featured_beam,
        intent_arc_boost=intent_arc_boost,
    )
    result = _finalize_plan_score(
        parts,
        screens,
        assets_by_id=assets_by_id,
        weights=weights,
        subject_run_tolerance=subject_run_tolerance,
        featured_beam=featured_beam,
        enable_gravity_balance=enable_gravity_balance,
    )
    result.total += moment_secondary_plan_bonus(
        screens,
        arc_segment=arc_segment,
        secondary_ids=moment_secondary_ids or set(),
        boost=moment_secondary_boost,
    )
    return result


def rank_screens(
    screens: list[dict],
    *,
    aspects: Mapping[str, AspectKind],
    assets_by_id: Mapping[str, dict],
    weights: ScoringWeights,
    **kwargs: Any,
) -> list[tuple[dict, ScoreBreakdown]]:
    """Return screens sorted by total score descending (stable tie-break by input order)."""
    scored: list[tuple[int, dict, ScoreBreakdown]] = []
    for i, screen in enumerate(screens):
        scored.append(
            (
                i,
                screen,
                score_screen(
                    screen,
                    aspects=aspects,
                    assets_by_id=assets_by_id,
                    weights=weights,
                    **kwargs,
                ),
            )
        )
    scored.sort(key=lambda row: (-row[2].total, row[0]))
    return [(screen, breakdown) for _i, screen, breakdown in scored]
